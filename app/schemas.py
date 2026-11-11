"""Response models (OpenAPI contract) for the routes/departures API."""
import datetime as dt

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
