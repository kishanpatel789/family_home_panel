import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import current_app as app
import requests
from pydantic import ValidationError

from . import models
from .config import logger


CONFIG = app.config["APP_CONFIG"]["weather"]
TIMEZONE = CONFIG["timezone"]
LAT = CONFIG["lat"]
LON = CONFIG["lon"]
API_KEY = CONFIG["api_key"]
UNITS = CONFIG.get("units", "metric")
NUM_DAYS = CONFIG.get("num_days", 3)
BASE_URL = CONFIG.get("base_url", "https://api.openweathermap.org/data/2.5")
CACHE_FILE = CONFIG["cache_file"]
CACHE_TTL = CONFIG["cache_ttl"]

WEATHER_EMOJI_MAP = {
    "01d": "\u2600",  # sun
    "01n": "\U0001f319",  # crescent moon
    "02d": "\u26c5",  # few clouds (day)
    "02n": "\u2601",  # partly cloudy (night)
    "03d": "\u26c5",  # Scattered clouds
    "03n": "\u2601",
    "04d": "\u2601",  # Broken clouds
    "04n": "\u2601",
    "09d": "\U0001f327",  # Shower rain
    "09n": "\U0001f327",
    "10d": "\U0001f326",  # Rain (day)
    "10n": "\U0001f327",  # Rain (night)
    "11d": "\u26c8",  # Thunderstorm
    "11n": "\u26c8",
    "13d": "\U0001f328",  # Snow
    "13n": "\U0001f328",
    "50d": "\U0001f327",  # Mist
    "50n": "\U0001f327",
}


def call_api_current_weather() -> dict:
    url = f"{BASE_URL}/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units={UNITS}"
    response = requests.get(url)
    response.raise_for_status()
    current_weather = response.json()

    return current_weather


def call_api_forecast_weather() -> list:
    url = f"{BASE_URL}/forecast?lat={LAT}&lon={LON}&appid={API_KEY}&units={UNITS}&cnt={NUM_DAYS*8}"
    response = requests.get(url)
    response.raise_for_status()
    forecast_weather = response.json()["list"]

    return forecast_weather


def process_rain_snow(weather: dict) -> tuple:
    rain_mmh = None
    snow_mmh = None

    if "rain" in weather:
        rain_mmh = round(weather["rain"]["1h"])
    if "snow" in weather:
        snow_mmh = round(weather["snow"]["1h"])

    return (rain_mmh, snow_mmh)


def timestamp_to_date_hour(timestamp: int) -> str:
    return (
        datetime.fromtimestamp(timestamp)
        .astimezone(ZoneInfo(TIMEZONE))
        .strftime("%H:%M")
    )


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


def get_cached_weather() -> models.WeatherCache:
    try:
        with open(CACHE_FILE, "rt") as cache_file:
            cache_data = models.WeatherCache(**json.load(cache_file))
    except (ValidationError, FileNotFoundError, json.decoder.JSONDecodeError) as e:
        logger.error(e)
        return update_weather_cache()

    cache_expiration_timestamp = cache_data.timestamp + CACHE_TTL
    if time.time() < cache_expiration_timestamp:
        logger.info("Using fresh cache.")
        return cache_data
    else:
        logger.info("Cache expired. Refreshing cache.")
        return update_weather_cache()


def get_weather() -> dict:
    """Returns weather data to be used in jinja template; relies on cache

    Returns:
        _type_: _description_
    """
    weather_cache = get_cached_weather()
    weather_cache_dict = weather_cache.model_dump()
    weather_cache_dict["last_updated"] = weather_cache.formatted_timestamp

    for f in weather_cache_dict["forecast"]:
        f["timestamp"] = timestamp_to_date_hour(f["timestamp"])

    return weather_cache_dict
