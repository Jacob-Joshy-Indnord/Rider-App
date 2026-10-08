"""Fixed shuttle catalog: stops, route directions, shuttles and the daily timetable.

Routes are fixed by the business (route planning is out of scope), so the
catalog is static reference data. ``Catalog.departures_on`` expands the daily
timetable into concrete, timezone-aware departures for a given service date.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Stop:
    id: str
    name: str


@dataclass(frozen=True)
class Shuttle:
    id: str
    name: str
    seat_count: int


@dataclass(frozen=True)
class Route:
    id: str
    name: str
    stops: tuple[Stop, ...]

    @property
    def origin(self) -> Stop:
        return self.stops[0]

    @property
    def destination(self) -> Stop:
        return self.stops[-1]


@dataclass(frozen=True)
class ScheduledRun:
    """One entry in the daily timetable: a route leaves at a local time with a shuttle."""

    route_id: str
    local_time: time
    shuttle_id: str


@dataclass(frozen=True)
class Departure:
    id: str
    route: Route
    scheduled_at: datetime
    shuttle: Shuttle


class Catalog:
    def __init__(
        self,
        routes: list[Route],
        shuttles: list[Shuttle],
        timetable: list[ScheduledRun],
        tz: ZoneInfo,
    ) -> None:
        self.routes = routes
        self.shuttles = {s.id: s for s in shuttles}
        self.timetable = timetable
        self.tz = tz
        route_ids = {r.id for r in routes}
        for run in timetable:
            if run.route_id not in route_ids or run.shuttle_id not in self.shuttles:
                raise ValueError(f"timetable entry references unknown route/shuttle: {run}")

    def departures_on(self, service_date: date) -> dict[str, list[Departure]]:
        """Today's departures per route id, sorted by scheduled time."""
        routes = {r.id: r for r in self.routes}
        result: dict[str, list[Departure]] = {r.id: [] for r in self.routes}
        for run in self.timetable:
            scheduled_at = datetime.combine(service_date, run.local_time, tzinfo=self.tz)
            result[run.route_id].append(
                Departure(
                    id=f"{run.route_id}:{service_date.isoformat()}:{run.local_time:%H%M}",
                    route=routes[run.route_id],
                    scheduled_at=scheduled_at,
                    shuttle=self.shuttles[run.shuttle_id],
                )
            )
        for deps in result.values():
            deps.sort(key=lambda d: d.scheduled_at)
        return result


CAMPUS_A = Stop("campus-a", "Campus A")
CAMPUS_B = Stop("campus-b", "Campus B")
METRO = Stop("metro", "Metro")
A_NORTH_GATE = Stop("campus-a-north-gate", "Campus A North Gate")
B_PARKING = Stop("campus-b-parking", "Campus B Parking")


def _route(origin_id: str, dest_id: str, name: str, stops: list[Stop]) -> Route:
    return Route(id=f"{origin_id}-to-{dest_id}", name=name, stops=tuple(stops))


def default_catalog(tz: ZoneInfo) -> Catalog:
    a_out = [CAMPUS_A, A_NORTH_GATE, METRO]
    b_out = [CAMPUS_B, B_PARKING, METRO]
    routes = [
        _route("campus-a", "metro", "Campus A → Metro", a_out),
        _route("metro", "campus-a", "Metro → Campus A", list(reversed(a_out))),
        _route("campus-b", "metro", "Campus B → Metro", b_out),
        _route("metro", "campus-b", "Metro → Campus B", list(reversed(b_out))),
    ]
    shuttles = [
        Shuttle("shuttle-1", "Shuttle 1", 12),
        Shuttle("shuttle-2", "Shuttle 2", 12),
        Shuttle("shuttle-3", "Shuttle 3", 16),
    ]
    t = time
    timetable = [
        # Morning: metro → campuses, evening: campuses → metro, plus midday runs.
        ScheduledRun("metro-to-campus-a", t(7, 30), "shuttle-1"),
        ScheduledRun("metro-to-campus-a", t(8, 30), "shuttle-1"),
        ScheduledRun("metro-to-campus-a", t(12, 30), "shuttle-1"),
        ScheduledRun("campus-a-to-metro", t(8, 0), "shuttle-1"),
        ScheduledRun("campus-a-to-metro", t(16, 30), "shuttle-1"),
        ScheduledRun("campus-a-to-metro", t(17, 30), "shuttle-1"),
        ScheduledRun("metro-to-campus-b", t(7, 45), "shuttle-2"),
        ScheduledRun("metro-to-campus-b", t(8, 45), "shuttle-3"),
        ScheduledRun("metro-to-campus-b", t(12, 45), "shuttle-2"),
        ScheduledRun("campus-b-to-metro", t(8, 15), "shuttle-2"),
        ScheduledRun("campus-b-to-metro", t(16, 45), "shuttle-3"),
        ScheduledRun("campus-b-to-metro", t(17, 45), "shuttle-2"),
    ]
    return Catalog(routes, shuttles, timetable, tz)
