"""Read access to routes, stops and departures."""
import datetime as dt
import sqlite3
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Stop:
    id: int
    code: str
    name: str
    position: int


@dataclass(frozen=True)
class Route:
    id: int
    code: str
    name: str
    stops: list[Stop] = field(default_factory=list)


@dataclass(frozen=True)
class Departure:
    id: int
    route_id: int
    route_code: str
    shuttle_id: int
    shuttle_code: str
    scheduled_at: dt.datetime
    seat_count: int


_DEPARTURE_SQL = """
SELECT d.id, d.route_id, r.code AS route_code, d.shuttle_id, s.code AS shuttle_code,
       d.scheduled_at, d.seat_count
FROM departures d
JOIN routes r ON r.id = d.route_id
JOIN shuttles s ON s.id = d.shuttle_id
"""


def _departure(row) -> Departure:
    return Departure(
        id=row["id"], route_id=row["route_id"], route_code=row["route_code"],
        shuttle_id=row["shuttle_id"], shuttle_code=row["shuttle_code"],
        scheduled_at=dt.datetime.fromisoformat(row["scheduled_at"]),
        seat_count=row["seat_count"])


def get_departure(conn: sqlite3.Connection, departure_id: int) -> Departure | None:
    row = conn.execute(_DEPARTURE_SQL + " WHERE d.id = ?", (departure_id,)).fetchone()
    return _departure(row) if row else None


def list_routes(conn: sqlite3.Connection) -> list[Route]:
    rows = conn.execute(
        "SELECT r.id AS route_id, r.code AS route_code, r.name AS route_name, "
        "       s.id, s.code, s.name, rs.position "
        "FROM routes r JOIN route_stops rs ON rs.route_id = r.id "
        "JOIN stops s ON s.id = rs.stop_id ORDER BY r.code, rs.position").fetchall()
    routes: dict[int, Route] = {}
    for row in rows:
        route = routes.setdefault(
            row["route_id"], Route(row["route_id"], row["route_code"], row["route_name"]))
        route.stops.append(Stop(row["id"], row["code"], row["name"], row["position"]))
    return list(routes.values())


def list_departures_for_date(conn: sqlite3.Connection, service_date: dt.date) -> list[Departure]:
    rows = conn.execute(
        _DEPARTURE_SQL + " WHERE d.service_date = ? ORDER BY d.route_id, d.scheduled_at",
        (service_date.isoformat(),)).fetchall()
    return [_departure(r) for r in rows]


def list_departures_for_route(conn: sqlite3.Connection, route_id: int,
                              service_date: dt.date) -> list[Departure]:
    return [d for d in list_departures_for_date(conn, service_date) if d.route_id == route_id]
