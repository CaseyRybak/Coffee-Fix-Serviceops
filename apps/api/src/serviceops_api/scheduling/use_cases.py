from __future__ import annotations

from typing import Protocol

from serviceops_api.scheduling.models import (
    AppointmentWindowPayload,
    CancelAppointmentPayload,
    RescheduleAppointmentPayload,
    ScheduleListResponse,
    StaffAppointmentResponse,
)
from serviceops_api.staff_auth import StaffUser


class SchedulingStore(Protocol):
    def create_appointment(
        self,
        request_number: str,
        technician_identifier: str,
        technician_name: str | None,
        starts_at: str,
        ends_at: str,
        window_label: str | None,
        actor: str,
    ) -> dict[str, object]:
        """Persist a scheduled appointment."""

    def reschedule_appointment(
        self,
        request_number: str,
        appointment_id: int,
        starts_at: str,
        ends_at: str,
        window_label: str | None,
        reason: str | None,
        actor: str,
    ) -> dict[str, object]:
        """Supersede the current appointment with a new time window."""

    def cancel_appointment(
        self,
        request_number: str,
        appointment_id: int,
        reason: str | None,
        actor: str,
    ) -> dict[str, object]:
        """Cancel an active appointment."""

    def list_dispatcher_schedule(self) -> list[dict[str, object]]:
        """Return all active appointment rows for dispatcher schedule."""

    def list_technician_schedule(self, technician_identifier: str) -> list[dict[str, object]]:
        """Return active appointments for one technician."""


class CreateAppointment:
    def __init__(self, repository: SchedulingStore) -> None:
        self._repository = repository

    def execute(
        self,
        request_number: str,
        payload: AppointmentWindowPayload,
        staff: StaffUser,
    ) -> StaffAppointmentResponse:
        return StaffAppointmentResponse.model_validate(
            self._repository.create_appointment(
                request_number=request_number,
                technician_identifier=payload.technician_identifier,
                technician_name=payload.technician_name,
                starts_at=payload.starts_at,
                ends_at=payload.ends_at,
                window_label=payload.window_label,
                actor="dispatcher",
            )
        )


class RescheduleAppointment:
    def __init__(self, repository: SchedulingStore) -> None:
        self._repository = repository

    def execute(
        self,
        request_number: str,
        appointment_id: int,
        payload: RescheduleAppointmentPayload,
        staff: StaffUser,
    ) -> StaffAppointmentResponse:
        return StaffAppointmentResponse.model_validate(
            self._repository.reschedule_appointment(
                request_number=request_number,
                appointment_id=appointment_id,
                starts_at=payload.starts_at,
                ends_at=payload.ends_at,
                window_label=payload.window_label,
                reason=payload.reason,
                actor="dispatcher",
            )
        )


class CancelAppointment:
    def __init__(self, repository: SchedulingStore) -> None:
        self._repository = repository

    def execute(
        self,
        request_number: str,
        appointment_id: int,
        payload: CancelAppointmentPayload,
        staff: StaffUser,
    ) -> StaffAppointmentResponse:
        return StaffAppointmentResponse.model_validate(
            self._repository.cancel_appointment(
                request_number=request_number,
                appointment_id=appointment_id,
                reason=payload.reason,
                actor="dispatcher",
            )
        )


class ListDispatcherSchedule:
    def __init__(self, repository: SchedulingStore) -> None:
        self._repository = repository

    def execute(self) -> ScheduleListResponse:
        return ScheduleListResponse.model_validate({"items": self._repository.list_dispatcher_schedule()})


class ListTechnicianSchedule:
    def __init__(self, repository: SchedulingStore) -> None:
        self._repository = repository

    def execute(self, staff: StaffUser) -> ScheduleListResponse:
        return ScheduleListResponse.model_validate(
            {"items": self._repository.list_technician_schedule(staff.username)}
        )
