from datetime import date, datetime

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_catalog_lists_all_routes_with_ordered_stops_and_departures():
    r = client.get("/api/v1/departures/today")
    assert r.status_code == 200
    body = r.json()
    assert body["date"] == date.today().isoformat()
    names = {x["name"] for x in body["routes"]}
    assert names == {
        "Campus A to Metro", "Metro to Campus A",
        "Campus B to Metro", "Metro to Campus B",
    }
    for route in body["routes"]:
        assert len(route["stops"]) >= 2
        assert [s["sequence"] for s in route["stops"]] == list(range(1, len(route["stops"]) + 1))
        assert route["departures"]
        times = [d["scheduled_time"] for d in route["departures"]]
        assert times == sorted(times)
        for d in route["departures"]:
            assert datetime.fromisoformat(d["scheduled_time"]).date() == date.today()
            assert d["seat_count"] > 0
            assert d["seats_remaining"] == d["seat_count"]


def test_reverse_route_stops_are_reversed():
    routes = {x["name"]: x for x in client.get("/api/v1/routes").json()}
    fwd = [s["name"] for s in routes["Campus A to Metro"]["stops"]]
    rev = [s["name"] for s in routes["Metro to Campus A"]["stops"]]
    assert rev == fwd[::-1]


def test_routes_endpoint_has_no_departures():
    routes = client.get("/api/v1/routes").json()
    assert len(routes) == 4
    assert all("departures" not in r for r in routes)


def test_route_departures_and_404():
    rid = client.get("/api/v1/routes").json()[0]["id"]
    r = client.get(f"/api/v1/routes/{rid}/departures/today")
    assert r.status_code == 200 and r.json()
    assert client.get("/api/v1/routes/nope/departures/today").status_code == 404


def test_seats_remaining_reflects_confirmed_bookings():
    from app import catalog
    dep = client.get("/api/v1/departures/today").json()["routes"][0]["departures"][0]
    catalog.confirmed_counts[dep["id"]] = 5
    try:
        again = client.get("/api/v1/departures/today").json()["routes"][0]["departures"][0]
        assert again["seats_remaining"] == dep["seat_count"] - 5
    finally:
        catalog.confirmed_counts.clear()
