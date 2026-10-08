"""FastAPI application: today's departures API and the trip-booking view."""
from __future__ import annotations

import os
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse

from app.catalog import Catalog, default_catalog
from app.schemas import DepartureOut, RouteOut, ShuttleOut, StopOut, TodaysDepartures

STATIC_DIR = Path(__file__).parent / "static"
Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_app(clock: Clock = _utc_now, catalog: Catalog | None = None) -> FastAPI:
    catalog = catalog or default_catalog(ZoneInfo(os.environ.get("SHUTTLE_TZ", "UTC")))
    app = FastAPI(title="Rider App — Booking Workflow", version="0.1.0")

    @app.get("/api/departures/today", response_model=TodaysDepartures, tags=["departures"])
    def todays_departures() -> TodaysDepartures:
        """Fixed route directions with ordered stops and today's scheduled departures."""
        today = clock().astimezone(catalog.tz).date()
        departures = catalog.departures_on(today)
        routes = []
        for route in catalog.routes:
            last = len(route.stops)
            routes.append(
                RouteOut(
                    id=route.id,
                    name=route.name,
                    origin=route.origin.name,
                    destination=route.destination.name,
                    stops=[
                        StopOut(id=s.id, name=s.name, sequence=i, boardable=i < last)
                        for i, s in enumerate(route.stops, start=1)
                    ],
                    departures=[
                        DepartureOut(
                            id=d.id,
                            scheduled_at=d.scheduled_at,
                            shuttle=ShuttleOut(
                                id=d.shuttle.id, name=d.shuttle.name, seat_count=d.shuttle.seat_count
                            ),
                        )
                        for d in departures[route.id]
                    ],
                )
            )
        return TodaysDepartures(date=today, timezone=str(catalog.tz), routes=routes)

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse("/book")

    @app.get("/book", include_in_schema=False)
    def booking_view() -> FileResponse:
        return FileResponse(STATIC_DIR / "book.html", media_type="text/html")

    return app


app = create_app()
