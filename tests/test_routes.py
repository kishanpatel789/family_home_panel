def test_home_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Home Panel" in response.data


def test_weather_route(client):
    response = client.get("/weather")
    assert response.status_code == 200
    assert b"Last updated" in response.data


def test_events_route(client):
    response = client.get("/events")
    assert response.status_code == 200
    assert b"Last updated" in response.data
