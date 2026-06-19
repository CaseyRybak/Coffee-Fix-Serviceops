from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from serviceops_api.ai_agents.api import create_dispatcher_ai_router, create_staff_assistant_router
from serviceops_api.ai_agents.assistant_tools import AssistantToolRegistry, create_assistant_planner
from serviceops_api.ai_agents.providers import create_ai_suggestion_provider
from serviceops_api.ai_agents.repository import (
    PostgresAiAssistantHistoryRepository,
    PostgresAiSuggestionRepository,
    SqliteAiAssistantHistoryRepository,
    SqliteAiSuggestionRepository,
    create_ai_assistant_history_repository,
    create_ai_suggestion_repository,
)
from serviceops_api.ai_agents.use_cases import (
    AcceptAiClarificationSuggestion,
    ConfirmStaffAssistantTool,
    GenerateAiSuggestions,
    IgnoreAiSuggestion,
    ListAiSuggestions,
    ListStaffAssistantRuns,
    RunStaffAssistant,
)
from serviceops_api.config import get_settings
from serviceops_api.health import HealthStatus, build_health_status
from serviceops_api.observability import configure_logging
from serviceops_api.inventory.api import create_inventory_router
from serviceops_api.inventory.repository import (
    PostgresInventoryRepository,
    SqliteInventoryRepository,
    create_inventory_repository,
)
from serviceops_api.inventory.use_cases import (
    AddCompatibility,
    AdjustReservation,
    ApprovePurchaseRequest,
    CancelPurchaseRequest,
    CreatePart,
    CreatePurchaseRequest,
    CreateSupplier,
    CreateLowStockPurchaseDraft,
    GetPurchaseRequest,
    ListParts,
    ListPurchaseRequests,
    ListReservations,
    ListStockMovements,
    ListSuppliers,
    MarkPurchaseRequestOrdered,
    ReceivePurchaseRequest,
    ReleaseReservation,
    ReplacePurchaseRequestItems,
    ReservePart,
    SetStockCount,
    SubmitPurchaseRequest,
)
from serviceops_api.knowledge_base.api import create_knowledge_base_router
from serviceops_api.knowledge_base.embeddings import create_embedding_provider
from serviceops_api.knowledge_base.repository import (
    PostgresKnowledgeBaseRepository,
    SqliteKnowledgeBaseRepository,
    create_knowledge_base_repository,
)
from serviceops_api.knowledge_base.use_cases import IngestKnowledgeDocument, RetrieveKnowledge
from serviceops_api.notifications.api import create_notifications_router
from serviceops_api.notifications.n8n import DisabledN8nClient, N8nDeliveryClient, N8nWebhookClient
from serviceops_api.notifications.repository import (
    PostgresNotificationRepository,
    SqliteNotificationRepository,
    create_notification_repository,
)
from serviceops_api.notifications.use_cases import (
    LinkTelegramOptIn,
    NotificationPublisher,
    OperationalN8nAutomation,
    RecordN8nDeliveryResult,
)
from serviceops_api.owner_dashboard.api import create_owner_dashboard_router
from serviceops_api.owner_dashboard.use_cases import GetOwnerDailyReport, GetOwnerDashboard
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
from serviceops_api.scheduling.api import create_scheduling_router
from serviceops_api.scheduling.use_cases import (
    CancelAppointment,
    CreateAppointment,
    ListDispatcherSchedule,
    ListTechnicianSchedule,
    RescheduleAppointment,
)
from serviceops_api.staff_auth import StaffAuthenticator, create_staff_auth_router, require_staff_any_role, require_staff_role
from serviceops_api.staff_management.api import create_staff_dispatcher_directory_router, create_staff_management_router
from serviceops_api.staff_management.repository import (
    PostgresStaffAccountRepository,
    SqliteStaffAccountRepository,
    create_staff_account_repository,
)
from serviceops_api.staff_management.use_cases import (
    ActivateStaffAccount,
    CreateStaffAccount,
    DeactivateStaffAccount,
    ListStaffAccounts,
    ListStaffAuditEvents,
    ListTechnicianCandidates,
    ResetStaffPassword,
    UpdateStaffProfile,
    UpdateStaffRoles,
)
from serviceops_api.technicians.api import create_technician_profile_router, create_technician_router
from serviceops_api.technicians.repository import (
    PostgresTechnicianProfileRepository,
    SqliteTechnicianProfileRepository,
    create_technician_profile_repository,
)
from serviceops_api.technicians.use_cases import (
    GetTechnicianRequest,
    ListTechnicianRequests,
    ListTechnicianProfiles,
    RecordTechnicianDiagnosis,
    RecordTechnicianPartsUsed,
    RecordTechnicianResult,
    RecommendTechnicians,
    UpsertTechnicianProfile,
)


def create_app(
    service_request_repository: ServiceRequestRepository | PostgresServiceRequestRepository | None = None,
    knowledge_base_repository: SqliteKnowledgeBaseRepository | PostgresKnowledgeBaseRepository | None = None,
    ai_suggestion_repository: SqliteAiSuggestionRepository | PostgresAiSuggestionRepository | None = None,
    ai_assistant_history_repository: SqliteAiAssistantHistoryRepository | PostgresAiAssistantHistoryRepository | None = None,
    inventory_repository: SqliteInventoryRepository | PostgresInventoryRepository | None = None,
    staff_account_repository: SqliteStaffAccountRepository | PostgresStaffAccountRepository | None = None,
    technician_profile_repository: SqliteTechnicianProfileRepository | PostgresTechnicianProfileRepository | None = None,
    notification_repository: SqliteNotificationRepository | PostgresNotificationRepository | None = None,
    n8n_client: N8nDeliveryClient | None = None,
    n8n_callback_secret: str | None = None,
    telegram_bot_api_secret: str | None = None,
    staff_authenticator: StaffAuthenticator | None = None,
) -> FastAPI:
    app = FastAPI(title="Coffee Fix ServiceOps API")
    settings = get_settings()
    settings.validate_runtime()
    configure_logging(settings.service_name, settings.environment)
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
        or ai_assistant_history_repository is not None
        or inventory_repository is not None
        or staff_account_repository is not None
        or technician_profile_repository is not None
        or notification_repository is not None
        or n8n_client is not None
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
    assistant_history_store = ai_assistant_history_repository or (
        SqliteAiAssistantHistoryRepository.in_memory()
        if has_injected_repository
        else create_ai_assistant_history_repository(settings)
    )
    inventory_store = inventory_repository or (
        SqliteInventoryRepository.in_memory()
        if has_injected_repository
        else create_inventory_repository(settings)
    )
    staff_account_store = staff_account_repository or (
        SqliteStaffAccountRepository.in_memory()
        if has_injected_repository
        else create_staff_account_repository(settings)
    )
    technician_profile_store = technician_profile_repository or (
        SqliteTechnicianProfileRepository.in_memory()
        if has_injected_repository
        else create_technician_profile_repository(settings)
    )
    notification_store = notification_repository or (
        SqliteNotificationRepository.in_memory()
        if has_injected_repository
        else create_notification_repository(settings)
    )
    delivery_client = n8n_client or (
        DisabledN8nClient()
        if has_injected_repository
        else N8nWebhookClient(settings)
    )
    notification_publisher = NotificationPublisher(notification_store, delivery_client, repository)
    embedding_provider = create_embedding_provider(settings)
    retrieve_knowledge = RetrieveKnowledge(knowledge_repository, embedding_provider)
    suggestion_provider = create_ai_suggestion_provider(settings)
    authenticator = staff_authenticator or StaffAuthenticator(settings, staff_account_store)
    get_public_status = GetPublicStatus(repository)
    owner_dashboard = GetOwnerDashboard(repository, inventory_store)
    owner_daily_report = GetOwnerDailyReport(owner_dashboard)
    assistant_tools = AssistantToolRegistry(
        service_request_repository=repository,
        owner_dashboard=owner_dashboard,
        owner_daily_report=owner_daily_report,
        retrieve_knowledge=retrieve_knowledge,
        list_parts=ListParts(inventory_store),
        list_purchase_requests=ListPurchaseRequests(inventory_store),
        list_reservations=ListReservations(inventory_store),
        list_suppliers=ListSuppliers(inventory_store),
        list_staff_accounts=ListStaffAccounts(staff_account_store),
        list_technician_profiles=ListTechnicianProfiles(technician_profile_store, staff_account_store),
        recommend_technicians=RecommendTechnicians(repository, technician_profile_store, staff_account_store),
        create_purchase_request=CreatePurchaseRequest(inventory_store, actor="assistant"),
        planner=create_assistant_planner(settings),
    )
    app.include_router(create_staff_auth_router(authenticator))
    app.include_router(
        create_staff_management_router(
            CreateStaffAccount(staff_account_store),
            ListStaffAccounts(staff_account_store),
            UpdateStaffRoles(staff_account_store),
            UpdateStaffProfile(staff_account_store),
            ActivateStaffAccount(staff_account_store),
            DeactivateStaffAccount(staff_account_store),
            ResetStaffPassword(staff_account_store),
            ListStaffAuditEvents(staff_account_store),
            staff_dependency=require_staff_role("admin", authenticator),
        )
    )
    app.include_router(
        create_staff_dispatcher_directory_router(
            ListTechnicianCandidates(staff_account_store),
            staff_dependency=require_staff_role("dispatcher", authenticator),
        )
    )
    app.include_router(
        create_service_requests_router(
            CreateServiceRequest(repository, notification_publisher),
            get_public_status,
            SubmitCustomerAnswer(repository, notification_publisher),
            CreateTelegramOptIn(repository, settings.telegram_bot_username),
        )
    )
    app.include_router(create_public_status_router(get_public_status))
    app.include_router(
        create_knowledge_base_router(
            IngestKnowledgeDocument(knowledge_repository, embedding_provider),
            retrieve_knowledge,
            write_dependency=require_staff_role("admin", authenticator),
            read_dependency=require_staff_any_role({"admin", "dispatcher"}, authenticator),
        )
    )
    app.include_router(
        create_dispatcher_router(
            ListDispatcherRequests(repository),
            GetDispatcherRequest(repository, ai_repository, notification_store),
            UpdateDispatcherStatus(repository, notification_publisher),
            AskDispatcherClarification(repository, notification_publisher),
            AssignDispatcherTechnician(repository),
            SaveDispatcherInternalNote(repository),
            staff_dependency=require_staff_role("dispatcher", authenticator),
        )
    )
    app.include_router(
        create_scheduling_router(
            CreateAppointment(repository),
            RescheduleAppointment(repository),
            CancelAppointment(repository),
            ListDispatcherSchedule(repository),
            ListTechnicianSchedule(repository),
            dispatcher_staff_dependency=require_staff_role("dispatcher", authenticator),
            technician_staff_dependency=require_staff_role("technician", authenticator),
        )
    )
    app.include_router(
        create_notifications_router(
            RecordN8nDeliveryResult(notification_store),
            n8n_callback_secret if n8n_callback_secret is not None else settings.n8n_callback_secret,
            LinkTelegramOptIn(repository),
            telegram_bot_api_secret if telegram_bot_api_secret is not None else settings.telegram_bot_api_secret,
            OperationalN8nAutomation(owner_dashboard, owner_daily_report, notification_store),
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
    app.include_router(
        create_staff_assistant_router(
            RunStaffAssistant(assistant_history_store, assistant_tools),
            ListStaffAssistantRuns(assistant_history_store),
            ConfirmStaffAssistantTool(assistant_history_store, assistant_tools),
            staff_dependency=require_staff_any_role({"admin", "dispatcher", "inventory"}, authenticator),
        )
    )
    app.include_router(
        create_technician_profile_router(
            ListTechnicianProfiles(technician_profile_store, staff_account_store),
            UpsertTechnicianProfile(technician_profile_store, staff_account_store),
            RecommendTechnicians(repository, technician_profile_store, staff_account_store),
            admin_dependency=require_staff_role("admin", authenticator),
            dispatcher_dependency=require_staff_role("dispatcher", authenticator),
        )
    )
    app.include_router(
        create_inventory_router(
            CreatePart(inventory_store),
            AddCompatibility(inventory_store),
            ListParts(inventory_store),
            SetStockCount(inventory_store),
            ReservePart(inventory_store),
            AdjustReservation(inventory_store),
            ReleaseReservation(inventory_store),
            ListReservations(inventory_store),
            ListStockMovements(inventory_store),
            CreateSupplier(inventory_store),
            ListSuppliers(inventory_store),
            CreatePurchaseRequest(inventory_store),
            ListPurchaseRequests(inventory_store),
            GetPurchaseRequest(inventory_store),
            ReplacePurchaseRequestItems(inventory_store),
            SubmitPurchaseRequest(inventory_store),
            ApprovePurchaseRequest(inventory_store),
            MarkPurchaseRequestOrdered(inventory_store),
            ReceivePurchaseRequest(inventory_store),
            CancelPurchaseRequest(inventory_store),
            CreateLowStockPurchaseDraft(inventory_store),
            staff_dependency=require_staff_role("inventory", authenticator),
            read_dependency=require_staff_any_role({"admin", "inventory", "technician"}, authenticator),
            low_stock_dependency=require_staff_any_role({"admin", "dispatcher", "inventory"}, authenticator),
            procurement_read_dependency=require_staff_any_role({"admin", "inventory"}, authenticator),
            procurement_approval_dependency=require_staff_role("admin", authenticator),
        )
    )
    app.include_router(
        create_owner_dashboard_router(
            owner_dashboard,
            owner_daily_report,
            staff_dependency=require_staff_role("admin", authenticator),
        )
    )
    app.include_router(
        create_technician_router(
            ListTechnicianRequests(repository),
            GetTechnicianRequest(repository),
            RecordTechnicianDiagnosis(repository),
            RecordTechnicianResult(repository),
            RecordTechnicianPartsUsed(repository, inventory_store),
            staff_dependency=require_staff_role("technician", authenticator),
        )
    )

    @app.get("/health", response_model=HealthStatus)
    def health() -> HealthStatus:
        return build_health_status(settings)

    return app


app = create_app()
