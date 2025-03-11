import json
import time
from datetime import datetime, timedelta, timezone

from flask import (
    render_template,
    make_response,
    abort,
    redirect,
    url_for,
    flash,
    request,
)
from flask import current_app as app
import requests
from pydantic import ValidationError

from . import models
from .config import logger

config = app.config["API_CONFIG"]["weather"]
LAT = config["lat"]
LON = config["lon"]
API_KEY = config["api_key"]
UNITS = config.get("units", "metric")
NUM_DAYS = int(config.get("num_days", 3))
BASE_URL = config.get("base_url", "https://api.openweathermap.org/data/2.5")


# get current weather
def get_current_weather():
    url = f"{BASE_URL}/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units={UNITS}"
    response = requests.get(url)
    response.raise_for_status()
    current_weather = response.json()

    return current_weather


# get forecast
def get_forecast_weather():
    url = f"{BASE_URL}/forecast?lat={LAT}&lon={LON}&appid={API_KEY}&units={UNITS}&cnt={NUM_DAYS*8}"
    response = requests.get(url)
    response.raise_for_status()
    forecast_weather = response.json()

    return forecast_weather


def update_weather_cache() -> models.WeatherCache:
    cw = get_current_weather()
    # forecast_weather_json = get_forecast_weather()

    current_weather_model = models.CurrentWeather(
        condition=f"{cw['weather'][0]['main']} - {cw['weather'][0]['description']}",
        temperature=round(cw["main"]["temp"]),
        wind_speed=cw["wind"]["speed"],
        wind_deg=cw["wind"]["deg"],
        cloud_coverage=cw["clouds"]["all"],
        rain=cw.get("rain", {}).get("1h"),
        snow=cw.get("snow", {}).get("1h"),
    )

    weather_cache = models.WeatherCache(
        timestamp=int(time.time()),
        current=current_weather_model,
    )

    with open(app.config["API_CONFIG"]["weather"]["cache_file"], "wt") as cache_file:
        json.dump(weather_cache.model_dump(), cache_file, indent=4)

    return weather_cache


def get_cached_weather() -> models.WeatherCache:
    with open(app.config["API_CONFIG"]["weather"]["cache_file"], "rt") as cache_file:
        try:
            cache_data = models.WeatherCache(**json.load(cache_file))
        except ValidationError as e:
            logger.error(e)
            return update_weather_cache()
        
    cache_expiration_timestamp = cache_data.timestamp + app.config["API_CONFIG"]["weather"]["cache_ttl"]
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
    # get weather
    # try cache first
    weather_cache = get_cached_weather()

    return weather_cache.model_dump()
    #   if cache is not available or expired, make api call

    # make api call
    # get current weather
    # get forecast weather
    # parse current weather and forecast weather
    # store parsed weather in cache

    # return weather object


@app.route("/")
def home():
    weather_dict = get_weather()

    return render_template(
        "index.html",
        weather=weather_dict,
        events_today=None,
        events_tomorrow=None,
        meals=None,
    )


@app.route("/test")
def test():
    return get_weather().model_dump()
