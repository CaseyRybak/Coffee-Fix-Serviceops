from __future__ import annotations

from typing import Protocol

from serviceops_api.staff_auth import StaffUser
from serviceops_api.technicians.models import (
    DiagnosisChecklistPayload,
    RecordPartsUsedPayload,
    RepairResultPayload,
    TechnicianActionResponse,
    TechnicianRequestDetail,
    TechnicianRequestListResponse,
)
from serviceops_api.inventory.repository import InventoryStore


class TechnicianServiceRequestStore(Protocol):
    def list_requests_for_technician(self, technician_identifier: str) -> list[dict[str, object]]:
        """Return requests assigned to a technician."""

    def get_technician_request(self, request_number: str, technician_identifier: str) -> dict[str, object]:
        """Return a technician-safe request detail."""

    def record_technician_diagnosis(
        self,
        request_number: str,
        technician_identifier: str,
        checklist: dict[str, bool],
        summary: str,
        actor: str,
    ) -> str:
        """Persist diagnosis and append a status event."""

    def record_technician_result(
        self,
        request_number: str,
        technician_identifier: str,
        result: str,
        summary: str,
        next_step: str | None,
        actor: str,
    ) -> str:
        """Persist repair result and append a status event."""

    def record_technician_parts_used_status(
        self,
        request_number: str,
        technician_identifier: str,
        actor: str,
    ) -> str:
        """Append a request-history event after parts usage."""


def technician_identifier(staff: StaffUser) -> str:
    return staff.username


class ListTechnicianRequests:
    def __init__(self, repository: TechnicianServiceRequestStore) -> None:
        self._repository = repository

    def execute(self, staff: StaffUser) -> TechnicianRequestListResponse:
        return TechnicianRequestListResponse.model_validate(
            {"items": self._repository.list_requests_for_technician(technician_identifier(staff))}
        )


class GetTechnicianRequest:
    def __init__(self, repository: TechnicianServiceRequestStore) -> None:
        self._repository = repository

    def execute(self, request_number: str, staff: StaffUser) -> TechnicianRequestDetail:
        return TechnicianRequestDetail.model_validate(
            self._repository.get_technician_request(request_number, technician_identifier(staff))
        )


class RecordTechnicianDiagnosis:
    def __init__(self, repository: TechnicianServiceRequestStore) -> None:
        self._repository = repository

    def execute(
        self,
        request_number: str,
        payload: DiagnosisChecklistPayload,
        staff: StaffUser,
    ) -> TechnicianActionResponse:
        status = self._repository.record_technician_diagnosis(
            request_number=request_number,
            technician_identifier=technician_identifier(staff),
            checklist={
                "machine_powered_on": payload.machine_powered_on,
                "water_supply_checked": payload.water_supply_checked,
                "leak_checked": payload.leak_checked,
                "error_code_checked": payload.error_code_checked,
            },
            summary=payload.summary,
            actor="technician",
        )
        return TechnicianActionResponse(
            request_number=request_number,
            status=status,  # type: ignore[arg-type]
            message="Technician diagnosis recorded",
        )


class RecordTechnicianResult:
    def __init__(self, repository: TechnicianServiceRequestStore) -> None:
        self._repository = repository

    def execute(
        self,
        request_number: str,
        payload: RepairResultPayload,
        staff: StaffUser,
    ) -> TechnicianActionResponse:
        status = self._repository.record_technician_result(
            request_number=request_number,
            technician_identifier=technician_identifier(staff),
            result=payload.result,
            summary=payload.summary,
            next_step=payload.next_step,
            actor="technician",
        )
        return TechnicianActionResponse(
            request_number=request_number,
            status=status,  # type: ignore[arg-type]
            message="Technician result recorded",
        )


class RecordTechnicianPartsUsed:
    def __init__(self, service_repository: TechnicianServiceRequestStore, inventory_repository: InventoryStore) -> None:
        self._service_repository = service_repository
        self._inventory_repository = inventory_repository

    def execute(
        self,
        request_number: str,
        payload: RecordPartsUsedPayload,
        staff: StaffUser,
    ) -> TechnicianActionResponse:
        identifier = technician_identifier(staff)
        self._service_repository.get_technician_request(request_number, identifier)
        self._inventory_repository.record_parts_used(
            request_number=request_number,
            part_id=payload.part_id,
            quantity=payload.quantity,
            note=payload.note,
            actor="technician",
        )
        status = self._service_repository.record_technician_parts_used_status(
            request_number=request_number,
            technician_identifier=identifier,
            actor="technician",
        )
        return TechnicianActionResponse(
            request_number=request_number,
            status=status,  # type: ignore[arg-type]
            message="Technician parts used recorded",
        )
