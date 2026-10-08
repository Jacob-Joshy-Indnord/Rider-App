"""Response models for the departures API (published in the OpenAPI document)."""
from datetime import date, datetime

from pydantic import BaseModel, Field


class StopOut(BaseModel):
    id: str
    name: str
    sequence: int = Field(description="1-based position of the stop along the route")
    boardable: bool = Field(description="False for the final stop, where riders only alight")


class ShuttleOut(BaseModel):
    id: str
    name: str
    seat_count: int


class DepartureOut(BaseModel):
    id: str
    scheduled_at: datetime
    shuttle: ShuttleOut


class RouteOut(BaseModel):
    id: str
    name: str
    origin: str
    destination: str
    stops: list[StopOut]
    departures: list[DepartureOut]


class TodaysDepartures(BaseModel):
    date: date
    timezone: str
    routes: list[RouteOut]
