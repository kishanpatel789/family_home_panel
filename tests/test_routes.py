def test_home_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Home Panel" in response.data

def test_testhome_route(client):
    response = client.get("/test")
    assert response.status_code == 200
    assert b"Home Panel" in response.data


def test_weather_route(client):
    response = client.get("/weather", headers={"HX-Request": "true"})
    print(response.data)
    print(client)
    for rule in client.application.url_map.iter_rules():
        print(f"{rule}: {rule.endpoint}")
    assert response.status_code == 200
    assert b"Loading weather..." not in response.data


def test_events_route(client):
    response = client.get("/events")
    assert response.status_code == 200
    assert b"Loading events..." not in response.data
