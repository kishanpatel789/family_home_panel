import pytest
from application import create_app
from application.config import Config

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "APP_CONFIG": Config.APP_CONFIG,
    })
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    return app.test_client()