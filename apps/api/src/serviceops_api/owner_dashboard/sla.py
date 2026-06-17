from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel


SlaState = Literal["on_track", "near_deadline", "overdue", "inactive"]

INACTIVE_STATUSES = {"completed", "closed", "cancelled", "warranty_case"}
SLA_WINDOWS = {
    "today": (timedelta(hours=8), timedelta(hours=2)),
    "one_two_days": (timedelta(hours=48), timedelta(hours=8)),
    "planned": (timedelta(hours=120), timedelta(hours=24)),
}


class SlaSnapshot(BaseModel):
    request_number: str
    state: SlaState
    deadline_at: str | None
    hours_remaining: float | None
    is_overdue: bool
    is_near_deadline: bool


def calculate_sla_snapshot(
    *,
    request_number: str,
    urgency: str,
    status: str,
    created_at: str,
    now: datetime | None = None,
) -> SlaSnapshot:
    if status in INACTIVE_STATUSES:
        return SlaSnapshot(
            request_number=request_number,
            state="inactive",
            deadline_at=None,
            hours_remaining=None,
            is_overdue=False,
            is_near_deadline=False,
        )

    due_window, near_window = SLA_WINDOWS.get(urgency, SLA_WINDOWS["planned"])
    current_time = _as_aware_utc(now or datetime.now(UTC))
    created_time = _parse_datetime(created_at)
    deadline = created_time + due_window
    remaining = deadline - current_time
    hours_remaining = round(remaining.total_seconds() / 3600, 2)

    if remaining.total_seconds() < 0:
        state: SlaState = "overdue"
    elif remaining <= near_window:
        state = "near_deadline"
    else:
        state = "on_track"

    return SlaSnapshot(
        request_number=request_number,
        state=state,
        deadline_at=deadline.isoformat(),
        hours_remaining=hours_remaining,
        is_overdue=state == "overdue",
        is_near_deadline=state == "near_deadline",
    )


def _parse_datetime(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    if "T" not in normalized and " " in normalized:
        normalized = normalized.replace(" ", "T", 1)
    parsed = datetime.fromisoformat(normalized)
    return _as_aware_utc(parsed)


def _as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
