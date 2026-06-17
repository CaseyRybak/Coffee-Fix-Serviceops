from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from serviceops_api.owner_dashboard.models import OwnerDailyReportResponse, OwnerDashboardResponse
from serviceops_api.owner_dashboard.use_cases import GetOwnerDailyReport, GetOwnerDashboard


def create_owner_dashboard_router(
    get_dashboard: GetOwnerDashboard,
    get_daily_report: GetOwnerDailyReport,
    staff_dependency: Depends | None = None,
) -> APIRouter:
    dependencies = [Depends(staff_dependency)] if staff_dependency is not None else []
    router = APIRouter(prefix="/owner", tags=["owner dashboard"], dependencies=dependencies)

    @router.get("/dashboard", response_model=OwnerDashboardResponse)
    async def owner_dashboard(now: str | None = Query(default=None), _staff: Any = None) -> OwnerDashboardResponse:
        return get_dashboard.execute(_parse_now(now))

    @router.get("/daily-report", response_model=OwnerDailyReportResponse)
    async def owner_daily_report(now: str | None = Query(default=None), _staff: Any = None) -> OwnerDailyReportResponse:
        return get_daily_report.execute(_parse_now(now))

    return router


def _parse_now(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.replace("Z", "+00:00")
    if "T" in normalized and " " in normalized:
        head, tail = normalized.rsplit(" ", 1)
        if ":" in tail:
            normalized = f"{head}+{tail}"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid now timestamp") from exc
