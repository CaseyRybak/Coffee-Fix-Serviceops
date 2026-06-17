from __future__ import annotations

from pydantic import BaseModel, Field

from serviceops_api.owner_dashboard.sla import SlaSnapshot


class OwnerDashboardMetrics(BaseModel):
    new_requests: int = 0
    in_progress_requests: int = 0
    waiting_for_parts_requests: int = 0
    completed_requests: int = 0
    overdue_requests: int = 0
    near_deadline_requests: int = 0


class OwnerSlaRiskItem(BaseModel):
    request_number: str
    status: str
    urgency: str
    customer_name: str
    machine_label: str
    latest_event_title: str
    sla: SlaSnapshot


class TechnicianWorkloadItem(BaseModel):
    technician_identifier: str
    active_requests: int
    scheduled_visits: int
    waiting_for_parts: int


class IssueGroupItem(BaseModel):
    label: str
    count: int


class LowStockRiskItem(BaseModel):
    part_id: int
    sku: str
    name: str
    unit: str
    available_quantity: int
    low_stock_threshold: int | None


class OwnerDashboardResponse(BaseModel):
    generated_at: str
    metrics: OwnerDashboardMetrics
    sla_risks: list[OwnerSlaRiskItem] = Field(default_factory=list)
    technician_workload: list[TechnicianWorkloadItem] = Field(default_factory=list)
    top_issue_groups: list[IssueGroupItem] = Field(default_factory=list)
    low_stock_risk: list[LowStockRiskItem] = Field(default_factory=list)


class OwnerDailyReportResponse(BaseModel):
    report_date: str
    generated_at: str
    summary: OwnerDashboardMetrics
    highlights: list[str]
    sla_risks: list[OwnerSlaRiskItem]
    low_stock_risk: list[LowStockRiskItem]
    dashboard_url: str
