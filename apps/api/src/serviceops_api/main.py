from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from serviceops_api.config import get_settings
from serviceops_api.health import HealthStatus, build_health_status
from serviceops_api.service_requests.api import (
    create_dispatcher_router,
    create_public_status_router,
    create_service_requests_router,
)
from serviceops_api.service_requests.repository import (
    PostgresServiceRequestRepository,
    ServiceRequestRepository,
    create_service_request_repository,
)
from serviceops_api.service_requests.use_cases import (
    AskDispatcherClarification,
    AssignDispatcherTechnician,
    CreateServiceRequest,
    CreateTelegramOptIn,
    GetDispatcherRequest,
    GetPublicStatus,
    ListDispatcherRequests,
    SaveDispatcherInternalNote,
    SubmitCustomerAnswer,
    UpdateDispatcherStatus,
)


def create_app(
    service_request_repository: ServiceRequestRepository | PostgresServiceRequestRepository | None = None,
) -> FastAPI:
    app = FastAPI(title="Coffee Fix ServiceOps API")
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["content-type"],
    )
    repository = service_request_repository or create_service_request_repository(settings)
    get_public_status = GetPublicStatus(repository)
    app.include_router(
        create_service_requests_router(
            CreateServiceRequest(repository),
            get_public_status,
            SubmitCustomerAnswer(repository),
            CreateTelegramOptIn(repository),
        )
    )
    app.include_router(create_public_status_router(get_public_status))
    app.include_router(
        create_dispatcher_router(
            ListDispatcherRequests(repository),
            GetDispatcherRequest(repository),
            UpdateDispatcherStatus(repository),
            AskDispatcherClarification(repository),
            AssignDispatcherTechnician(repository),
            SaveDispatcherInternalNote(repository),
        )
    )

    @app.get("/health", response_model=HealthStatus)
    def health() -> HealthStatus:
        return build_health_status(settings)

    return app


app = create_app()
