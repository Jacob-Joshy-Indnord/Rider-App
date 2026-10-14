from datetime import date, time

from fastapi.testclient import TestClient

from app.main import create_app
from app.catalog import CatalogService, SEATS_PER_SHUTTLE

TODAY = date(2026, 10, 14)


class FakeBookings:
    """Confirmed-seat counts per departure id, standing in for the booking module."""

    def __init__(self, confirmed=None):
        self.confirmed = confirmed or {}

    def confirmed_seats(self, departure_id: str, day: date) -> int:
        return self.confirmed.get(departure_id, 0)


def make_client(bookings=None):
    service = CatalogService(bookings=bookings or FakeBookings(), today=lambda: TODAY)
    return TestClient(create_app(service))


def test_lists_all_four_fixed_routes_with_ordered_stops():
    body = make_client().get("/routes").json()
    names = {r["name"] for r in body}
    assert names == {
        "Campus A to Metro",
        "Metro to Campus A",
        "Campus B to Metro",
        "Metro to Campus B",
    }
    for route in body:
        stops = route["stops"]
        assert len(stops) >= 2
        assert [s["sequence"] for s in stops] == list(range(1, len(stops) + 1))
    a_to_m = next(r for r in body if r["name"] == "Campus A to Metro")
    m_to_a = next(r for r in body if r["name"] == "Metro to Campus A")
    assert [s["name"] for s in m_to_a["stops"]] == [s["name"] for s in reversed(a_to_m["stops"])]


def test_departures_today_cover_every_route_with_times_and_seats():
    resp = make_client().get("/departures")
    assert resp.status_code == 200
    body = resp.json()
    assert body["date"] == "2026-10-14"
    route_ids = {r["id"] for r in make_client().get("/routes").json()}
    assert {d["route_id"] for d in body["departures"]} == route_ids
    for d in body["departures"]:
        time.fromisoformat(d["departure_time"])
        assert d["seat_count"] == SEATS_PER_SHUTTLE
        assert d["seats_remaining"] == SEATS_PER_SHUTTLE
    for rid in route_ids:
        times = [d["departure_time"] for d in body["departures"] if d["route_id"] == rid]
        assert times == sorted(times)


def test_seats_remaining_reflects_confirmed_bookings():
    probe = make_client().get("/departures").json()["departures"]
    first, second = probe[0]["id"], probe[1]["id"]
    client = make_client(FakeBookings({first: 5, second: SEATS_PER_SHUTTLE + 3}))
    by_id = {d["id"]: d for d in client.get("/departures").json()["departures"]}
    assert by_id[first]["seats_remaining"] == SEATS_PER_SHUTTLE - 5
    assert by_id[second]["seats_remaining"] == 0  # never negative


def test_catalog_nests_stops_and_departures_per_route():
    body = make_client().get("/catalog").json()
    assert len(body["routes"]) == 4
    for route in body["routes"]:
        assert route["stops"] and route["departures"]
        assert all(d["route_id"] == route["id"] for d in route["departures"])


def test_filter_departures_by_route_and_unknown_route_404():
    client = make_client()
    rid = client.get("/routes").json()[0]["id"]
    deps = client.get("/departures", params={"route_id": rid}).json()["departures"]
    assert deps and all(d["route_id"] == rid for d in deps)
    assert client.get("/departures", params={"route_id": "nope"}).status_code == 404


def test_openapi_documents_endpoints():
    paths = make_client().get("/openapi.json").json()["paths"]
    assert {"/routes", "/departures", "/catalog"} <= set(paths)
