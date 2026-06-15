# Scheduling Depth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing dispatcher-entered `visit_window` text into a structured appointment workflow with create, reschedule, cancel, technician capacity checks, schedule views, technician visibility, and request-history updates.

**Architecture:** Keep scheduling as a bounded slice inside the existing modular monolith shape. Add scheduling models/use cases/API as an application boundary, while persisting appointments in the existing service-request repository because the current request aggregate already owns status history, assignment metadata, public snapshots, and technician worklists. Keep public status customer-safe: expose only appointment timing/state and lifecycle events, never technician phone numbers, internal notes, staff audit data, AI internals, or operational metadata.

**Tech Stack:** FastAPI, Pydantic, sqlite/PostgreSQL hand-written migrations, pytest/httpx, React/Vite, Node test runner, existing staff RBAC, existing service-request status timeline.

---

## File Structure

- Create `apps/api/src/serviceops_api/scheduling/__init__.py`: scheduling package marker.
- Create `apps/api/src/serviceops_api/scheduling/models.py`: appointment DTOs, payload validation, schedule list models, availability summaries.
- Create `apps/api/src/serviceops_api/scheduling/use_cases.py`: create, reschedule, cancel, list dispatcher schedule, list technician schedule, and capacity checks.
- Create `apps/api/src/serviceops_api/scheduling/api.py`: dispatcher and technician scheduling routes.
- Modify `apps/api/src/serviceops_api/service_requests/models.py`: add appointment snapshots to dispatcher detail, public status, and technician DTO-facing contracts where needed.
- Modify `apps/api/src/serviceops_api/service_requests/use_cases.py`: extend repository protocol with scheduling methods and, only if kept for backward compatibility, make assignment with `visit_window` delegate to structured appointment creation.
- Modify `apps/api/src/serviceops_api/service_requests/repository.py`: add sqlite appointment table, migration bridge, scheduling persistence methods, public/dispatcher/technician schedule projections, and PostgreSQL initialization for migration `0007`.
- Create `apps/api/src/serviceops_api/migrations/0007_scheduling_appointments.sql`: PostgreSQL appointment table, lifecycle checks, indexes, and compatibility columns.
- Modify `apps/api/src/serviceops_api/main.py`: wire scheduling use cases and routers behind `dispatcher` and `technician` role dependencies.
- Create `apps/api/tests/test_scheduling_workflow.py`: API and repository tests for create, reschedule, cancel, capacity conflicts, lifecycle blocks, public safety, and role protection.
- Modify `apps/api/tests/test_dispatcher_requests.py`: keep legacy assignment behavior passing and assert dispatcher detail includes the current appointment snapshot.
- Modify `apps/api/tests/test_technician_workflow.py`: assert technician lists/details reflect structured appointment timing and cancelled/rescheduled state.
- Modify `apps/api/tests/test_operations_migrate.py`: assert the production migration runner includes scheduling migration through service-request repository initialization.
- Modify `apps/web/src/App.tsx`: add scheduling API helpers, dispatcher schedule view, appointment form/actions, and technician appointment timing/state display.
- Modify `apps/web/src/App.test.tsx`: cover scheduling path builders, dispatcher schedule rendering, appointment controls, and technician schedule cues.
- Modify `apps/web/src/styles.css`: add compact schedule list/calendar-oriented styles using existing internal workspace visual patterns.
- Modify `domains/scheduling/domain.md`: record Phase 15 appointment lifecycle, availability/capacity rules, and public/private boundary.
- Modify `domains/technicians/domain.md`: record technician schedule visibility and capacity assumptions.
- Modify `domains/service-requests/domain.md`: record appointment-created/rescheduled/cancelled status-history semantics.
- Modify `docs/execution-plans/index.md`: after implementation and review, set active phase to Phase 16.
- Modify `project_notes.md`: after implementation and review, move Phase 15 to completed status and set active focus to Phase 16.
- Create `docs/review/phase-15-review.md`: only after local verification and independent review are complete.

## Scheduling Contract

Appointment states:

- `scheduled`: active confirmed appointment.
- `rescheduled`: historical appointment superseded by a newer scheduled appointment.
- `cancelled`: cancelled appointment with no active visit unless a later scheduled appointment exists.

Appointment fields:

- `appointment_id`: internal integer id, visible only to staff APIs.
- `request_number`: public request number.
- `technician_identifier`: staff username used by existing technician assignment matching.
- `technician_name`: display name for dispatcher/staff views; default to `technician_identifier` when no separate name exists.
- `starts_at`: ISO datetime string with timezone offset, required.
- `ends_at`: ISO datetime string with timezone offset, required and greater than `starts_at`.
- `window_label`: short human-friendly label, derived from the datetime range when omitted.
- `status`: appointment state.
- `reschedule_reason`: optional dispatcher-entered reason, max 500 chars.
- `cancel_reason`: optional dispatcher-entered reason, max 500 chars.
- `created_at` and `updated_at`: persistence timestamps.

Capacity rules for Phase 15:

- One technician cannot have two active `scheduled` appointments whose time windows overlap.
- Cancelled and historical `rescheduled` appointments do not block capacity.
- Appointment creation requires an assigned technician or supplies `technician_identifier`; if the request was assigned to a different technician, scheduling updates the request assignment to the appointment technician.
- Scheduling is allowed only for request statuses `new`, `awaiting_assignment`, `technician_assigned`, `visit_scheduled`, and `needs_clarification`.
- Scheduling is blocked for `diagnostics`, `waiting_for_parts`, `repair_in_progress`, `completed`, `closed`, `warranty_case`, and `cancelled`.
- Rescheduling and cancellation are blocked for terminal statuses `completed`, `closed`, `warranty_case`, and `cancelled`.

Public boundary:

- Public status may show customer-safe timeline entries and a current appointment snapshot containing `window_label`, `starts_at`, `ends_at`, and `status`.
- Public status must not expose `appointment_id`, technician phone, internal notes, staff usernames beyond existing event actor labels, capacity diagnostics, or cancellation/reschedule internal reasons unless the text is a customer-safe event description.

Legacy compatibility:

- Keep `service_requests.visit_window` populated with the current active appointment `window_label` so existing dispatcher/technician screens and tests do not break mid-slice.
- Existing `/dispatcher/service-requests/{request_number}/assignment` with `visit_window` should keep returning `visit_scheduled`. It may create a structured appointment using a label-only fallback only if no ISO datetimes are available; however, new scheduling endpoints must be the primary Phase 15 path.

## Task 1: Backend Scheduling Models And Failing API Tests

**Files:**

- Create: `apps/api/src/serviceops_api/scheduling/models.py`
- Create: `apps/api/tests/test_scheduling_workflow.py`

- [ ] Add `apps/api/src/serviceops_api/scheduling/models.py` with Pydantic contracts:

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

AppointmentStatus = Literal["scheduled", "rescheduled", "cancelled"]


def _clean_required(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Field is required")
    return cleaned


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class AppointmentWindowPayload(BaseModel):
    technician_identifier: str = Field(min_length=1, max_length=180)
    technician_name: str | None = Field(default=None, max_length=120)
    starts_at: str = Field(min_length=1, max_length=40)
    ends_at: str = Field(min_length=1, max_length=40)
    window_label: str | None = Field(default=None, max_length=160)

    _clean_technician_identifier = field_validator("technician_identifier")(_clean_required)
    _clean_technician_name = field_validator("technician_name")(_clean_optional)
    _clean_starts_at = field_validator("starts_at")(_clean_required)
    _clean_ends_at = field_validator("ends_at")(_clean_required)
    _clean_window_label = field_validator("window_label")(_clean_optional)


class RescheduleAppointmentPayload(BaseModel):
    starts_at: str = Field(min_length=1, max_length=40)
    ends_at: str = Field(min_length=1, max_length=40)
    window_label: str | None = Field(default=None, max_length=160)
    reason: str | None = Field(default=None, max_length=500)

    _clean_starts_at = field_validator("starts_at")(_clean_required)
    _clean_ends_at = field_validator("ends_at")(_clean_required)
    _clean_window_label = field_validator("window_label")(_clean_optional)
    _clean_reason = field_validator("reason")(_clean_optional)


class CancelAppointmentPayload(BaseModel):
    reason: str | None = Field(default=None, max_length=500)

    _clean_reason = field_validator("reason")(_clean_optional)


class AppointmentSnapshot(BaseModel):
    appointment_id: int
    request_number: str
    technician_identifier: str
    technician_name: str
    starts_at: str
    ends_at: str
    window_label: str
    status: AppointmentStatus
    reschedule_reason: str | None = None
    cancel_reason: str | None = None
    created_at: str
    updated_at: str


class StaffAppointmentResponse(BaseModel):
    request_number: str
    status: str
    appointment: AppointmentSnapshot
    message: str


class ScheduleListItem(BaseModel):
    appointment: AppointmentSnapshot
    request_status: str
    customer_name: str
    machine_label: str
    urgency: str
    address: str
    latest_event_title: str


class ScheduleListResponse(BaseModel):
    items: list[ScheduleListItem]
```

- [ ] Add helper functions to `apps/api/tests/test_scheduling_workflow.py` matching the style of existing API tests:

```python
import asyncio

import httpx

from serviceops_api.main import create_app
from serviceops_api.service_requests.repository import ServiceRequestRepository


def payload(name: str = "Anna Petrova") -> dict[str, object]:
    return {
        "customer": {"name": name, "phone": "+7 999 111-22-33", "telegram": "@anna_fix", "client_type": "coffee_shop"},
        "machine": {"brand": "Jura", "model": "E8", "location_type": "coffee_shop"},
        "problem": "Machine leaks water under the brew group.",
        "address": "Tverskaya district",
        "urgency": "today",
    }


async def post_json(repository: ServiceRequestRepository, path: str, body: dict[str, object], token: str | None = None) -> httpx.Response:
    app = create_app(service_request_repository=repository)
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"} if token else None
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(path, json=body, headers=headers)


async def get_json(repository: ServiceRequestRepository, path: str, token: str | None = None) -> httpx.Response:
    app = create_app(service_request_repository=repository)
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"} if token else None
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path, headers=headers)


async def create_request(repository: ServiceRequestRepository, body: dict[str, object] | None = None) -> str:
    response = await post_json(repository, "/service-requests", body or payload())
    assert response.status_code == 201
    return str(response.json()["request_number"])


async def staff_token(repository: ServiceRequestRepository, username: str, password: str) -> str:
    response = await post_json(repository, "/staff/login", {"username": username, "password": password})
    assert response.status_code == 200
    return str(response.json()["access_token"])
```

- [ ] Add failing test `test_dispatcher_can_create_structured_appointment_and_schedule_view`:

```python
def test_dispatcher_can_create_structured_appointment_and_schedule_view() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository))
    token = asyncio.run(staff_token(repository, "dispatcher@coffeefix.local", "dispatcher-local"))

    response = asyncio.run(
        post_json(
            repository,
            f"/dispatcher/service-requests/{request_number}/appointments",
            {
                "technician_identifier": "technician@coffeefix.local",
                "technician_name": "Pavel Sokolov",
                "starts_at": "2026-06-16T14:00:00+03:00",
                "ends_at": "2026-06-16T16:00:00+03:00",
                "window_label": "16 июня 14:00-16:00",
            },
            token=token,
        )
    )

    assert response.status_code == 200
    body = response.json()
    assert body["request_number"] == request_number
    assert body["status"] == "visit_scheduled"
    assert body["appointment"]["status"] == "scheduled"
    assert body["appointment"]["window_label"] == "16 июня 14:00-16:00"

    schedule = asyncio.run(get_json(repository, "/dispatcher/schedule", token=token)).json()
    assert [item["appointment"]["request_number"] for item in schedule["items"]] == [request_number]
    assert schedule["items"][0]["appointment"]["technician_identifier"] == "technician@coffeefix.local"

    detail = asyncio.run(get_json(repository, f"/dispatcher/service-requests/{request_number}", token=token)).json()
    assert detail["status"] == "visit_scheduled"
    assert detail["assignment"]["technician_name"] == "technician@coffeefix.local"
    assert detail["assignment"]["visit_window"] == "16 июня 14:00-16:00"
    assert detail["appointment"]["window_label"] == "16 июня 14:00-16:00"
    assert detail["timeline"][-1]["title"] == "Визит запланирован"
```

- [ ] Run: `cd apps/api && uv run --extra dev pytest tests/test_scheduling_workflow.py::test_dispatcher_can_create_structured_appointment_and_schedule_view -v`
- [ ] Expected: FAIL because scheduling package/routes do not exist yet.

## Task 2: Scheduling Repository Persistence And Migration

**Files:**

- Modify: `apps/api/src/serviceops_api/service_requests/repository.py`
- Create: `apps/api/src/serviceops_api/migrations/0007_scheduling_appointments.sql`
- Modify: `apps/api/tests/test_scheduling_workflow.py`

- [ ] Add sqlite table creation inside `ServiceRequestRepository.initialize()`:

```sql
CREATE TABLE IF NOT EXISTS request_appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_request_id INTEGER NOT NULL REFERENCES service_requests(id),
    technician_identifier TEXT NOT NULL,
    technician_name TEXT NOT NULL,
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL,
    window_label TEXT NOT NULL,
    status TEXT NOT NULL,
    reschedule_reason TEXT,
    cancel_reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_request_appointments_request
    ON request_appointments (service_request_id);
CREATE INDEX IF NOT EXISTS idx_request_appointments_technician_window
    ON request_appointments (technician_identifier, starts_at, ends_at, status);
```

- [ ] Add PostgreSQL migration `apps/api/src/serviceops_api/migrations/0007_scheduling_appointments.sql`:

```sql
CREATE TABLE IF NOT EXISTS request_appointments (
    id BIGSERIAL PRIMARY KEY,
    service_request_id BIGINT NOT NULL REFERENCES service_requests(id),
    technician_identifier TEXT NOT NULL,
    technician_name TEXT NOT NULL,
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    window_label TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('scheduled', 'rescheduled', 'cancelled')),
    reschedule_reason TEXT,
    cancel_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (ends_at > starts_at)
);

CREATE INDEX IF NOT EXISTS idx_request_appointments_request
    ON request_appointments (service_request_id);
CREATE INDEX IF NOT EXISTS idx_request_appointments_technician_window
    ON request_appointments (technician_identifier, starts_at, ends_at, status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_request_appointments_one_active_per_request
    ON request_appointments (service_request_id)
    WHERE status = 'scheduled';
```

- [ ] In `repository.py`, add constant:

```python
SCHEDULING_MIGRATION_PATH = MIGRATIONS_DIR / "0007_scheduling_appointments.sql"
```

- [ ] Update `PostgresServiceRequestRepository.initialize()` to execute `SCHEDULING_MIGRATION_PATH` after `0004_technician_inventory.sql` when it exists.
- [ ] Add repository methods:

```python
def create_appointment(
    self,
    request_number: str,
    technician_identifier: str,
    technician_name: str | None,
    starts_at: str,
    ends_at: str,
    window_label: str | None,
    actor: str,
) -> dict[str, Any]:
    ...

def reschedule_appointment(
    self,
    request_number: str,
    appointment_id: int,
    starts_at: str,
    ends_at: str,
    window_label: str | None,
    reason: str | None,
    actor: str,
) -> dict[str, Any]:
    ...

def cancel_appointment(self, request_number: str, appointment_id: int, reason: str | None, actor: str) -> dict[str, Any]:
    ...

def list_dispatcher_schedule(self) -> list[dict[str, Any]]:
    ...

def list_technician_schedule(self, technician_identifier: str) -> list[dict[str, Any]]:
    ...

def get_current_appointment(self, request_number: str) -> dict[str, Any] | None:
    ...
```

- [ ] Implement overlap detection in repository SQL:

```sql
SELECT ra.id
FROM request_appointments ra
WHERE ra.technician_identifier = ?
  AND ra.status = 'scheduled'
  AND ra.starts_at < ?
  AND ra.ends_at > ?
  AND ra.id != COALESCE(?, -1)
LIMIT 1
```

Use parameters `(technician_identifier, ends_at, starts_at, ignored_appointment_id)`.

- [ ] Implement lifecycle status blocks by reading current `service_requests.status` before writing.
- [ ] On create, update `service_requests.status = 'visit_scheduled'`, `assigned_technician_name = technician_identifier`, and `visit_window = resolved_window_label`.
- [ ] On reschedule, mark old row `rescheduled`, insert a new `scheduled` row, keep request status `visit_scheduled`, and update `visit_window`.
- [ ] On cancel, mark active row `cancelled`, clear `visit_window`, keep technician assignment, set request status to `technician_assigned`, and append a customer-safe event.
- [ ] Append status events:
  - create: status `visit_scheduled`, title `Визит запланирован`, description `Диспетчер согласовал окно визита мастера.`, actor `dispatcher`;
  - reschedule: status `visit_scheduled`, title `Визит перенесен`, description `Диспетчер обновил согласованное окно визита.`, actor `dispatcher`;
  - cancel: status `technician_assigned`, title `Визит отменен`, description `Окно визита отменено, диспетчер согласует новое время.`, actor `dispatcher`.
- [ ] Add failing/passing repository-backed tests for conflict and lifecycle blocks:

```python
def test_scheduling_rejects_overlapping_technician_window() -> None:
    repository = ServiceRequestRepository.in_memory()
    first = asyncio.run(create_request(repository, payload("Anna Petrova")))
    second = asyncio.run(create_request(repository, payload("Ivan Ivanov")))
    token = asyncio.run(staff_token(repository, "dispatcher@coffeefix.local", "dispatcher-local"))
    first_response = asyncio.run(post_json(repository, f"/dispatcher/service-requests/{first}/appointments", {
        "technician_identifier": "technician@coffeefix.local",
        "starts_at": "2026-06-16T14:00:00+03:00",
        "ends_at": "2026-06-16T16:00:00+03:00",
    }, token=token))
    second_response = asyncio.run(post_json(repository, f"/dispatcher/service-requests/{second}/appointments", {
        "technician_identifier": "technician@coffeefix.local",
        "starts_at": "2026-06-16T15:00:00+03:00",
        "ends_at": "2026-06-16T17:00:00+03:00",
    }, token=token))

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Technician already has an appointment in this window"
```

- [ ] Run: `cd apps/api && uv run --extra dev pytest tests/test_scheduling_workflow.py -v`
- [ ] Expected: tests still fail until use cases/routes are wired in Task 3.

## Task 3: Scheduling Use Cases, API Routes, And RBAC

**Files:**

- Create: `apps/api/src/serviceops_api/scheduling/use_cases.py`
- Create: `apps/api/src/serviceops_api/scheduling/api.py`
- Create: `apps/api/src/serviceops_api/scheduling/__init__.py`
- Modify: `apps/api/src/serviceops_api/main.py`
- Modify: `apps/api/tests/test_scheduling_workflow.py`

- [ ] Create `apps/api/src/serviceops_api/scheduling/use_cases.py`:

```python
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


class SchedulingConflictError(RuntimeError):
    pass


class SchedulingLifecycleError(RuntimeError):
    pass


class SchedulingStore(Protocol):
    def create_appointment(self, request_number: str, technician_identifier: str, technician_name: str | None, starts_at: str, ends_at: str, window_label: str | None, actor: str) -> dict[str, object]:
        ...
    def reschedule_appointment(self, request_number: str, appointment_id: int, starts_at: str, ends_at: str, window_label: str | None, reason: str | None, actor: str) -> dict[str, object]:
        ...
    def cancel_appointment(self, request_number: str, appointment_id: int, reason: str | None, actor: str) -> dict[str, object]:
        ...
    def list_dispatcher_schedule(self) -> list[dict[str, object]]:
        ...
    def list_technician_schedule(self, technician_identifier: str) -> list[dict[str, object]]:
        ...


class CreateAppointment:
    def __init__(self, repository: SchedulingStore) -> None:
        self._repository = repository

    def execute(self, request_number: str, payload: AppointmentWindowPayload, staff: StaffUser) -> StaffAppointmentResponse:
        result = self._repository.create_appointment(request_number, payload.technician_identifier, payload.technician_name, payload.starts_at, payload.ends_at, payload.window_label, "dispatcher")
        return StaffAppointmentResponse.model_validate(result)


class RescheduleAppointment:
    def __init__(self, repository: SchedulingStore) -> None:
        self._repository = repository

    def execute(self, request_number: str, appointment_id: int, payload: RescheduleAppointmentPayload, staff: StaffUser) -> StaffAppointmentResponse:
        result = self._repository.reschedule_appointment(request_number, appointment_id, payload.starts_at, payload.ends_at, payload.window_label, payload.reason, "dispatcher")
        return StaffAppointmentResponse.model_validate(result)


class CancelAppointment:
    def __init__(self, repository: SchedulingStore) -> None:
        self._repository = repository

    def execute(self, request_number: str, appointment_id: int, payload: CancelAppointmentPayload, staff: StaffUser) -> StaffAppointmentResponse:
        result = self._repository.cancel_appointment(request_number, appointment_id, payload.reason, "dispatcher")
        return StaffAppointmentResponse.model_validate(result)


class ListDispatcherSchedule:
    def __init__(self, repository: SchedulingStore) -> None:
        self._repository = repository

    def execute(self) -> ScheduleListResponse:
        return ScheduleListResponse.model_validate({"items": self._repository.list_dispatcher_schedule()})


class ListTechnicianSchedule:
    def __init__(self, repository: SchedulingStore) -> None:
        self._repository = repository

    def execute(self, staff: StaffUser) -> ScheduleListResponse:
        return ScheduleListResponse.model_validate({"items": self._repository.list_technician_schedule(staff.username)})
```

- [ ] Create `apps/api/src/serviceops_api/scheduling/api.py` with routes:

```python
from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, status

from serviceops_api.scheduling.models import AppointmentWindowPayload, CancelAppointmentPayload, RescheduleAppointmentPayload, ScheduleListResponse, StaffAppointmentResponse
from serviceops_api.scheduling.use_cases import CancelAppointment, CreateAppointment, ListDispatcherSchedule, ListTechnicianSchedule, RescheduleAppointment, SchedulingConflictError, SchedulingLifecycleError
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

    @router.post("/dispatcher/service-requests/{request_number}/appointments", response_model=StaffAppointmentResponse)
    async def create_dispatcher_appointment(request_number: str, payload: AppointmentWindowPayload, staff: StaffUser = Depends(dispatcher_staff_dependency)) -> StaffAppointmentResponse:
        try:
            return create_appointment.execute(request_number, payload, staff)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found") from exc
        except SchedulingConflictError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except SchedulingLifecycleError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    @router.post("/dispatcher/service-requests/{request_number}/appointments/{appointment_id}/reschedule", response_model=StaffAppointmentResponse)
    async def reschedule_dispatcher_appointment(request_number: str, appointment_id: int, payload: RescheduleAppointmentPayload, staff: StaffUser = Depends(dispatcher_staff_dependency)) -> StaffAppointmentResponse:
        try:
            return reschedule_appointment.execute(request_number, appointment_id, payload, staff)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found") from exc
        except SchedulingConflictError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except SchedulingLifecycleError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    @router.post("/dispatcher/service-requests/{request_number}/appointments/{appointment_id}/cancel", response_model=StaffAppointmentResponse)
    async def cancel_dispatcher_appointment(request_number: str, appointment_id: int, payload: CancelAppointmentPayload, staff: StaffUser = Depends(dispatcher_staff_dependency)) -> StaffAppointmentResponse:
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
```

- [ ] Wire in `apps/api/src/serviceops_api/main.py`:

```python
from serviceops_api.scheduling.api import create_scheduling_router
from serviceops_api.scheduling.use_cases import (
    CancelAppointment,
    CreateAppointment,
    ListDispatcherSchedule,
    ListTechnicianSchedule,
    RescheduleAppointment,
)
```

Then include:

```python
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
```

- [ ] Add tests for RBAC:

```python
def test_scheduling_routes_require_staff_roles() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository))
    technician_token = asyncio.run(staff_token(repository, "technician@coffeefix.local", "technician-local"))
    dispatcher_token = asyncio.run(staff_token(repository, "dispatcher@coffeefix.local", "dispatcher-local"))

    unauthenticated = asyncio.run(get_json(repository, "/dispatcher/schedule"))
    wrong_dispatcher_role = asyncio.run(get_json(repository, "/dispatcher/schedule", token=technician_token))
    wrong_technician_role = asyncio.run(get_json(repository, "/technician/schedule", token=dispatcher_token))
    create_without_auth = asyncio.run(post_json(repository, f"/dispatcher/service-requests/{request_number}/appointments", {
        "technician_identifier": "technician@coffeefix.local",
        "starts_at": "2026-06-16T14:00:00+03:00",
        "ends_at": "2026-06-16T16:00:00+03:00",
    }))

    assert unauthenticated.status_code == 401
    assert wrong_dispatcher_role.status_code == 403
    assert wrong_technician_role.status_code == 403
    assert create_without_auth.status_code == 401
```

- [ ] Run: `cd apps/api && uv run --extra dev pytest tests/test_scheduling_workflow.py -v`
- [ ] Expected: scheduling tests pass or expose repository-method defects to fix before continuing.

## Task 4: Dispatcher, Technician, And Public Snapshot Integration

**Files:**

- Modify: `apps/api/src/serviceops_api/service_requests/models.py`
- Modify: `apps/api/src/serviceops_api/service_requests/repository.py`
- Modify: `apps/api/tests/test_dispatcher_requests.py`
- Modify: `apps/api/tests/test_technician_workflow.py`
- Modify: `apps/api/tests/test_scheduling_workflow.py`

- [ ] In `service_requests/models.py`, add staff-safe and public-safe appointment snapshots:

```python
class PublicAppointmentSnapshot(BaseModel):
    starts_at: str
    ends_at: str
    window_label: str
    status: str


class DispatcherAppointmentSnapshot(PublicAppointmentSnapshot):
    appointment_id: int
    technician_identifier: str
    technician_name: str
    reschedule_reason: str | None = None
    cancel_reason: str | None = None
```

- [ ] Add `appointment: PublicAppointmentSnapshot | None` to `PublicStatusResponse`.
- [ ] Add `appointment: DispatcherAppointmentSnapshot | None` to `DispatcherRequestDetail`.
- [ ] Add `appointment: PublicAppointmentSnapshot | None` or equivalent technician-safe field to `TechnicianRequestDetail` in `apps/api/src/serviceops_api/technicians/models.py`.
- [ ] Update repository projections:
  - `_get_public_status()` includes current scheduled appointment if present;
  - `_dispatcher_detail()` includes current appointment;
  - `list_requests_for_technician()` and `get_technician_request()` include structured appointment information and continue returning `visit_window`;
  - `list_dispatcher_requests()` may keep current shape, but schedule view uses `list_dispatcher_schedule()`.
- [ ] Add test `test_reschedule_and_cancel_update_history_technician_and_public_snapshots`:

```python
def test_reschedule_and_cancel_update_history_technician_and_public_snapshots() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository))
    dispatcher = asyncio.run(staff_token(repository, "dispatcher@coffeefix.local", "dispatcher-local"))
    technician = asyncio.run(staff_token(repository, "technician@coffeefix.local", "technician-local"))
    created = asyncio.run(post_json(repository, f"/dispatcher/service-requests/{request_number}/appointments", {
        "technician_identifier": "technician@coffeefix.local",
        "starts_at": "2026-06-16T14:00:00+03:00",
        "ends_at": "2026-06-16T16:00:00+03:00",
        "window_label": "16 июня 14:00-16:00",
    }, token=dispatcher)).json()

    appointment_id = created["appointment"]["appointment_id"]
    rescheduled = asyncio.run(post_json(repository, f"/dispatcher/service-requests/{request_number}/appointments/{appointment_id}/reschedule", {
        "starts_at": "2026-06-17T10:00:00+03:00",
        "ends_at": "2026-06-17T12:00:00+03:00",
        "window_label": "17 июня 10:00-12:00",
        "reason": "Клиент попросил утро",
    }, token=dispatcher))
    new_appointment_id = rescheduled.json()["appointment"]["appointment_id"]
    cancelled = asyncio.run(post_json(repository, f"/dispatcher/service-requests/{request_number}/appointments/{new_appointment_id}/cancel", {
        "reason": "Клиент перенесет позже",
    }, token=dispatcher))

    assert rescheduled.status_code == 200
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "technician_assigned"

    tech_detail = asyncio.run(get_json(repository, f"/technician/service-requests/{request_number}", token=technician)).json()
    assert tech_detail["visit_window"] is None
    assert tech_detail["appointment"] is None

    public_status = asyncio.run(get_json(repository, f"/service-requests/{request_number}/status")).json()
    public_text = str(public_status)
    assert public_status["status"] == "technician_assigned"
    assert public_status["appointment"] is None
    assert "Визит перенесен" in public_text
    assert "Визит отменен" in public_text
    assert "Клиент попросил утро" not in public_text
    assert "Клиент перенесет позже" not in public_text
    assert "appointment_id" not in public_text
```

- [ ] Update existing dispatcher and technician tests where response JSON gains a nullable `appointment` field.
- [ ] Run:
  - `cd apps/api && uv run --extra dev pytest tests/test_scheduling_workflow.py tests/test_dispatcher_requests.py tests/test_technician_workflow.py -v`
- [ ] Expected: all three test modules pass.

## Task 5: Legacy Assignment Compatibility And Lifecycle Edge Cases

**Files:**

- Modify: `apps/api/src/serviceops_api/service_requests/repository.py`
- Modify: `apps/api/tests/test_dispatcher_requests.py`
- Modify: `apps/api/tests/test_scheduling_workflow.py`

- [ ] Keep existing assignment endpoint behavior:
  - assigning without `visit_window` returns `technician_assigned`;
  - assigning with `visit_window` returns `visit_scheduled`;
  - dispatcher detail `assignment.visit_window` remains populated;
  - public status still does not expose technician phone/name.
- [ ] Decide implementation detail:
  - If `visit_window` has no parseable structured times, do not create a structured appointment row from legacy assignment; keep it as legacy metadata.
  - If future UI sends structured appointment endpoints, appointment rows become the source of schedule views.
- [ ] Add lifecycle block test:

```python
def test_scheduling_rejects_terminal_or_in_progress_requests() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository))
    dispatcher = asyncio.run(staff_token(repository, "dispatcher@coffeefix.local", "dispatcher-local"))
    repository.add_status_event(request_number, "diagnostics", "Диагностика начата", "Мастер уже на выезде.", "technician")

    response = asyncio.run(post_json(repository, f"/dispatcher/service-requests/{request_number}/appointments", {
        "technician_identifier": "technician@coffeefix.local",
        "starts_at": "2026-06-16T14:00:00+03:00",
        "ends_at": "2026-06-16T16:00:00+03:00",
    }, token=dispatcher))

    assert response.status_code == 422
    assert response.json()["detail"] == "Request status does not allow scheduling changes"
```

- [ ] Add datetime validation test for `ends_at <= starts_at` returning HTTP 422 with a clear detail from Pydantic or use-case validation.
- [ ] Run:
  - `cd apps/api && uv run --extra dev pytest tests/test_scheduling_workflow.py tests/test_dispatcher_requests.py -v`
- [ ] Expected: compatibility and lifecycle tests pass.

## Task 6: Frontend API Helpers And Dispatcher Schedule View

**Files:**

- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.test.tsx`
- Modify: `apps/web/src/styles.css`

- [ ] Add exported path builders in `App.tsx`:

```ts
export function buildDispatcherSchedulePath(): string {
  return "/dispatcher/schedule";
}

export function buildDispatcherAppointmentPath(requestNumber: string): string {
  return `/dispatcher/service-requests/${normalizeRequestNumber(requestNumber)}/appointments`;
}

export function buildDispatcherAppointmentReschedulePath(requestNumber: string, appointmentId: number): string {
  return `/dispatcher/service-requests/${normalizeRequestNumber(requestNumber)}/appointments/${appointmentId}/reschedule`;
}

export function buildDispatcherAppointmentCancelPath(requestNumber: string, appointmentId: number): string {
  return `/dispatcher/service-requests/${normalizeRequestNumber(requestNumber)}/appointments/${appointmentId}/cancel`;
}

export function buildTechnicianSchedulePath(): string {
  return "/technician/schedule";
}
```

- [ ] Add matching tests in `App.test.tsx`:

```ts
assert.equal(buildDispatcherSchedulePath(), "/dispatcher/schedule");
assert.equal(
  buildDispatcherAppointmentPath(" cfx-20260605-000001 "),
  "/dispatcher/service-requests/CFX-20260605-000001/appointments",
);
assert.equal(
  buildDispatcherAppointmentReschedulePath("CFX-20260605-000001", 7),
  "/dispatcher/service-requests/CFX-20260605-000001/appointments/7/reschedule",
);
assert.equal(
  buildDispatcherAppointmentCancelPath("CFX-20260605-000001", 7),
  "/dispatcher/service-requests/CFX-20260605-000001/appointments/7/cancel",
);
assert.equal(buildTechnicianSchedulePath(), "/technician/schedule");
```

- [ ] Extend TypeScript interfaces:
  - `AppointmentSnapshot`;
  - `ScheduleListItem`;
  - `ScheduleListResponse`;
  - `DispatcherRequestDetail.appointment`;
  - `TechnicianRequestDetail.appointment`.
- [ ] Update `DispatcherPage` props to accept `initialSchedule?: ScheduleListResponse`.
- [ ] Fetch `/dispatcher/schedule` after session load and after successful scheduling actions.
- [ ] Render a compact schedule-oriented panel near the dispatcher list:
  - heading `Расписание`;
  - date/time label;
  - technician identifier/name;
  - request number;
  - customer/machine/address;
  - active appointment status.
- [ ] Add appointment controls in dispatcher detail:
  - create appointment form with technician identifier, optional display name, starts_at, ends_at, window_label;
  - reschedule form when `detail.appointment` exists;
  - cancel button/form when `detail.appointment` exists;
  - preserve existing legacy `Назначить мастера` form for assignment metadata.
- [ ] Keep controls dense and internal-workspace styled; do not add landing-page or marketing elements.
- [ ] Add render test:

```tsx
const html = renderToStaticMarkup(
  <DispatcherPage
    initialList={{ items: [/* existing item */] }}
    initialSchedule={{
      items: [{
        appointment: {
          appointment_id: 7,
          request_number: "CFX-20260605-000001",
          technician_identifier: "technician@coffeefix.local",
          technician_name: "Pavel Sokolov",
          starts_at: "2026-06-16T14:00:00+03:00",
          ends_at: "2026-06-16T16:00:00+03:00",
          window_label: "16 июня 14:00-16:00",
          status: "scheduled",
          reschedule_reason: null,
          cancel_reason: null,
          created_at: "2026-06-15 10:00:00",
          updated_at: "2026-06-15 10:00:00",
        },
        request_status: "visit_scheduled",
        customer_name: "Anna Petrova",
        machine_label: "Jura E8",
        urgency: "today",
        address: "Tverskaya district",
        latest_event_title: "Визит запланирован",
      }],
    }}
    initialDetail={{ ...dispatcherDetail, appointment: { /* same appointment without request_status wrapper */ } }}
  />,
);

assert.match(html, /Расписание/);
assert.match(html, /16 июня 14:00-16:00/);
assert.match(html, /Перенести визит/);
assert.match(html, /Отменить визит/);
```

- [ ] Update `styles.css` with stable dimensions for schedule rows, compact form grids, and no card-inside-card nesting.
- [ ] Run:
  - `npm run web:test`
  - `npm run web:lint`
- [ ] Expected: frontend tests and lint pass.

## Task 7: Technician Schedule View And Appointment State Display

**Files:**

- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.test.tsx`
- Modify: `apps/web/src/styles.css`
- Modify: `apps/api/tests/test_technician_workflow.py`

- [ ] Update `TechnicianPage` props to accept `initialSchedule?: ScheduleListResponse`.
- [ ] Fetch `/technician/schedule` with technician auth headers and render:
  - heading `Мое расписание`;
  - appointment window label;
  - request number and customer;
  - address and machine label.
- [ ] In assigned-visit list/detail, show structured appointment label when `appointment` exists; fallback to `visit_window`.
- [ ] Add render assertions:

```tsx
assert.match(html, /Мое расписание/);
assert.match(html, /16 июня 14:00-16:00/);
assert.match(html, /Запланировано/);
```

- [ ] Add API test that technician schedule includes only appointments for the authenticated technician:

```python
def test_technician_schedule_only_lists_authenticated_technician_appointments() -> None:
    repository = ServiceRequestRepository.in_memory()
    own_request = asyncio.run(create_request(repository, payload("Anna Petrova")))
    other_request = asyncio.run(create_request(repository, payload("Ivan Ivanov")))
    dispatcher = asyncio.run(staff_token(repository, "dispatcher@coffeefix.local", "dispatcher-local"))
    technician = asyncio.run(staff_token(repository, "technician@coffeefix.local", "technician-local"))
    asyncio.run(post_json(repository, f"/dispatcher/service-requests/{own_request}/appointments", {
        "technician_identifier": "technician@coffeefix.local",
        "starts_at": "2026-06-16T14:00:00+03:00",
        "ends_at": "2026-06-16T16:00:00+03:00",
    }, token=dispatcher))
    asyncio.run(post_json(repository, f"/dispatcher/service-requests/{other_request}/appointments", {
        "technician_identifier": "other-tech@coffeefix.local",
        "starts_at": "2026-06-16T17:00:00+03:00",
        "ends_at": "2026-06-16T19:00:00+03:00",
    }, token=dispatcher))

    response = asyncio.run(get_json(repository, "/technician/schedule", token=technician))

    assert response.status_code == 200
    assert [item["appointment"]["request_number"] for item in response.json()["items"]] == [own_request]
```

- [ ] Run:
  - `cd apps/api && uv run --extra dev pytest tests/test_scheduling_workflow.py tests/test_technician_workflow.py -v`
  - `npm run web:test`
  - `npm run web:lint`
- [ ] Expected: technician schedule works in API and UI render tests.

## Task 8: Documentation, Phase Handoff, And Review Artifact

**Files:**

- Modify: `domains/scheduling/domain.md`
- Modify: `domains/technicians/domain.md`
- Modify: `domains/service-requests/domain.md`
- Modify: `docs/execution-plans/index.md`
- Modify: `project_notes.md`
- Create: `docs/review/phase-15-review.md` after independent review

- [ ] Update `domains/scheduling/domain.md` with:
  - appointment lifecycle states;
  - overlap/capacity rule;
  - dispatcher create/reschedule/cancel use cases;
  - technician schedule visibility;
  - Phase 15 remaining limitations: no automatic route optimization, no customer self-scheduling, no notification automation for appointment changes unless explicitly added in a later phase.
- [ ] Update `domains/technicians/domain.md` with:
  - technician schedule lists use staff username as identifier;
  - capacity is one active appointment per overlapping window;
  - technician can see appointment timing and cancellation/reschedule effects but cannot reschedule from technician workspace in Phase 15.
- [ ] Update `domains/service-requests/domain.md` with:
  - scheduling events appended to request history;
  - `visit_scheduled` vs `technician_assigned` behavior;
  - public status appointment safety boundary.
- [ ] After implementation and independent review, update `project_notes.md`:
  - Current Status includes Phase 15 scheduling depth completed.
  - Active Focus becomes `Phase 16: Inventory Reservations`.
  - Next Steps begin with detailed Phase 16 implementation plan.
- [ ] After implementation and independent review, update `docs/execution-plans/index.md`:
  - Active Phase points to `phases/16-inventory-reservations.md`.
  - Detailed Plans includes `detailed/15-scheduling-depth-implementation.md`.
- [ ] Create `docs/review/phase-15-review.md` only after review, with:
  - reviewer role;
  - files reviewed;
  - verification commands and results;
  - blocking issues;
  - non-blocking issues;
  - suggested follow-up slice;
  - documentation updates needed;
  - final recommendation.
- [ ] Run:
  - `python3 tools/repo-checks/check_docs.py`
- [ ] Expected: docs harness passes.

## Verification

- [ ] `python3 tools/repo-checks/check_docs.py`
- [ ] `cd apps/api && uv run --extra dev pytest tests/test_scheduling_workflow.py -v`
- [ ] `cd apps/api && uv run --extra dev pytest tests/test_dispatcher_requests.py tests/test_technician_workflow.py tests/test_service_request_status.py tests/test_operations_migrate.py -v`
- [ ] `cd apps/api && uv run --extra dev pytest`
- [ ] `cd apps/worker && uv run --extra dev pytest`
- [ ] `cd apps/telegram-bot && uv run --extra dev pytest`
- [ ] `npm run web:test`
- [ ] `npm run web:lint`
- [ ] `npm run web:build`
- [ ] `docker compose -f docker-compose.production.yml --env-file .env.example config`
- [ ] `bash -n tools/operations/postgres_backup.sh`
- [ ] `bash -n tools/operations/postgres_restore.sh`
- [ ] `bash -n tools/operations/smoke_test.sh`
- [ ] `python3 tools/operations/test_smoke_script_contract.py`
- [ ] Secret scan before review:
  - `rg -n "sk-|SERVICEOPS_[A-Z0-9_]*(SECRET|TOKEN|PASSWORD|API_KEY)=.+[A-Za-z0-9_-]{16,}" . --glob '!apps/**/.venv/**' --glob '!node_modules/**' --glob '!reference/figma/node_modules/**'`
  - Expected: no real reusable secrets in tracked files.

## Subagent Review Gate

Ask the reviewer to inspect:

- Appointment create/reschedule/cancel lifecycle matches request status rules and does not strand requests in inconsistent statuses.
- Technician worklists and `/technician/schedule` reflect appointment timing, reschedules, and cancellations for only the authenticated technician.
- Dispatcher schedule ergonomics support scanning active appointments and changing/cancelling the current appointment without losing legacy assignment metadata.
- Capacity checks prevent overlapping active appointments for the same technician and do not block cancelled or historical rescheduled appointments.
- Role-protected APIs reject public, unauthenticated, and wrong-role access.
- Public status snapshots remain customer-safe and do not expose appointment ids, technician phone numbers, internal notes, AI data, audit data, or capacity diagnostics.
- Phase 15 does not implement Phase 16 inventory reservations, billing, automatic route optimization, customer self-scheduling, or autonomous AI scheduling decisions.

## Self-Review

- Phase 15 deliverables are covered by Tasks 1-8.
- The plan creates appointment model/persistence, dispatcher actions, technician capacity checks, staff schedule views, technician appointment visibility, request timeline entries, role protection, and tests for creation/rescheduling/cancellation/history.
- The plan keeps `visit_window` compatibility while introducing structured appointment rows as the new scheduling source.
- The plan uses existing FastAPI/Pydantic/sqlite/PostgreSQL/React patterns and avoids introducing a calendar engine or unrelated refactors.
- The plan updates documentation and phase handoff only after implementation and independent review.
- Commit/push steps are intentionally omitted because repository policy forbids commits or pushes without a direct user instruction in the current conversation turn.
