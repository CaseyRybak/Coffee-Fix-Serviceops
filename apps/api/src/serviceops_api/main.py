from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from serviceops_api.config import get_settings
from serviceops_api.health import HealthStatus, build_health_status
from serviceops_api.service_requests.api import create_service_requests_router
from serviceops_api.service_requests.repository import ServiceRequestRepository
from serviceops_api.service_requests.use_cases import CreateServiceRequest


def create_app(service_request_repository: ServiceRequestRepository | None = None) -> FastAPI:
    app = FastAPI(title="Coffee Fix ServiceOps API")
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["POST", "OPTIONS"],
        allow_headers=["content-type"],
    )
    repository = service_request_repository or ServiceRequestRepository(settings.intake_sqlite_path)
    app.include_router(create_service_requests_router(CreateServiceRequest(repository)))

    @app.get("/health", response_model=HealthStatus)
    def health() -> HealthStatus:
        return build_health_status(settings)

    return app


app = create_app()
