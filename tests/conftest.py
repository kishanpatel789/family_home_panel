import pytest
from application import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })

    return app

@pytest.fixture
def client(app):
    return app.test_client()