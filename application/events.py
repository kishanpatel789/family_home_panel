from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

from googleapiclient.discovery import build
from google.oauth2 import service_account


from flask import current_app as app
import requests
from pydantic import ValidationError

from . import models
from .config import logger

CONFIG = app.config["APP_CONFIG"]["events"]
KEY_FILE = CONFIG["key_file"]
TIMEZONE = CONFIG.get("timezone", "America/Chicago")
EVENT_CALENDARS = CONFIG["event_calendars"]
DIRECTION_ORIGIN = CONFIG["direction_origin"]
CACHE_FILE = CONFIG["cache_file"]
CACHE_TTL = CONFIG["cache_ttl"]


SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
SERVICE_ACCOUNT_FILE = KEY_FILE
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("calendar", "v3", credentials=credentials)





def call_api_events(calendar_id) -> list[dict]:
    today_midnight = (
        datetime.today()
        .astimezone(ZoneInfo(TIMEZONE))
        .replace(hour=0, minute=0, second=0)
    )
    two_days_later = today_midnight + timedelta(days=2)
    dt_format_rfc3339 = "%Y-%m-%dT%H:%M:%S%:z"

    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=today_midnight.strftime(dt_format_rfc3339),
            timeMax=two_days_later.strftime(dt_format_rfc3339),
            singleEvents=True,
            maxResults=50,
        )
        .execute()
    )
    events = events_result.get("items", [])

    return events

def update_weather_cache() -> models.WeatherCache:
    cw = call_api_current_weather()
    rain_mmh, snow_mmh = process_rain_snow(cw)
    current_weather_model = models.CurrentWeather(
        condition=f"{cw['weather'][0]['main']} - {cw['weather'][0]['description']}",
        icon=cw["weather"][0]["icon"],
        temperature=round(cw["main"]["temp"]),
        wind_speed=round(cw["wind"]["speed"] / 1000 * 60 * 60),  # convert m/s to km/hr
        wind_deg=cw["wind"]["deg"],
        cloud_coverage=cw["clouds"]["all"],
        rain=rain_mmh,
        snow=snow_mmh,
    )

    fw = call_api_forecast_weather()
    forecast_weather_models = []
    for f in fw:
        _forecast_model = models.HourForecast(
            timestamp=f["dt"],
            condition=f"{f['weather'][0]['main']} - {f['weather'][0]['description']}",
            icon=f["weather"][0]["icon"],
            temperature=round(f["main"]["temp"]),
            precipitation_chance=f["pop"] * 100,
        )
        forecast_weather_models.append(_forecast_model)

    weather_cache = models.WeatherCache(
        timestamp=int(time.time()),
        current=current_weather_model,
        forecast=forecast_weather_models,
    )

    with open(CACHE_FILE, "wt") as cache_file:
        json.dump(weather_cache.model_dump(), cache_file, indent=4)

    return weather_cache


for event in events:
    print(
        event["summary"],
        event.get("start", {}).get("dateTime", "No start time"),
        event.get("end", {}).get("dateTime", "No end time"),
        event.get("location", "No location"),
    )
