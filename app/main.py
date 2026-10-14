from fastapi import FastAPI, HTTPException

from .catalog import Catalog, CatalogService, DeparturesToday, Route


def create_app(service: CatalogService | None = None) -> FastAPI:
    service = service or CatalogService()
    app = FastAPI(title="Rider App API")

    @app.get("/routes", response_model=list[Route])
    def list_routes():
        return service.routes()

    @app.get("/departures", response_model=DeparturesToday)
    def todays_departures(route_id: str | None = None):
        if route_id is not None and service.get_route(route_id) is None:
            raise HTTPException(404, "Unknown route")
        return service.departures_today(route_id)

    @app.get("/catalog", response_model=Catalog)
    def catalog():
        return service.catalog()

    return app


app = create_app()
