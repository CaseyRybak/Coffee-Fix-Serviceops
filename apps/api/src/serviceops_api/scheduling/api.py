from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, status

from serviceops_api.scheduling.models import (
    AppointmentWindowPayload,
    CancelAppointmentPayload,
    RescheduleAppointmentPayload,
    ScheduleListResponse,
    SchedulingConflictError,
    SchedulingLifecycleError,
    StaffAppointmentResponse,
)
from serviceops_api.scheduling.use_cases import (
    CancelAppointment,
    CreateAppointment,
    ListDispatcherSchedule,
    ListTechnicianSchedule,
    RescheduleAppointment,
)
from serviceops_api.staff_auth import StaffUser


def create_scheduling_router(
    create_appointment: CreateAppointment,
    reschedule_appointment: RescheduleAppointment,
    cancel_appointment: CancelAppointment,
    list_dispatcher_schedule: ListDispatcherSchedule,
    list_technician_schedule: ListTechnicianSchedule,
    dispatcher_staff_dependency: Callable[..., object],
    technician_staff_dependency: Callable[..., object],
) -> APIRouter:
    router = APIRouter(tags=["scheduling"])

    @router.get("/dispatcher/schedule", response_model=ScheduleListResponse)
    async def dispatcher_schedule(_staff: StaffUser = Depends(dispatcher_staff_dependency)) -> ScheduleListResponse:
        return list_dispatcher_schedule.execute()

    @router.post(
        "/dispatcher/service-requests/{request_number}/appointments",
        response_model=StaffAppointmentResponse,
    )
    async def create_dispatcher_appointment(
        request_number: str,
        payload: AppointmentWindowPayload,
        staff: StaffUser = Depends(dispatcher_staff_dependency),
    ) -> StaffAppointmentResponse:
        try:
            return create_appointment.execute(request_number, payload, staff)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found") from exc
        except SchedulingConflictError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except SchedulingLifecycleError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    @router.post(
        "/dispatcher/service-requests/{request_number}/appointments/{appointment_id}/reschedule",
        response_model=StaffAppointmentResponse,
    )
    async def reschedule_dispatcher_appointment(
        request_number: str,
        appointment_id: int,
        payload: RescheduleAppointmentPayload,
        staff: StaffUser = Depends(dispatcher_staff_dependency),
    ) -> StaffAppointmentResponse:
        try:
            return reschedule_appointment.execute(request_number, appointment_id, payload, staff)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found") from exc
        except SchedulingConflictError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except SchedulingLifecycleError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    @router.post(
        "/dispatcher/service-requests/{request_number}/appointments/{appointment_id}/cancel",
        response_model=StaffAppointmentResponse,
    )
    async def cancel_dispatcher_appointment(
        request_number: str,
        appointment_id: int,
        payload: CancelAppointmentPayload,
        staff: StaffUser = Depends(dispatcher_staff_dependency),
    ) -> StaffAppointmentResponse:
        try:
            return cancel_appointment.execute(request_number, appointment_id, payload, staff)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found") from exc
        except SchedulingLifecycleError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    @router.get("/technician/schedule", response_model=ScheduleListResponse)
    async def technician_schedule(staff: StaffUser = Depends(technician_staff_dependency)) -> ScheduleListResponse:
        return list_technician_schedule.execute(staff)

    return router
