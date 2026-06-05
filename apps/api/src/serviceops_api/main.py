from fastapi import FastAPI

from serviceops_api.config import get_settings
from serviceops_api.health import HealthStatus, build_health_status


def create_app() -> FastAPI:
    app = FastAPI(title="Coffee Fix ServiceOps API")

    @app.get("/health", response_model=HealthStatus)
    def health() -> HealthStatus:
        return build_health_status(get_settings())

    return app


app = create_app()

