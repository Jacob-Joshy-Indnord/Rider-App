"""FastAPI application: routes, today's departures and seat booking."""
import datetime as dt
import sqlite3
from collections.abc import Callable, Iterator
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Header, HTTPException, status

from app import booking, config, db, repository, seed
from app.schemas import (BookingIn, BookingOut, DepartureOut, ErrorOut, RouteOut, ShuttleOut,
                         StopOut, TodaysDeparturesOut)

# HTTP status for each booking rejection reason.
_ERROR_STATUS = {
    booking.DepartureNotFound: status.HTTP_404_NOT_FOUND,
    booking.StopNotOnRoute: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


def service_today(tz: ZoneInfo, now: dt.datetime | None = None) -> dt.date:
    """The current service day in the shuttle operator's timezone."""
    return (now or dt.datetime.now(tz)).astimezone(tz).date()


def create_app(connection_factory: Callable[[], sqlite3.Connection] | None = None,
               today: Callable[[], dt.date] | None = None,
               now: Callable[[], dt.datetime] | None = None) -> FastAPI:
    """Build the app.

    Without a connection_factory, each request gets its own connection to
    config.DATABASE_PATH (closed afterwards) so concurrent bookings run in
    separate transactions; schema and seed are applied once on first use.
    A supplied factory's connections are owned by the caller and not closed.
    """
    app = FastAPI(title="Rider App API", version="1.0.0")
    today = today or (lambda: service_today(config.SERVICE_TZ))
    now = now or (lambda: dt.datetime.now(dt.timezone.utc))
    initialised: list[bool] = []

    def get_conn() -> Iterator[sqlite3.Connection]:
        if connection_factory is not None:
            yield connection_factory()
            return
        conn = db.connect(config.DATABASE_PATH)
        try:
            if not initialised:
                db.create_schema(conn)
                seed.apply_seed(conn)
                initialised.append(True)
            yield conn
        finally:
            conn.close()

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

    @app.post("/api/v1/bookings", response_model=BookingOut, status_code=status.HTTP_201_CREATED,
              summary="Book one seat; Confirmed if a seat is free, otherwise Waitlisted",
              responses={404: {"model": ErrorOut}, 409: {"model": ErrorOut},
                         422: {"model": ErrorOut}})
    def create_booking(body: BookingIn, x_rider_id: str = Header(min_length=1),
                       conn: sqlite3.Connection = Depends(get_conn)) -> BookingOut:
        try:
            b = booking.create_booking(conn, x_rider_id, body.departure_id,
                                       body.boarding_stop_id, now=now())
        except booking.BookingError as exc:
            raise HTTPException(_ERROR_STATUS.get(type(exc), status.HTTP_409_CONFLICT),
                                detail={"code": exc.code, "message": str(exc)}) from exc
        return BookingOut(id=b.id, departure_id=b.departure_id,
                          boarding_stop_id=b.boarding_stop_id, status=b.status,
                          waitlist_position=b.waitlist_position, created_at=b.created_at)

    return app


app = create_app()
