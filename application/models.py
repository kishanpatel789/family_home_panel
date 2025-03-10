from pydantic import BaseModel

class CurrentWeather(BaseModel):
    condition: str
    temperature: int
    wind_speed: float
    wind_direction: int
    cloud_coverage: int
    rain: float | None = None
    snow: float | None = None
        

class ForecastWeather(BaseModel):
    pass

class WeatherCache(BaseModel):
    timestamp: int
    current: CurrentWeather
    # forecast: ForecastWeather