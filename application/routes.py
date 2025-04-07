import time

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

from .weather import get_weather, WEATHER_EMOJI_MAP
from .events import get_events


@app.route("/")
def home():
    weather_dict = get_weather()
    events_dict = get_events()

    return render_template(
        "index.html",
        weather=weather_dict,
        weather_emoji_map=WEATHER_EMOJI_MAP,
        events=events_dict,
    )

@app.route("/weather")
def weather():
    weather_dict = get_weather()

    return render_template(
        "weather.html",
        weather=weather_dict,
        weather_emoji_map=WEATHER_EMOJI_MAP,
    )

@app.route("/events")
def events():
    events_dict = get_events()

    return render_template(
        "events.html",
        events=events_dict,
    )
