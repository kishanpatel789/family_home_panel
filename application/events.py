import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import urlencode
import time

from googleapiclient.discovery import build
from google.oauth2 import service_account
from flask import current_app as app
from pydantic import ValidationError

from . import models
from .config import logger

CONFIG: dict = app.config["APP_CONFIG"]["events"]
KEY_FILE: str = CONFIG["key_file"]
TIMEZONE: str = CONFIG.get("timezone", "America/Chicago")
EVENT_CALENDARS: dict = CONFIG["event_calendars"]
FOOD_CALENDAR_ID: str = CONFIG["food_calendar"]["id"]
GOOGLE_MAPS_BASE_URL: str = CONFIG["google_maps_base_url"]
GOOGLE_MAPS_API_VERSION: str = CONFIG["google_maps_api_version"]
DIRECTION_ORIGIN: str = CONFIG["direction_origin"]
CACHE_FILE: str = CONFIG["cache_file"]
CACHE_TTL: int = CONFIG["cache_ttl"]


SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
SERVICE_ACCOUNT_FILE = KEY_FILE
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("calendar", "v3", credentials=credentials)


def call_api_events(
    calendar_id: str, start_dt: datetime, end_dt: datetime
) -> list[dict]:

    logger.info(f"Calling Google Calendar API for events from {calendar_id}")
    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=start_dt.isoformat(),
            timeMax=end_dt.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=10,
        )
        .execute()
    )
    events = events_result.get("items", [])
    logger.info(f"    Received {len(events)} events from Google Calendar API")

    return events


def create_directions_url(location: str | None) -> str | None:
    if location is not None and location != DIRECTION_ORIGIN:

        url_query = urlencode(
            {
                "api": GOOGLE_MAPS_API_VERSION,
                "origin": DIRECTION_ORIGIN,
                "destination": location,
            }
        )
        dir_url = f"{GOOGLE_MAPS_BASE_URL}/?{url_query}"

        return dir_url


def sort_events(events: list[models.Event]) -> list[models.Event]:
    return sorted(events, key=lambda x: (not x.full_day, x.start, x.summary))


def update_events_cache() -> models.EventsCache:
    today_midnight = (
        datetime.today()
        .astimezone(ZoneInfo(TIMEZONE))
        .replace(hour=0, minute=0, second=0)
    )
    tomorrow_midnight = today_midnight + timedelta(days=1)
    two_days_midnight = today_midnight + timedelta(days=2)

    events_today = []
    events_tomorrow = []
    meals_today = []
    meals_tomorrow = []

    for cal_name, cal_info in EVENT_CALENDARS.items():
        events = call_api_events(cal_info["id"], today_midnight, two_days_midnight)

        for e in events:
            if "date" in e["start"]:  # full day event
                e_model = models.Event(
                    calendar=cal_name,
                    summary=e["summary"],
                    full_day=True,
                    start=datetime.fromisoformat(e["start"]["date"]).astimezone(
                        ZoneInfo(TIMEZONE)
                    ),
                    end=datetime.fromisoformat(e["end"]["date"]).astimezone(
                        ZoneInfo(TIMEZONE)
                    ),
                    location=e.get("location"),
                    directions=create_directions_url(e.get("location")),
                )
                if e_model.start <= today_midnight < e_model.end:
                    events_today.append(e_model)
                if e_model.start <= tomorrow_midnight < e_model.end:
                    events_tomorrow.append(e_model)

            elif "dateTime" in e["start"]:  # timed event
                e_model = models.Event(
                    calendar=cal_name,  # change later
                    summary=e["summary"],
                    start=datetime.fromisoformat(e["start"]["dateTime"]),
                    end=datetime.fromisoformat(e["end"]["dateTime"]),
                    location=e.get("location"),
                    directions=create_directions_url(e.get("location")),
                )
                if today_midnight <= e_model.start < tomorrow_midnight:
                    events_today.append(e_model)
                if tomorrow_midnight <= e_model.start < two_days_midnight:
                    events_tomorrow.append(e_model)

    food_events = call_api_events(FOOD_CALENDAR_ID, today_midnight, two_days_midnight)

    for f in food_events:
        if "date" in f["start"]:  # full day "event"
            f_model = models.Food(
                summary=f["summary"],
                start=datetime.fromisoformat(f["start"]["date"]).astimezone(
                    ZoneInfo(TIMEZONE)
                ),
                end=datetime.fromisoformat(f["end"]["date"]).astimezone(
                    ZoneInfo(TIMEZONE)
                ),
            )
            if f_model.start <= today_midnight < f_model.end:
                meals_today.append(f_model)
            if f_model.start <= tomorrow_midnight < f_model.end:
                meals_tomorrow.append(f_model)

    events_cache = models.EventsCache(
        timestamp=int(time.time()),
        events_today=sort_events(events_today),
        meals_today=meals_today,
        events_tomorrow=sort_events(events_tomorrow),
        meals_tomorrow=meals_tomorrow,
    )

    with open(CACHE_FILE, "wt") as cache_file:
        cache_file.write(events_cache.model_dump_json(indent=4))

    return events_cache


def get_cached_events() -> models.EventsCache:
    try:
        with open(CACHE_FILE, "rt") as cache_file:
            cache_data = models.EventsCache(**json.load(cache_file))
    except (ValidationError, FileNotFoundError) as e:
        logger.error(e)
        return update_events_cache()

    cache_expiration_timestamp = cache_data.timestamp + CACHE_TTL
    if time.time() < cache_expiration_timestamp:
        logger.info("Using fresh cache.")
        return cache_data
    else:
        logger.info("Cache expired. Refreshing cache.")
        return update_events_cache()


def format_events(events_cache_dict: dict) -> dict:
    for event_day in ["events_today", "events_tomorrow"]:
        for e in events_cache_dict[event_day]:
            e["start"] = e["start"].strftime("%H:%M")
            e["end"] = e["end"].strftime("%H:%M")

            for root_address, friendly_name in CONFIG["common_locations"].items():
                if root_address.lower() in e["location"].lower():
                    e["location"] = friendly_name
                    break

    return events_cache_dict


def get_events() -> dict:
    """Returns events data to be used in jinja template; relies on cache

    Returns:
        _type_: _description_
    """
    events_cache = get_cached_events()
    events_cache_dict = events_cache.model_dump()
    events_cache_dict["last_updated"] = events_cache.formatted_timestamp

    events_cache_dict = format_events(events_cache_dict)

    return events_cache_dict
