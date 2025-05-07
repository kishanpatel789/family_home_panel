from application.models import CurrentWeather, HourForecast


def test_current_weather_model():
    data = {
        "condition": "Clear",
        "icon": "01d",
        "temperature": 25,
        "wind_speed": 5,
        "wind_deg": 90,
        "cloud_coverage": 0,
    }
    weather = CurrentWeather(**data)

    assert weather.temperature == 25
    assert weather.condition == "Clear"
    assert weather.rain == None


def test_hour_forecast_model():
    data = {
        "timestamp": 1746662400,
        "condition": "Clouds - scattered clouds",
        "icon": "03d",
        "temperature": 25,
        "precipitation_chance": 0,
    }
    forecast = HourForecast(**data)

    assert forecast.temperature == 25
    assert forecast.timestamp == 1746662400
