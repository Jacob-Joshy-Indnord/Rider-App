from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app import catalog

app = FastAPI(title="Rider App API", version="0.1.0")


class StopOut(BaseModel):
    id: str
    name: str
    sequence: int


class DepartureOut(BaseModel):
    id: str
    route_id: str
    scheduled_time: str
    seat_count: int
    seats_remaining: int


class RouteOut(BaseModel):
    id: str
    name: str
    stops: list[StopOut]


class RouteWithDeparturesOut(RouteOut):
    departures: list[DepartureOut]


class CatalogOut(BaseModel):
    date: date
    routes: list[RouteWithDeparturesOut]


def _route_out(route: catalog.Route) -> dict:
    return {"id": route.id, "name": route.name,
            "stops": [vars(s) for s in route.stops]}


@app.get("/api/v1/routes", response_model=list[RouteOut])
def list_routes():
    return [_route_out(r) for r in catalog.get_routes()]


@app.get("/api/v1/departures/today", response_model=CatalogOut)
def todays_catalog():
    today = date.today()
    return {"date": today, "routes": [
        {**_route_out(r), "departures": catalog.departures_today(r, today)}
        for r in catalog.get_routes()]}


@app.get("/api/v1/routes/{route_id}/departures/today", response_model=list[DepartureOut])
def route_departures_today(route_id: str):
    route = catalog.get_route(route_id)
    if route is None:
        raise HTTPException(404, "Route not found")
    return catalog.departures_today(route)
