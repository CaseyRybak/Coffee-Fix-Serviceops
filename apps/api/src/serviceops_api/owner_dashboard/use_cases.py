from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Protocol

from serviceops_api.owner_dashboard.models import (
    IssueGroupItem,
    LowStockRiskItem,
    OwnerDailyReportResponse,
    OwnerDashboardMetrics,
    OwnerDashboardResponse,
    OwnerSlaRiskItem,
    TechnicianWorkloadItem,
)
from serviceops_api.owner_dashboard.sla import calculate_sla_snapshot


ACTIVE_WORK_STATUSES = {"technician_assigned", "visit_scheduled", "diagnostics", "waiting_for_parts", "repair_in_progress"}
COMPLETED_STATUSES = {"completed", "closed"}
ISSUE_KEYWORDS = (
    ("no coffee flow", ("no coffee flow", "не течет кофе", "нет пролива", "не льется кофе")),
    ("leak", ("leak", "leaks", "протеч", "течет")),
    ("grinder", ("grinder", "grind", "кофемол", "помол")),
    ("steam", ("steam", "пар", "капучин")),
    ("power", ("power", "включ", "не включается")),
)


class OwnerServiceRequestReader(Protocol):
    def list_owner_dashboard_requests(self) -> list[dict[str, object]]:
        """Return internal request rows for owner dashboard aggregation."""


class InventoryPartReader(Protocol):
    def list_parts(self) -> list[dict[str, object]]:
        """Return inventory parts with stock risk fields."""


class GetOwnerDashboard:
    def __init__(self, request_reader: OwnerServiceRequestReader, inventory_reader: InventoryPartReader) -> None:
        self._request_reader = request_reader
        self._inventory_reader = inventory_reader

    def execute(self, now: datetime | None = None) -> OwnerDashboardResponse:
        generated_at = _normalize_now(now)
        request_rows = self._request_reader.list_owner_dashboard_requests()
        metrics = OwnerDashboardMetrics()
        sla_risks: list[OwnerSlaRiskItem] = []
        workload: dict[str, dict[str, int]] = defaultdict(
            lambda: {"active_requests": 0, "scheduled_visits": 0, "waiting_for_parts": 0}
        )
        issue_groups: Counter[str] = Counter()

        for row in request_rows:
            metrics.total_requests += 1
            status = str(row["status"])
            if status == "new":
                metrics.new_requests += 1
            if status in ACTIVE_WORK_STATUSES:
                metrics.in_progress_requests += 1
            if status == "waiting_for_parts":
                metrics.waiting_for_parts_requests += 1
            if status in COMPLETED_STATUSES:
                metrics.completed_requests += 1

            sla = calculate_sla_snapshot(
                request_number=str(row["request_number"]),
                urgency=str(row["urgency"]),
                status=status,
                created_at=str(row["created_at"]),
                now=generated_at,
            )
            if sla.is_overdue:
                metrics.overdue_requests += 1
            if sla.is_near_deadline:
                metrics.near_deadline_requests += 1
            if sla.state in {"overdue", "near_deadline"}:
                sla_risks.append(_sla_risk_item(row, sla))

            technician = str(row.get("assigned_technician_name") or "").strip()
            if technician and status in ACTIVE_WORK_STATUSES:
                workload[technician]["active_requests"] += 1
                if status == "waiting_for_parts":
                    workload[technician]["waiting_for_parts"] += 1
                if int(row.get("scheduled_visit_count") or 0) > 0:
                    workload[technician]["scheduled_visits"] += 1

            issue_groups[_issue_group(str(row["problem"]))] += 1

        return OwnerDashboardResponse(
            generated_at=generated_at.isoformat(),
            metrics=metrics,
            sla_risks=sorted(sla_risks, key=_risk_sort_key),
            technician_workload=_workload_items(workload),
            top_issue_groups=_issue_group_items(issue_groups),
            low_stock_risk=_low_stock_items(self._inventory_reader.list_parts()),
        )


class GetOwnerDailyReport:
    def __init__(self, dashboard: GetOwnerDashboard) -> None:
        self._dashboard = dashboard

    def execute(self, now: datetime | None = None) -> OwnerDailyReportResponse:
        dashboard = self._dashboard.execute(now)
        generated_at = _parse_datetime(dashboard.generated_at)
        highlights = [
            f"Всего заявок: {dashboard.metrics.total_requests}",
            f"Новые заявки: {dashboard.metrics.new_requests}",
            f"SLA риск: {dashboard.metrics.overdue_requests} просрочено, {dashboard.metrics.near_deadline_requests} близко к сроку",
            f"Ожидают запчасти: {dashboard.metrics.waiting_for_parts_requests}",
            f"Низкий складской остаток: {len(dashboard.low_stock_risk)} позиций",
        ]
        return OwnerDailyReportResponse(
            report_date=generated_at.date().isoformat(),
            generated_at=dashboard.generated_at,
            summary=dashboard.metrics,
            highlights=highlights,
            sla_risks=dashboard.sla_risks,
            low_stock_risk=dashboard.low_stock_risk,
            dashboard_url="/owner",
        )


def _normalize_now(now: datetime | None) -> datetime:
    value = now or datetime.now(UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _sla_risk_item(row: dict[str, object], sla) -> OwnerSlaRiskItem:
    return OwnerSlaRiskItem(
        request_number=str(row["request_number"]),
        status=str(row["status"]),
        urgency=str(row["urgency"]),
        customer_name=str(row["customer_name"]),
        machine_label=_machine_label(row),
        latest_event_title=str(row.get("latest_event_title") or ""),
        sla=sla,
    )


def _risk_sort_key(item: OwnerSlaRiskItem) -> tuple[int, float]:
    state_rank = 0 if item.sla.state == "overdue" else 1
    remaining = item.sla.hours_remaining if item.sla.hours_remaining is not None else 999999.0
    return state_rank, remaining


def _machine_label(row: dict[str, object]) -> str:
    model = str(row.get("model") or "").strip()
    brand = str(row.get("brand") or "").strip()
    return f"{brand} {model}".strip()


def _issue_group(problem: str) -> str:
    lowered = problem.lower()
    for label, keywords in ISSUE_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return label
    words = [word.strip(".,:;!?()[]").lower() for word in problem.split()]
    return " ".join(words[:3]) or "other"


def _workload_items(workload: dict[str, dict[str, int]]) -> list[TechnicianWorkloadItem]:
    return [
        TechnicianWorkloadItem(
            technician_identifier=technician,
            active_requests=counts["active_requests"],
            scheduled_visits=counts["scheduled_visits"],
            waiting_for_parts=counts["waiting_for_parts"],
        )
        for technician, counts in sorted(workload.items())
    ]


def _issue_group_items(issue_groups: Counter[str]) -> list[IssueGroupItem]:
    return [
        IssueGroupItem(label=label, count=count)
        for label, count in sorted(issue_groups.items(), key=lambda item: (-item[1], item[0]))[:5]
    ]


def _low_stock_items(parts: list[dict[str, object]]) -> list[LowStockRiskItem]:
    low_stock = [part for part in parts if bool(part.get("is_low_stock"))]
    return [
        LowStockRiskItem(
            part_id=int(part["part_id"]),
            sku=str(part["sku"]),
            name=str(part["name"]),
            unit=str(part["unit"]),
            available_quantity=int(part["available_quantity"]),
            low_stock_threshold=None
            if part.get("low_stock_threshold") is None
            else int(part["low_stock_threshold"]),
        )
        for part in sorted(low_stock, key=lambda item: (int(item["available_quantity"]), str(item["sku"])))
    ]
