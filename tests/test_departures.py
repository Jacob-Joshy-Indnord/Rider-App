"""task-GIWwVEEf_RY — Provide today's departures.

WHEN the app requests today's departures
THEN the response includes the four specified route directions with stops and
today's scheduled departures, each with a shuttle and fixed seat count.
"""
from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

TODAY = date(2026, 10, 8)
EXPECTED_DIRECTIONS = {
    ("Campus A", "Metro"),
    ("Metro", "Campus A"),
    ("Campus B", "Metro"),
    ("Metro", "Campus B"),
}


@pytest.fixture
def client():
    fixed_now = lambda: datetime(2026, 10, 8, 6, 0, tzinfo=timezone.utc)  # noqa: E731
    return TestClient(create_app(clock=fixed_now))


@pytest.fixture
def body(client):
    response = client.get("/api/departures/today")
    assert response.status_code == 200
    return response.json()


def test_response_is_for_today(body):
    assert body["date"] == TODAY.isoformat()


def test_includes_exactly_the_four_route_directions(body):
    directions = {(r["origin"], r["destination"]) for r in body["routes"]}
    assert directions == EXPECTED_DIRECTIONS
    assert len(body["routes"]) == 4


def test_each_route_has_ordered_stops_from_origin_to_destination(body):
    for route in body["routes"]:
        stops = route["stops"]
        assert len(stops) >= 2
        assert [s["sequence"] for s in stops] == list(range(1, len(stops) + 1))
        assert stops[0]["name"] == route["origin"]
        assert stops[-1]["name"] == route["destination"]


def test_reverse_directions_share_stops_in_reverse_order(body):
    by_dir = {(r["origin"], r["destination"]): r for r in body["routes"]}
    for campus in ("Campus A", "Campus B"):
        outbound = [s["id"] for s in by_dir[(campus, "Metro")]["stops"]]
        inbound = [s["id"] for s in by_dir[("Metro", campus)]["stops"]]
        assert inbound == list(reversed(outbound))


def test_each_route_has_todays_departures_with_shuttle_and_seat_count(body):
    for route in body["routes"]:
        assert route["departures"], f"{route['id']} has no departures today"
        for dep in route["departures"]:
            scheduled = datetime.fromisoformat(dep["scheduled_at"])
            assert scheduled.date() == TODAY
            assert scheduled.tzinfo is not None
            shuttle = dep["shuttle"]
            assert shuttle["id"]
            assert isinstance(shuttle["seat_count"], int)
            assert shuttle["seat_count"] > 0


def test_departures_are_sorted_and_uniquely_identified(body):
    ids = []
    for route in body["routes"]:
        times = [d["scheduled_at"] for d in route["departures"]]
        assert times == sorted(times)
        ids += [d["id"] for d in route["departures"]]
    assert len(ids) == len(set(ids))


def test_seat_count_is_fixed_per_shuttle(body):
    seats_by_shuttle = {}
    for route in body["routes"]:
        for dep in route["departures"]:
            s = dep["shuttle"]
            seats_by_shuttle.setdefault(s["id"], set()).add(s["seat_count"])
    assert all(len(v) == 1 for v in seats_by_shuttle.values())


def test_departures_follow_the_clock_date():
    tomorrow = lambda: datetime(2026, 10, 9, 23, 0, tzinfo=timezone.utc)  # noqa: E731
    body = TestClient(create_app(clock=tomorrow)).get("/api/departures/today").json()
    assert body["date"] == "2026-10-09"
    for route in body["routes"]:
        for dep in route["departures"]:
            assert dep["scheduled_at"].startswith("2026-10-09")


def test_endpoint_is_documented_in_openapi(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/departures/today" in paths
