from datetime import datetime

from pydantic import BaseModel

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
        return datetime.fromtimestamp(self.timestamp).strftime("%m-%d %H:%M")

class Event(BaseModel):
    calendar: str
    summary: str
    full_day: bool = False
    start: datetime
    end: datetime
    location: str | None = None
    directions: str | None = None

class EventsCache(BaseModel):
    timestamp: int
    events_today: list[Event]
    meals_today: list[str] = []
    events_tomorrow: list[Event]
    meals_tomorrow: list[str] = []
    
    @property
    def formatted_timestamp(self) -> str:
        """Convert timestamp into human-readable string"""
        return datetime.fromtimestamp(self.timestamp).strftime("%m-%d %H:%M")