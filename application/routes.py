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

@app.route("/")
def home():

    return render_template(
        "index.html",
    )