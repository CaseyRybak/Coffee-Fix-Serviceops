from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from serviceops_api.service_requests.models import (
    CustomerAnswerPayload,
    CustomerAnswerResponse,
    CreateServiceRequestPayload,
    CreateServiceRequestResponse,
    DispatcherActionResponse,
    DispatcherAssignmentPayload,
    DispatcherClarificationPayload,
    DispatcherInternalNotePayload,
    DispatcherRequestDetail,
    DispatcherRequestListResponse,
    DispatcherStatusUpdatePayload,
    PublicStatusResponse,
    ServiceRequestRecord,
    TelegramOptInPayload,
    TelegramOptInResponse,
)


class ServiceRequestStore(Protocol):
    def next_sequence(self) -> int:
        """Return the next local request sequence number."""

    def save(self, record: ServiceRequestRecord) -> None:
        """Persist a service request intake record."""

    def get_public_status_by_request_number(self, request_number: str) -> dict[str, object]:
        """Return a public status snapshot by request number."""

    def get_public_status_by_token(self, token: str) -> dict[str, object]:
        """Return a public status snapshot by public token."""

    def record_customer_answer(self, request_number: str, question_id: int, answer: str) -> str:
        """Persist a customer answer for a clarification question."""

    def create_telegram_opt_in(self, request_number: str, telegram: str | None) -> dict[str, object]:
        """Create a Telegram opt-in token for a request."""

    def list_dispatcher_requests(self) -> list[dict[str, object]]:
        """Return internal dispatcher request list items."""

    def get_dispatcher_request(self, request_number: str) -> dict[str, object]:
        """Return an internal dispatcher request detail snapshot."""

    def update_status(self, request_number: str, status: str, title: str, description: str, actor: str) -> str:
        """Update request status and append a status event."""

    def ask_clarification(self, request_number: str, question: str) -> int:
        """Create a clarification question for a request."""

    def assign_technician(
        self,
        request_number: str,
        technician_name: str,
        technician_phone: str | None,
        technician_region: str | None,
        visit_window: str | None,
    ) -> str:
        """Record manual technician assignment metadata."""

    def save_internal_note(self, request_number: str, note: str, actor: str) -> str:
        """Save an internal dispatcher note."""


class AiSuggestionReader(Protocol):
    def list_suggestions(self, request_number: str) -> list[dict[str, object]]:
        """Return AI suggestions for dispatcher detail."""


class NotificationEventPublisher(Protocol):
    def publish_request_created(self, request_number: str) -> None:
        """Publish a request-created notification event."""

    def publish_status_changed(self, request_number: str, new_status: str) -> None:
        """Publish a status-changed notification event."""

    def publish_clarification_requested(self, request_number: str, question_id: int) -> None:
        """Publish a clarification-requested notification event."""

    def publish_customer_answered(self, request_number: str, question_id: int) -> None:
        """Publish a customer-answered notification event."""


class NotificationDeliveryReader(Protocol):
    def list_for_request(self, request_number: str) -> list[dict[str, object]]:
        """Return notification delivery attempts for dispatcher detail."""


class CreateServiceRequest:
    def __init__(
        self,
        repository: ServiceRequestStore,
        notification_publisher: NotificationEventPublisher | None = None,
    ) -> None:
        self._repository = repository
        self._notification_publisher = notification_publisher

    def execute(self, payload: CreateServiceRequestPayload) -> CreateServiceRequestResponse:
        request_number = self._generate_request_number()
        record = ServiceRequestRecord(
            request_number=request_number,
            status="new",
            customer=payload.customer,
            machine=payload.machine,
            problem=payload.problem,
            address=payload.address,
            urgency=payload.urgency,
            attachment_metadata=payload.attachment_metadata,
        )
        self._repository.save(record)
        if self._notification_publisher is not None:
            self._notification_publisher.publish_request_created(request_number)
        return CreateServiceRequestResponse(
            request_number=request_number,
            status="new",
            message="Service request created",
        )

    def _generate_request_number(self) -> str:
        date_part = datetime.now(UTC).strftime("%Y%m%d")
        sequence = self._repository.next_sequence()
        return f"CFX-{date_part}-{sequence:06d}"


class GetPublicStatus:
    def __init__(self, repository: ServiceRequestStore) -> None:
        self._repository = repository

    def by_request_number(self, request_number: str) -> PublicStatusResponse:
        return PublicStatusResponse.model_validate(self._repository.get_public_status_by_request_number(request_number))

    def by_token(self, token: str) -> PublicStatusResponse:
        return PublicStatusResponse.model_validate(self._repository.get_public_status_by_token(token))


class SubmitCustomerAnswer:
    def __init__(
        self,
        repository: ServiceRequestStore,
        notification_publisher: NotificationEventPublisher | None = None,
    ) -> None:
        self._repository = repository
        self._notification_publisher = notification_publisher

    def execute(self, request_number: str, payload: CustomerAnswerPayload) -> CustomerAnswerResponse:
        status = self._repository.record_customer_answer(request_number, payload.question_id, payload.answer)
        if self._notification_publisher is not None:
            self._notification_publisher.publish_customer_answered(request_number, payload.question_id)
        return CustomerAnswerResponse(
            request_number=request_number,
            status=status,  # type: ignore[arg-type]
            message="Customer answer recorded",
        )


class CreateTelegramOptIn:
    def __init__(self, repository: ServiceRequestStore, bot_username: str = "coffeefix_service_bot") -> None:
        self._repository = repository
        self._bot_username = bot_username.strip().lstrip("@") or "coffeefix_service_bot"

    def execute(self, request_number: str, payload: TelegramOptInPayload) -> TelegramOptInResponse:
        opt_in = self._repository.create_telegram_opt_in(request_number, payload.telegram)
        opt_in["link"] = f"https://t.me/{self._bot_username}?start={opt_in['token']}"
        return TelegramOptInResponse.model_validate(opt_in)


class ListDispatcherRequests:
    def __init__(self, repository: ServiceRequestStore) -> None:
        self._repository = repository

    def execute(self) -> DispatcherRequestListResponse:
        return DispatcherRequestListResponse.model_validate({"items": self._repository.list_dispatcher_requests()})


class GetDispatcherRequest:
    def __init__(
        self,
        repository: ServiceRequestStore,
        ai_suggestion_reader: AiSuggestionReader | None = None,
        notification_delivery_reader: NotificationDeliveryReader | None = None,
    ) -> None:
        self._repository = repository
        self._ai_suggestion_reader = ai_suggestion_reader
        self._notification_delivery_reader = notification_delivery_reader

    def execute(self, request_number: str) -> DispatcherRequestDetail:
        detail = self._repository.get_dispatcher_request(request_number)
        if self._ai_suggestion_reader is not None:
            detail = {**detail, "ai_suggestions": self._ai_suggestion_reader.list_suggestions(request_number)}
        if self._notification_delivery_reader is not None:
            detail = {
                **detail,
                "notification_deliveries": self._notification_delivery_reader.list_for_request(request_number),
            }
        return DispatcherRequestDetail.model_validate(detail)


class UpdateDispatcherStatus:
    def __init__(
        self,
        repository: ServiceRequestStore,
        notification_publisher: NotificationEventPublisher | None = None,
    ) -> None:
        self._repository = repository
        self._notification_publisher = notification_publisher

    def execute(self, request_number: str, payload: DispatcherStatusUpdatePayload) -> DispatcherActionResponse:
        status = self._repository.update_status(
            request_number=request_number,
            status=payload.status,
            title=payload.title,
            description=payload.description,
            actor="dispatcher",
        )
        if self._notification_publisher is not None:
            self._notification_publisher.publish_status_changed(request_number, status)
        return DispatcherActionResponse(
            request_number=request_number,
            status=status,  # type: ignore[arg-type]
            message="Dispatcher status updated",
        )


class AskDispatcherClarification:
    def __init__(
        self,
        repository: ServiceRequestStore,
        notification_publisher: NotificationEventPublisher | None = None,
    ) -> None:
        self._repository = repository
        self._notification_publisher = notification_publisher

    def execute(self, request_number: str, payload: DispatcherClarificationPayload) -> DispatcherActionResponse:
        question_id = self._repository.ask_clarification(request_number, payload.question)
        if self._notification_publisher is not None:
            self._notification_publisher.publish_clarification_requested(request_number, question_id)
        return DispatcherActionResponse(
            request_number=request_number,
            status="needs_clarification",
            message="Clarification question created",
        )


class AssignDispatcherTechnician:
    def __init__(self, repository: ServiceRequestStore) -> None:
        self._repository = repository

    def execute(self, request_number: str, payload: DispatcherAssignmentPayload) -> DispatcherActionResponse:
        status = self._repository.assign_technician(
            request_number=request_number,
            technician_name=payload.technician_name,
            technician_phone=payload.technician_phone,
            technician_region=payload.technician_region,
            visit_window=payload.visit_window,
        )
        return DispatcherActionResponse(
            request_number=request_number,
            status=status,  # type: ignore[arg-type]
            message="Technician assignment recorded",
        )


class SaveDispatcherInternalNote:
    def __init__(self, repository: ServiceRequestStore) -> None:
        self._repository = repository

    def execute(self, request_number: str, payload: DispatcherInternalNotePayload) -> DispatcherActionResponse:
        status = self._repository.save_internal_note(request_number, payload.note, "dispatcher")
        return DispatcherActionResponse(
            request_number=request_number,
            status=status,  # type: ignore[arg-type]
            message="Internal note saved",
        )
