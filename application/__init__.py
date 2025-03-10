from flask import Flask
from .config import Config

def create_app():
    app = Flask(__name__)

    # read config json
    app.config.from_object(Config)

    with app.app_context():
        # include routes
        from . import routes

        # register Blueprints

        return app

