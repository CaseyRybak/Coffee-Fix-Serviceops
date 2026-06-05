from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from serviceops_api.service_requests.models import (
    CreateServiceRequestPayload,
    CreateServiceRequestResponse,
    ServiceRequestRecord,
)


class ServiceRequestStore(Protocol):
    def next_sequence(self) -> int:
        """Return the next local request sequence number."""

    def save(self, record: ServiceRequestRecord) -> None:
        """Persist a service request intake record."""


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
