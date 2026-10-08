"""task-MYVTAFzmURY — Show route choices.

WHEN the rider opens the trip-booking view
THEN the rider can select a fixed route, one of today's departures, and a stop
on that route.
"""
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    fixed_now = lambda: datetime(2026, 10, 8, 6, 0, tzinfo=timezone.utc)  # noqa: E731
    return TestClient(create_app(clock=fixed_now))


def test_booking_view_is_served(client):
    response = client.get("/book")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_booking_view_has_route_departure_and_stop_selectors(client):
    html = client.get("/book").text
    for control in ('id="route"', 'id="departure"', 'id="stop"'):
        assert control in html
    assert "<select" in html


def test_booking_view_loads_todays_departures(client):
    html = client.get("/book").text
    assert "/api/departures/today" in html


def test_root_redirects_to_booking_view(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/book"


def test_every_route_offers_departures_and_stops_to_choose(client):
    """The data behind the view supports a full route → departure → stop pick."""
    body = client.get("/api/departures/today").json()
    for route in body["routes"]:
        assert route["name"]
        assert route["departures"]
        # Boarding is possible at every stop except the final one.
        boardable = [s for s in route["stops"] if s["boardable"]]
        assert boardable
        assert route["stops"][-1]["boardable"] is False
        assert all(s["boardable"] for s in route["stops"][:-1])
