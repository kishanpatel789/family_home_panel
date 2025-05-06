from flask import Blueprint, render_template, current_app

from .weather import get_weather, WEATHER_EMOJI_MAP
from .events import get_events

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return render_template(
        "index.html",
    )


@main_bp.route("/weather")
def weather():
    try:
        weather_dict = get_weather(current_app.config["APP_CONFIG"]["weather"])
        return render_template(
            "weather.html",
            weather=weather_dict,
            weather_emoji_map=WEATHER_EMOJI_MAP,
        )
    except Exception:
        return render_template("weather_error.html")


@main_bp.route("/events")
def events():
    try:
        events_dict = get_events(current_app.config["APP_CONFIG"]["events"])
        return render_template(
            "events.html",
            events=events_dict,
        )
    except Exception:
        return render_template("events_error.html")
