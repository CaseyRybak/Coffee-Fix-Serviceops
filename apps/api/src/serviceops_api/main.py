from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from serviceops_api.ai_agents.api import create_dispatcher_ai_router
from serviceops_api.ai_agents.providers import DeterministicAiSuggestionProvider
from serviceops_api.ai_agents.repository import (
    PostgresAiSuggestionRepository,
    SqliteAiSuggestionRepository,
    create_ai_suggestion_repository,
)
from serviceops_api.ai_agents.use_cases import (
    AcceptAiClarificationSuggestion,
    GenerateAiSuggestions,
    IgnoreAiSuggestion,
    ListAiSuggestions,
)
from serviceops_api.config import get_settings
from serviceops_api.health import HealthStatus, build_health_status
from serviceops_api.knowledge_base.api import create_knowledge_base_router
from serviceops_api.knowledge_base.embeddings import DeterministicEmbeddingProvider
from serviceops_api.knowledge_base.repository import (
    PostgresKnowledgeBaseRepository,
    SqliteKnowledgeBaseRepository,
    create_knowledge_base_repository,
)
from serviceops_api.knowledge_base.use_cases import IngestKnowledgeDocument, RetrieveKnowledge
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
from serviceops_api.staff_auth import StaffAuthenticator, create_staff_auth_router, require_staff_role


def create_app(
    service_request_repository: ServiceRequestRepository | PostgresServiceRequestRepository | None = None,
    knowledge_base_repository: SqliteKnowledgeBaseRepository | PostgresKnowledgeBaseRepository | None = None,
    ai_suggestion_repository: SqliteAiSuggestionRepository | PostgresAiSuggestionRepository | None = None,
    staff_authenticator: StaffAuthenticator | None = None,
) -> FastAPI:
    app = FastAPI(title="Coffee Fix ServiceOps API")
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["authorization", "content-type"],
    )
    has_injected_repository = (
        service_request_repository is not None
        or knowledge_base_repository is not None
        or ai_suggestion_repository is not None
    )
    repository = service_request_repository or create_service_request_repository(settings)
    knowledge_repository = knowledge_base_repository or (
        SqliteKnowledgeBaseRepository.in_memory()
        if has_injected_repository
        else create_knowledge_base_repository(settings)
    )
    ai_repository = ai_suggestion_repository or (
        SqliteAiSuggestionRepository.in_memory()
        if has_injected_repository
        else create_ai_suggestion_repository(settings)
    )
    embedding_provider = DeterministicEmbeddingProvider(settings.knowledge_embedding_dimensions)
    retrieve_knowledge = RetrieveKnowledge(knowledge_repository, embedding_provider)
    suggestion_provider = DeterministicAiSuggestionProvider()
    authenticator = staff_authenticator or StaffAuthenticator(settings)
    get_public_status = GetPublicStatus(repository)
    app.include_router(create_staff_auth_router(authenticator))
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
        create_knowledge_base_router(
            IngestKnowledgeDocument(knowledge_repository, embedding_provider),
            retrieve_knowledge,
        )
    )
    app.include_router(
        create_dispatcher_router(
            ListDispatcherRequests(repository),
            GetDispatcherRequest(repository, ai_repository),
            UpdateDispatcherStatus(repository),
            AskDispatcherClarification(repository),
            AssignDispatcherTechnician(repository),
            SaveDispatcherInternalNote(repository),
            staff_dependency=require_staff_role("dispatcher", authenticator),
        )
    )
    app.include_router(
        create_dispatcher_ai_router(
            GenerateAiSuggestions(
                repository,
                ai_repository,
                suggestion_provider,
                retrieve_knowledge,
                suggestion_limit=settings.ai_suggestion_limit,
            ),
            ListAiSuggestions(ai_repository),
            AcceptAiClarificationSuggestion(repository, ai_repository),
            IgnoreAiSuggestion(ai_repository),
            staff_dependency=require_staff_role("dispatcher", authenticator),
        )
    )

    @app.get("/health", response_model=HealthStatus)
    def health() -> HealthStatus:
        return build_health_status(settings)

    return app


app = create_app()
