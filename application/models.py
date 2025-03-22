from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel
from flask import current_app as app


APP_CONFIG = app.config["APP_CONFIG"]


class CurrentWeather(BaseModel):
    condition: str
    icon: str
    temperature: int
    wind_speed: int
    wind_deg: int
    cloud_coverage: int
    rain: int | None = None
    snow: int | None = None


class HourForecast(BaseModel):
    timestamp: int
    condition: str
    icon: str
    temperature: int
    precipitation_chance: int


class WeatherCache(BaseModel):
    timestamp: int
    current: CurrentWeather
    forecast: list[HourForecast]

    @property
    def formatted_timestamp(self) -> str:
        """Convert timestamp into human-readable string"""
        return (
            datetime.fromtimestamp(self.timestamp)
            .astimezone(ZoneInfo(APP_CONFIG["weather"]["timezone"]))
            .strftime("%m-%d %H:%M")
        )


class Event(BaseModel):
    calendar: str
    summary: str
    full_day: bool = False
    start: datetime
    end: datetime
    location: str | None = None
    directions: str | None = None


class Food(BaseModel):
    summary: str
    start: datetime
    end: datetime


class EventsCache(BaseModel):
    timestamp: int
    events_today: list[Event]
    meals_today: list[Food] = []
    events_tomorrow: list[Event]
    meals_tomorrow: list[Food] = []

    @property
    def formatted_timestamp(self) -> str:
        """Convert timestamp into human-readable string"""
        return (
            datetime.fromtimestamp(self.timestamp)
            .astimezone(ZoneInfo(APP_CONFIG["events"]["timezone"]))
            .strftime("%m-%d %H:%M")
        )
