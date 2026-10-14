"""Fixed routes, stops and today's departures with seat availability."""
from datetime import date, time
from typing import Callable, Protocol

from pydantic import BaseModel

SEATS_PER_SHUTTLE = 12  # fixed seat count per shuttle (13th rider is waitlisted)


class Stop(BaseModel):
    id: str
    name: str
    sequence: int


class Route(BaseModel):
    id: str
    name: str
    stops: list[Stop]


class Departure(BaseModel):
    id: str
    route_id: str
    departure_time: time
    seat_count: int
    seats_remaining: int


class DeparturesToday(BaseModel):
    date: date
    departures: list[Departure]


class RouteWithDepartures(Route):
    departures: list[Departure]


class Catalog(BaseModel):
    date: date
    routes: list[RouteWithDepartures]


class BookingCounts(Protocol):
    def confirmed_seats(self, departure_id: str, day: date) -> int: ...


class NoBookings:
    """Default until the booking module supplies real counts."""

    def confirmed_seats(self, departure_id: str, day: date) -> int:
        return 0


# (route id, name, ordered stop names)
_CAMPUS_A = ["Campus A Main Gate", "Campus A Parking", "Metro Station"]
_CAMPUS_B = ["Campus B Main Gate", "Campus B Library", "Metro Station"]
_ROUTE_DEFS = [
    ("campus-a-metro", "Campus A to Metro", _CAMPUS_A),
    ("metro-campus-a", "Metro to Campus A", _CAMPUS_A[::-1]),
    ("campus-b-metro", "Campus B to Metro", _CAMPUS_B),
    ("metro-campus-b", "Metro to Campus B", _CAMPUS_B[::-1]),
]
_SCHEDULE = [time(7, 30), time(8, 0), time(8, 30), time(12, 0), time(17, 0), time(17, 30), time(18, 0)]


def _slug(name: str) -> str:
    return name.lower().replace(" ", "-")


class CatalogService:
    def __init__(self, bookings: BookingCounts | None = None, today: Callable[[], date] = date.today):
        self._bookings = bookings or NoBookings()
        self._today = today
        self._routes = [
            Route(
                id=rid,
                name=name,
                stops=[Stop(id=f"{rid}:{_slug(s)}", name=s, sequence=i) for i, s in enumerate(stops, 1)],
            )
            for rid, name, stops in _ROUTE_DEFS
        ]

    def routes(self) -> list[Route]:
        return self._routes

    def get_route(self, route_id: str) -> Route | None:
        return next((r for r in self._routes if r.id == route_id), None)

    def departures_today(self, route_id: str | None = None) -> DeparturesToday:
        day = self._today()
        routes = [r for r in self._routes if route_id in (None, r.id)]
        deps = [self._departure(r.id, t, day) for r in routes for t in _SCHEDULE]
        return DeparturesToday(date=day, departures=deps)

    def catalog(self) -> Catalog:
        today = self.departures_today()
        return Catalog(
            date=today.date,
            routes=[
                RouteWithDepartures(**r.model_dump(), departures=[d for d in today.departures if d.route_id == r.id])
                for r in self._routes
            ],
        )

    def _departure(self, route_id: str, at: time, day: date) -> Departure:
        dep_id = f"{route_id}@{at.strftime('%H%M')}"
        taken = self._bookings.confirmed_seats(dep_id, day)
        return Departure(
            id=dep_id,
            route_id=route_id,
            departure_time=at,
            seat_count=SEATS_PER_SHUTTLE,
            seats_remaining=max(SEATS_PER_SHUTTLE - taken, 0),
        )
