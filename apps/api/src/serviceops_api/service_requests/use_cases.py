from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from serviceops_api.service_requests.models import (
    CustomerAnswerPayload,
    CustomerAnswerResponse,
    CreateServiceRequestPayload,
    CreateServiceRequestResponse,
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


class CreateServiceRequest:
    def __init__(self, repository: ServiceRequestStore) -> None:
        self._repository = repository

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
    def __init__(self, repository: ServiceRequestStore) -> None:
        self._repository = repository

    def execute(self, request_number: str, payload: CustomerAnswerPayload) -> CustomerAnswerResponse:
        status = self._repository.record_customer_answer(request_number, payload.question_id, payload.answer)
        return CustomerAnswerResponse(
            request_number=request_number,
            status=status,  # type: ignore[arg-type]
            message="Customer answer recorded",
        )


class CreateTelegramOptIn:
    def __init__(self, repository: ServiceRequestStore) -> None:
        self._repository = repository

    def execute(self, request_number: str, payload: TelegramOptInPayload) -> TelegramOptInResponse:
        return TelegramOptInResponse.model_validate(
            self._repository.create_telegram_opt_in(request_number, payload.telegram)
        )
