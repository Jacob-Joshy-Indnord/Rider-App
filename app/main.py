"""FastAPI application: read-only routes and today's departures."""
import datetime as dt
import sqlite3
from collections.abc import Callable, Iterator
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI

from app import config, db, repository, seed
from app.schemas import DepartureOut, RouteOut, ShuttleOut, StopOut, TodaysDeparturesOut


def service_today(tz: ZoneInfo, now: dt.datetime | None = None) -> dt.date:
    """The current service day in the shuttle operator's timezone."""
    return (now or dt.datetime.now(tz)).astimezone(tz).date()


def _default_connection_factory() -> sqlite3.Connection:
    conn = db.connect(config.DATABASE_PATH)
    db.create_schema(conn)
    seed.apply_seed(conn)
    return conn


def create_app(connection_factory: Callable[[], sqlite3.Connection] | None = None,
               today: Callable[[], dt.date] | None = None) -> FastAPI:
    app = FastAPI(title="Rider App API", version="1.0.0")
    factory = connection_factory or _default_connection_factory
    today = today or (lambda: service_today(config.SERVICE_TZ))
    shared: dict[str, sqlite3.Connection] = {}

    def get_conn() -> Iterator[sqlite3.Connection]:
        if "conn" not in shared:
            shared["conn"] = factory()
        yield shared["conn"]

    @app.get("/api/v1/departures/today", response_model=TodaysDeparturesOut,
             summary="Routes with ordered stops and today's scheduled departures")
    def todays_departures(conn: sqlite3.Connection = Depends(get_conn)) -> TodaysDeparturesOut:
        day = today()
        by_route: dict[int, list[DepartureOut]] = {}
        for d in repository.list_departures_for_date(conn, day):
            by_route.setdefault(d.route_id, []).append(DepartureOut(
                id=d.id, route_id=d.route_id, scheduled_at=d.scheduled_at,
                seat_count=d.seat_count, shuttle=ShuttleOut(id=d.shuttle_id, code=d.shuttle_code)))
        routes = [
            RouteOut(id=r.id, code=r.code, name=r.name,
                     stops=[StopOut(**vars(s)) for s in r.stops],
                     departures=by_route.get(r.id, []))
            for r in repository.list_routes(conn)
        ]
        return TodaysDeparturesOut(service_date=day, routes=routes)

    return app


app = create_app()
