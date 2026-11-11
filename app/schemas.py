"""Response models (OpenAPI contract) for the routes/departures API."""
import datetime as dt
from typing import Literal

from pydantic import BaseModel


class StopOut(BaseModel):
    id: int
    code: str
    name: str
    position: int


class ShuttleOut(BaseModel):
    id: int
    code: str


class DepartureOut(BaseModel):
    id: int
    route_id: int
    scheduled_at: dt.datetime
    seat_count: int
    shuttle: ShuttleOut


class RouteOut(BaseModel):
    id: int
    code: str
    name: str
    stops: list[StopOut]
    departures: list[DepartureOut]


class TodaysDeparturesOut(BaseModel):
    service_date: dt.date
    routes: list[RouteOut]


class BookingIn(BaseModel):
    departure_id: int
    boarding_stop_id: int


class BookingOut(BaseModel):
    id: int
    departure_id: int
    boarding_stop_id: int
    status: Literal["CONFIRMED", "WAITLISTED", "CANCELLED"]
    waitlist_position: int | None
    created_at: dt.datetime


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorOut(BaseModel):
    detail: ErrorDetail
