import json
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import urlencode
import time

from googleapiclient.discovery import build
from google.oauth2 import service_account
from pydantic import ValidationError

from . import models

logger = logging.getLogger(__name__)


def call_api_events(
    calendar_id: str, start_dt: datetime, end_dt: datetime, service
) -> list[dict]:
    """Call Google Calendar API and return events for given calendar and date range.

    Args:
        calendar_id (str): Google's ID of the calendar
        start_dt (datetime): start date to filter calendar events by
        end_dt (datetime): end date to filter calendar events by

    Returns:
        list[dict]: list of calendar events returned for given calendar and date range
    """

    logger.info(f"Calling Google Calendar API for events from '{calendar_id}'")
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


def create_directions_url(config: dict, location: str | None) -> str | None:
    """Convert event location (if any) into a directions url.
    For in-person events, this will be a Google Maps URL with the event location as the destination.
    For virtual events, this will be the event URL.
    For events without a location, this will be None.

    Args:
        location (str | None): Location of event

    Returns:
        str | None: URL to Google Maps directions or event URL
    """
    if location is not None:
        # virtual event
        if "https://" in location:
            return location

        # in-person event
        if location != config["direction_origin"]:
            url_query = urlencode(
                {
                    "api": config["google_maps_api_version"],
                    "origin": config["direction_origin"],
                    "destination": location,
                }
            )
            dir_url = f"{config['google_maps_base_url']}/?{url_query}"

            return dir_url


def sort_events(events: list[models.Event]) -> list[models.Event]:
    """Sort events by start time and event name (summary).
    Full day events appear first.

    Args:
        events (list[models.Event]): List of event models

    Returns:
        list[models.Event]: List of event models sorted
    """
    return sorted(events, key=lambda x: (not x.full_day, x.start, x.summary))


def update_events_cache(config: dict) -> models.EventsCache:
    """Update local event cache for multiple Google calendars.
    Captures events for today and tomorrow.
    Saves events in local json and returns pydantic model.

    Returns:
        models.EventsCache: Pydantic model of events
    """
    credentials = service_account.Credentials.from_service_account_file(
        config["key_file"], scopes=["https://www.googleapis.com/auth/calendar.readonly"]
    )
    service = build("calendar", "v3", credentials=credentials)

    today_midnight = (
        datetime.today()
        .astimezone(ZoneInfo(config["timezone"]))
        .replace(hour=0, minute=0, second=0)
    )
    tomorrow_midnight = today_midnight + timedelta(days=1)
    two_days_midnight = today_midnight + timedelta(days=2)

    events_today = []
    events_tomorrow = []
    meals_today = []
    meals_tomorrow = []

    for cal_name, cal_info in config["event_calendars"].items():
        events = call_api_events(
            cal_info["id"], today_midnight, two_days_midnight, service
        )

        for e in events:
            if "date" in e["start"]:  # full day event
                e_model = models.Event(
                    calendar=cal_name,
                    summary=e["summary"],
                    full_day=True,
                    start=datetime.fromisoformat(e["start"]["date"]).astimezone(
                        ZoneInfo(config["timezone"])
                    ),
                    end=datetime.fromisoformat(e["end"]["date"]).astimezone(
                        ZoneInfo(config["timezone"])
                    ),
                    location=e.get("location"),
                    directions=create_directions_url(config, e.get("location")),
                )
                if e_model.start <= today_midnight < e_model.end:
                    events_today.append(e_model)
                if e_model.start <= tomorrow_midnight < e_model.end:
                    events_tomorrow.append(e_model)

            elif "dateTime" in e["start"]:  # timed event
                e_model = models.Event(
                    calendar=cal_name,
                    summary=e["summary"],
                    start=datetime.fromisoformat(e["start"]["dateTime"]),
                    end=datetime.fromisoformat(e["end"]["dateTime"]),
                    location=e.get("location"),
                    directions=create_directions_url(config, e.get("location")),
                )
                if today_midnight <= e_model.start < tomorrow_midnight:
                    events_today.append(e_model)
                if tomorrow_midnight <= e_model.start < two_days_midnight:
                    events_tomorrow.append(e_model)

    food_events = call_api_events(
        config["food_calendar"]["id"], today_midnight, two_days_midnight, service
    )

    for f in food_events:
        if "date" in f["start"]:  # full day "event"
            f_model = models.Food(
                summary=f["summary"],
                start=datetime.fromisoformat(f["start"]["date"]).astimezone(
                    ZoneInfo(config["timezone"])
                ),
                end=datetime.fromisoformat(f["end"]["date"]).astimezone(
                    ZoneInfo(config["timezone"])
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

    with open(config["cache_file"], "wt") as cache_file:
        cache_file.write(events_cache.model_dump_json(indent=4))

    return events_cache


def get_cached_events(config: dict) -> models.EventsCache:
    """Get cached events if available. Else refresh cache and return results.

    Returns:
        models.EventsCache: Pydantic model of events
    """
    try:
        with open(config["cache_file"], "rt") as cache_file:
            cache_data = models.EventsCache(**json.load(cache_file))
    except (ValidationError, FileNotFoundError, json.decoder.JSONDecodeError) as e:
        logger.error(e)
        return update_events_cache(config)

    cache_expiration_timestamp = cache_data.timestamp + config["cache_ttl"]
    if time.time() < cache_expiration_timestamp:
        logger.info("Using fresh cache.")
        return cache_data
    else:
        logger.info("Cache expired. Refreshing cache.")
        return update_events_cache(config)


def format_events(config: dict, events_cache_dict: dict) -> dict:
    """Format event times and common locations for display.

    Args:
        events_cache_dict (dict): Events cache as python dict

    Returns:
        dict: Formated events cache
    """
    for event_day in ["events_today", "events_tomorrow"]:
        for e in events_cache_dict[event_day]:
            e["start"] = e["start"].strftime("%H:%M")
            e["end"] = e["end"].strftime("%H:%M")

            if e["location"] is not None:
                for root_address, friendly_name in config["common_locations"].items():
                    if root_address.lower() in e["location"].lower():
                        e["location"] = friendly_name
                        break

    return events_cache_dict


def get_events(config: dict) -> dict:
    """Returns events data to be used in jinja template; relies on cache

    Returns:
        dict: Events data for today and tomorrow
    """
    events_cache = get_cached_events(config)
    events_cache_dict = events_cache.model_dump()
    events_cache_dict["last_updated"] = events_cache.formatted_timestamp(
        config["timezone"]
    )

    events_cache_dict = format_events(config, events_cache_dict)

    return events_cache_dict
