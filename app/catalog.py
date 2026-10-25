"""Fixed route/stop/departure catalog.

Static reference data lives here until the PostgreSQL schema lands. The
booking task owns ``confirmed_counts`` (departure id -> Confirmed bookings);
seats remaining is derived from it, never stored.
"""
from dataclasses import dataclass
from datetime import date, datetime, time

SEAT_COUNT = 12  # fixed shuttle capacity (BRD scenario: 13th rider on a 12-seat departure)

DEPARTURE_TIMES = [time(7, 30), time(8, 30), time(9, 30), time(12, 0),
                   time(16, 30), time(17, 30), time(18, 30)]

# Stops in campus -> metro order; the reverse route uses the reverse order.
_CORRIDORS = {
    "campus-a": ("Campus A", ["Campus A Main Gate", "Campus A Library", "Harbor Road", "Metro Station"]),
    "campus-b": ("Campus B", ["Campus B Main Gate", "Campus B Parking", "Industrial Way", "Metro Station"]),
}

confirmed_counts: dict[str, int] = {}


@dataclass(frozen=True)
class Stop:
    id: str
    name: str
    sequence: int


@dataclass(frozen=True)
class Route:
    id: str
    name: str
    stops: tuple[Stop, ...]


def _build_routes() -> list[Route]:
    routes = []
    for key, (campus, stops) in _CORRIDORS.items():
        for rid, name, names in (
            (f"{key}-to-metro", f"{campus} to Metro", stops),
            (f"metro-to-{key}", f"Metro to {campus}", stops[::-1]),
        ):
            routes.append(Route(rid, name, tuple(
                Stop(f"{rid}-{i}", n, i) for i, n in enumerate(names, 1))))
    return routes


ROUTES = _build_routes()


def get_routes() -> list[Route]:
    return ROUTES


def get_route(route_id: str) -> Route | None:
    return next((r for r in ROUTES if r.id == route_id), None)


def departures_today(route: Route, today: date | None = None) -> list[dict]:
    today = today or date.today()
    out = []
    for t in DEPARTURE_TIMES:
        dep_id = f"{route.id}-{today.isoformat()}-{t.strftime('%H%M')}"
        out.append({
            "id": dep_id,
            "route_id": route.id,
            "scheduled_time": datetime.combine(today, t).isoformat(),
            "seat_count": SEAT_COUNT,
            "seats_remaining": max(SEAT_COUNT - confirmed_counts.get(dep_id, 0), 0),
        })
    return out
