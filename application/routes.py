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







@app.route("/")
def home():
    weather_dict = get_weather()

    return render_template(
        "index.html",
        weather=weather_dict,
        weather_emoji_map=WEATHER_EMOJI_MAP,
        events=None,
    )


@app.route("/test")
def test():
    return app.config
