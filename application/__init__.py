from flask import Flask
from .config import Config, configure_logging
from .routes import main_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(main_bp)

    configure_logging(app)

    return app
