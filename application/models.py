from datetime import datetime, timezone

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
