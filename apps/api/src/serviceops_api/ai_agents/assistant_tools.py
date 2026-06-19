from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from urllib.error import HTTPError, URLError
from typing import Protocol

from serviceops_api.ai_agents.providers import PostJson, post_json
from serviceops_api.inventory.models import InventoryPartItem
from serviceops_api.inventory.models import CreatePurchaseRequestPayload, PurchaseRequestItemPayload
from serviceops_api.inventory.use_cases import CreatePurchaseRequest, ListParts, ListPurchaseRequests, ListReservations, ListSuppliers
from serviceops_api.knowledge_base.models import KnowledgeRetrievalPayload
from serviceops_api.knowledge_base.use_cases import RetrieveKnowledge
from serviceops_api.owner_dashboard.use_cases import GetOwnerDailyReport, GetOwnerDashboard
from serviceops_api.staff_auth import StaffUser
from serviceops_api.staff_management.use_cases import ListStaffAccounts
from serviceops_api.technicians.use_cases import ListTechnicianProfiles, RecommendTechnicians


REQUEST_NUMBER_PATTERN = re.compile(r"CFX-\d{8}-\d{6}", re.IGNORECASE)
TOOL_POLICIES = {
    "find_request": "read_only",
    "list_overdue_requests": "read_only",
    "search_knowledge_base": "read_only",
    "check_part_stock": "read_only",
    "recommend_technician": "read_only",
    "generate_daily_report": "read_only",
    "answer_requests": "read_only",
    "answer_schedule": "read_only",
    "answer_technicians": "read_only",
    "answer_database_query": "read_only",
    "answer_capabilities": "read_only",
    "answer_service_catalog": "read_only",
    "answer_staff_contacts": "read_only",
    "answer_procurement": "read_only",
    "assistant_self_check": "read_only",
    "create_purchase_request_draft": "requires_confirmation",
}


@dataclass(frozen=True)
class AssistantDateRange:
    start: date
    end: date
    label: str


@dataclass(frozen=True)
class AssistantQueryPlan:
    domain: str
    entity: str
    metric: str
    question_type: str
    date: date | None = None
    date_range: AssistantDateRange | None = None
    status: str = ""
    status_label: str = ""


class AssistantRequestReader(Protocol):
    def list_dispatcher_requests(self) -> list[dict[str, object]]:
        """Return dispatcher request list ordered the same way as the staff UI."""

    def get_dispatcher_request(self, request_number: str) -> dict[str, object]:
        """Return an internal dispatcher request detail."""

    def list_dispatcher_schedule(self) -> list[dict[str, object]]:
        """Return active scheduled appointments for dispatchers."""


class AssistantPlanner(Protocol):
    def plan(self, message: str) -> dict[str, object]:
        """Choose one assistant tool plan for a staff message."""


class OpenAiCompatibleAssistantPlanner:
    def __init__(
        self,
        api_base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 20.0,
        max_retries: int = 2,
        post_json: PostJson = post_json,
    ) -> None:
        self._api_base_url = api_base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._max_retries = max(0, max_retries)
        self._post_json = post_json

    def plan(self, message: str) -> dict[str, object]:
        response = self._request_with_retries(self._build_body(message))
        try:
            content = response["choices"][0]["message"]["content"]  # type: ignore[index]
            parsed = json.loads(str(content))
        except Exception as exc:
            raise RuntimeError("Assistant planner request failed") from exc
        return _validate_planner_output(parsed, message)

    def _request_with_retries(self, body: dict[str, object]) -> dict[str, object]:
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        url = f"{self._api_base_url}/chat/completions"
        for attempt in range(self._max_retries + 1):
            try:
                return self._post_json(url, body, headers, self._timeout_seconds)
            except json.JSONDecodeError as exc:
                raise RuntimeError("Assistant planner request failed") from exc
            except HTTPError as exc:
                if attempt >= self._max_retries or exc.code not in {408, 409, 425, 429, 500, 502, 503, 504}:
                    raise RuntimeError("Assistant planner request failed") from exc
            except (TimeoutError, URLError, OSError) as exc:
                if attempt >= self._max_retries:
                    raise RuntimeError("Assistant planner request failed") from exc
        raise RuntimeError("Assistant planner request failed")

    def _build_body(self, message: str) -> dict[str, object]:
        return {
            "model": self._model,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You route Coffee Fix ServiceOps staff requests to exactly one tool. "
                        "Return only JSON with tool_name and arguments. Do not answer the user directly. "
                        "Allowed tools: find_request, list_overdue_requests, search_knowledge_base, "
                        "check_part_stock, recommend_technician, create_purchase_request_draft, generate_daily_report, "
                        "answer_requests, answer_schedule, answer_technicians, answer_database_query, "
                        "answer_capabilities, answer_service_catalog, answer_staff_contacts, answer_procurement. "
                        "Use answer_requests for questions about totals, counts, request filters, overall request volume, or 'сколько заявок'. "
                        "Use answer_database_query for questions requiring dates, database filters, suppliers, reservations, stock aggregates, technician regions, audit data, notification data, or assistant history. "
                        "Use answer_capabilities for questions about what the assistant can do. "
                        "Use answer_service_catalog for site/service/coverage/supported-brand questions. "
                        "Use answer_staff_contacts for staff or technician contact requests. "
                        "Use answer_procurement for purchase request and procurement status questions. "
                        "Use generate_daily_report only for explicit daily report requests. "
                        "Use answer_schedule for scheduled visit questions. "
                        "Use answer_technicians for technician names, counts, skills, and service regions. "
                        "For ordinal request lookup like 'найди вторую заявку', use find_request with ordinal_position. "
                        "Use find_request when a CFX request number or explicit ordinal request position is present. "
                        "Use create_purchase_request_draft only when supplier_id, part_id, and quantity are explicitly provided. "
                        "Never invent ids. If unsure, choose search_knowledge_base with the original query."
                    ),
                },
                {"role": "user", "content": safe_assistant_text(message)},
            ],
            "temperature": 0.0,
        }


class AssistantToolRegistry:
    def __init__(
        self,
        *,
        service_request_repository: AssistantRequestReader,
        owner_dashboard: GetOwnerDashboard,
        owner_daily_report: GetOwnerDailyReport,
        retrieve_knowledge: RetrieveKnowledge,
        list_parts: ListParts,
        list_purchase_requests: ListPurchaseRequests,
        list_reservations: ListReservations,
        list_suppliers: ListSuppliers,
        list_staff_accounts: ListStaffAccounts,
        list_technician_profiles: ListTechnicianProfiles,
        recommend_technicians: RecommendTechnicians,
        create_purchase_request: CreatePurchaseRequest,
        planner: AssistantPlanner | None = None,
    ) -> None:
        self._service_request_repository = service_request_repository
        self._owner_dashboard = owner_dashboard
        self._owner_daily_report = owner_daily_report
        self._retrieve_knowledge = retrieve_knowledge
        self._list_parts = list_parts
        self._list_purchase_requests = list_purchase_requests
        self._list_reservations = list_reservations
        self._list_suppliers = list_suppliers
        self._list_staff_accounts = list_staff_accounts
        self._list_technician_profiles = list_technician_profiles
        self._recommend_technicians = recommend_technicians
        self._create_purchase_request = create_purchase_request
        self._planner = planner

    def plan(self, message: str) -> dict[str, object]:
        guarded_plan = _guardrail_plan(message)
        if guarded_plan is not None:
            return guarded_plan
        if self._planner is not None:
            try:
                return self._planner.plan(message)
            except Exception:
                pass
        return _deterministic_plan(message)

    def answer(self, message: str, staff: StaffUser) -> dict[str, object]:
        intent = _assistant_intent(message)
        if intent == "purchase_draft":
            plan = self.plan(message)
            tool_call = self.preview(plan, staff)
            assistant_message = _assistant_answer_message(str(tool_call["status"]), str(tool_call["tool_name"]), str(tool_call.get("result_summary") or ""))
            return {"status": str(tool_call["status"]), "assistant_message": assistant_message, "tool_calls": [tool_call]}

        query_spec = _database_query_spec(message)
        if query_spec is not None:
            self._ensure_database_query_allowed(query_spec, staff)
            tool_call = self._answer_database_query(query_spec, message)
            intent = "database_query"
        else:
            if intent == "knowledge" and self._planner is not None:
                try:
                    intent = _intent_from_planned_tool(self._planner.plan(message), intent)
                except Exception:
                    pass
            tool_call = self._answer_read_only(intent, message, staff)
        self_check = _self_check_tool(message, intent, tool_call)
        if self_check["status"] == "failed":
            return {
                "status": "failed",
                "assistant_message": str(self_check["result_summary"]),
                "tool_calls": [tool_call, self_check],
            }
        return {
            "status": str(tool_call["status"]),
            "assistant_message": str(tool_call.get("result_summary") or ""),
            "tool_calls": [tool_call, self_check],
        }

    def _answer_read_only(self, intent: str, message: str, staff: StaffUser) -> dict[str, object]:
        request_number = _request_number(message)
        ordinal_position = _request_ordinal_position(message)
        if ordinal_position is not None and _mentions_request(message):
            self._ensure_allowed("find_request", staff)
            return self._find_request_by_position(ordinal_position)
        if request_number and intent in {"request_lookup", "requests", "recommend_technician"}:
            if intent == "recommend_technician" or _is_recommendation_question(message):
                self._ensure_allowed("recommend_technician", staff)
                return self._recommend_technician(request_number)
            self._ensure_allowed("find_request", staff)
            return self._find_request(request_number)
        if intent == "overdue_requests":
            self._ensure_allowed("list_overdue_requests", staff)
            return self._list_overdue_requests()
        if intent == "capabilities":
            self._ensure_allowed("answer_capabilities", staff)
            return self._answer_capabilities()
        if intent == "service_catalog":
            self._ensure_allowed("answer_service_catalog", staff)
            return self._answer_service_catalog(message)
        if intent == "staff_contacts":
            self._ensure_allowed("answer_staff_contacts", staff)
            return self._answer_staff_contacts(message)
        if intent == "procurement":
            self._ensure_allowed("answer_procurement", staff)
            return self._answer_procurement(message)
        if intent == "database_query":
            self._ensure_allowed("answer_database_query", staff)
            return self._answer_database_query(
                {
                    "domain": "unsupported",
                    "entity": "unknown",
                    "metric": "unsupported",
                    "question_type": "unknown",
                    "required_facets": ["entity", "metric"],
                },
                message,
            )
        if intent == "requests":
            self._ensure_allowed("answer_requests", staff)
            return self._answer_request_metrics(message)
        if intent == "schedule":
            self._ensure_allowed("answer_schedule", staff)
            return self._answer_schedule(message)
        if intent == "technicians":
            self._ensure_allowed("answer_technicians", staff)
            return self._answer_technicians(message)
        if intent == "inventory":
            self._ensure_allowed("check_part_stock", staff)
            return self._check_part_stock(_query(message))
        self._ensure_allowed("search_knowledge_base", staff)
        return self._search_knowledge(_query(message))

    def preview(self, plan: dict[str, object], staff: StaffUser) -> dict[str, object]:
        tool_name = str(plan["tool_name"])
        policy = str(plan["policy"])
        arguments = dict(plan.get("arguments", {}))
        self._ensure_allowed(tool_name, staff)
        if policy == "requires_confirmation":
            return {
                "tool_name": tool_name,
                "policy": policy,
                "status": "confirmation_required",
                "arguments": arguments,
                "result_summary": _mutation_preview(tool_name, arguments),
                "result_refs": [],
            }
        return self.execute(tool_name, arguments, staff)

    def execute(self, tool_name: str, arguments: dict[str, object], staff: StaffUser) -> dict[str, object]:
        self._ensure_allowed(tool_name, staff)
        if tool_name == "find_request":
            if "ordinal_position" in arguments:
                return self._find_request_by_position(int(arguments["ordinal_position"]))
            return self._find_request(str(arguments["request_number"]))
        if tool_name == "list_overdue_requests":
            return self._list_overdue_requests()
        if tool_name == "generate_daily_report":
            return self._generate_daily_report()
        if tool_name == "search_knowledge_base":
            return self._search_knowledge(str(arguments.get("query") or ""))
        if tool_name == "check_part_stock":
            return self._check_part_stock(str(arguments.get("query") or ""))
        if tool_name == "recommend_technician":
            return self._recommend_technician(str(arguments["request_number"]))
        if tool_name == "answer_capabilities":
            return self._answer_capabilities()
        if tool_name == "answer_service_catalog":
            return self._answer_service_catalog(str(arguments.get("query") or ""))
        if tool_name == "answer_staff_contacts":
            return self._answer_staff_contacts(str(arguments.get("query") or ""))
        if tool_name == "answer_procurement":
            return self._answer_procurement(str(arguments.get("query") or ""))
        if tool_name == "create_purchase_request_draft":
            return self._create_purchase_draft(arguments)
        raise ValueError(f"Unsupported assistant tool: {tool_name}")

    def _ensure_allowed(self, tool_name: str, staff: StaffUser) -> None:
        required_roles = {
            "find_request": {"admin", "dispatcher"},
            "list_overdue_requests": {"admin"},
            "generate_daily_report": {"admin"},
            "answer_requests": {"admin"},
            "answer_schedule": {"dispatcher"},
            "answer_technicians": {"admin", "dispatcher"},
            "answer_database_query": {"admin", "dispatcher", "inventory"},
            "answer_capabilities": {"admin", "dispatcher", "inventory"},
            "answer_service_catalog": {"admin", "dispatcher"},
            "answer_staff_contacts": {"admin", "dispatcher"},
            "answer_procurement": {"admin", "inventory"},
            "assistant_self_check": {"admin", "dispatcher", "inventory"},
            "search_knowledge_base": {"admin", "dispatcher"},
            "check_part_stock": {"admin", "inventory"},
            "recommend_technician": {"dispatcher"},
            "create_purchase_request_draft": {"inventory"},
        }[tool_name]
        if not any(role in staff.roles for role in required_roles):
            raise PermissionError("Staff role is not allowed for this assistant tool")

    def _ensure_database_query_allowed(self, query_spec: dict[str, object], staff: StaffUser) -> None:
        domain = str(query_spec.get("domain") or "")
        required_roles = {
            "requests": {"admin"},
            "inventory": {"admin", "inventory"},
            "suppliers": {"admin", "inventory"},
            "technicians": {"admin", "dispatcher"},
            "knowledge": {"admin", "dispatcher"},
            "notifications": {"admin"},
            "staff": {"admin"},
            "appointments": {"admin", "dispatcher"},
            "assistant_history": {"admin"},
        }.get(domain, {"admin"})
        if not any(role in staff.roles for role in required_roles):
            raise PermissionError("Staff role is not allowed for this assistant database query")

    def _find_request(self, request_number: str) -> dict[str, object]:
        detail = self._service_request_repository.get_dispatcher_request(request_number)
        machine = detail.get("machine") if isinstance(detail.get("machine"), dict) else {}
        customer = detail.get("customer") if isinstance(detail.get("customer"), dict) else {}
        summary = (
            f"{detail['request_number']}: {detail['status']}, "
            f"{customer.get('name', 'customer')}, {_machine_label(machine)}, {detail.get('urgency')}"
        )
        return _completed_tool(
            "find_request",
            {"request_number": request_number},
            summary,
            [{"label": str(detail["request_number"]), "target_type": "request", "target_id": str(detail["request_number"]), "href": f"/dispatcher?request={detail['request_number']}"}],
        )

    def _find_request_by_position(self, ordinal_position: int) -> dict[str, object]:
        requests = self._service_request_repository.list_dispatcher_requests()
        if ordinal_position < 1 or ordinal_position > len(requests):
            raise ValueError("Requested ordinal service request does not exist")
        request_number = str(requests[ordinal_position - 1]["request_number"])
        tool_call = self._find_request(request_number)
        tool_call["arguments"] = {"ordinal_position": ordinal_position}
        tool_call["result_summary"] = f"{_ordinal_request_label(ordinal_position)} in the current request list: {tool_call['result_summary']}"
        return tool_call

    def _list_overdue_requests(self) -> dict[str, object]:
        dashboard = self._owner_dashboard.execute()
        overdue = [item for item in dashboard.sla_risks if item.sla.state == "overdue"]
        refs = [
            {"label": item.request_number, "target_type": "request", "target_id": item.request_number, "href": f"/dispatcher?request={item.request_number}"}
            for item in overdue[:10]
        ]
        return _completed_tool(
            "list_overdue_requests",
            {},
            f"Overdue requests: {len(overdue)}" + (f" ({', '.join(item.request_number for item in overdue[:5])})" if overdue else ""),
            refs,
        )

    def _generate_daily_report(self) -> dict[str, object]:
        report = self._owner_daily_report.execute()
        return _completed_tool(
            "generate_daily_report",
            {},
            f"Daily report {report.report_date}: " + "; ".join(report.highlights),
            [{"label": "dashboard_url", "target_type": "owner_dashboard", "target_id": report.dashboard_url, "href": report.dashboard_url}],
        )

    def _answer_database_query(self, query_spec: dict[str, object], message: str) -> dict[str, object]:
        domain = str(query_spec["domain"])
        if domain == "requests":
            return self._answer_request_database_query(query_spec, message)
        if domain == "suppliers":
            return self._answer_supplier_database_query(query_spec, message)
        if domain == "inventory":
            return self._answer_inventory_database_query(query_spec, message)
        if domain == "technicians":
            return self._answer_technician_database_query(query_spec)
        if domain == "staff":
            return self._answer_staff_database_query(query_spec, message)
        if domain == "appointments":
            return self._answer_appointment_database_query(query_spec)
        return _completed_tool(
            "answer_database_query",
            _safe_database_query_arguments(query_spec),
            "Для этого вопроса нет безопасного read-only аналитического представления в ассистенте.",
            [],
        )

    def _answer_request_database_query(self, query_spec: dict[str, object], message: str) -> dict[str, object]:
        target_date = str(query_spec.get("date") or "")
        start_date = str(query_spec.get("start_date") or "")
        end_date = str(query_spec.get("end_date") or "")
        status_filter = str(query_spec.get("status") or "")
        statuses_filter = [str(status) for status in query_spec.get("statuses", [])] if isinstance(query_spec.get("statuses"), list) else []
        effective_statuses = statuses_filter or ([status_filter] if status_filter else [])
        rows = _request_rows_for_analysis(self._service_request_repository, include_timeline=bool(effective_statuses))
        matching = [
            row
            for row in rows
            if _request_row_matches_query_dates(row, effective_statuses, target_date, start_date, end_date)
            and (not effective_statuses or _request_row_has_status(row, effective_statuses))
        ]
        metric_label = str(query_spec.get("status_label") or "") or ("Новые заявки" if status_filter == "new" else "Заявки")
        label = str(query_spec.get("date_label") or "") or (_ru_date_label(target_date) if target_date else "За весь период")
        refs = [
            {
                "label": str(row["request_number"]),
                "target_type": "request",
                "target_id": str(row["request_number"]),
                "href": f"/dispatcher?request={row['request_number']}",
            }
            for row in matching[:10]
            if row.get("request_number")
        ]
        summary = f"{label}: {metric_label}: {len(matching)}."
        if _is_list_question(message) and matching:
            summary += " " + "; ".join(str(row["request_number"]) for row in matching[:10])
        return _completed_tool("answer_database_query", _safe_database_query_arguments(query_spec), summary, refs)

    def _answer_supplier_database_query(self, query_spec: dict[str, object], message: str) -> dict[str, object]:
        suppliers = [supplier for supplier in self._list_suppliers.execute().items if supplier.active]
        refs = [
            {"label": supplier.name, "target_type": "supplier", "target_id": str(supplier.supplier_id), "href": "/inventory"}
            for supplier in suppliers[:10]
        ]
        if _is_count_question(message) and not _is_list_question(message):
            summary = f"Поставщиков: {len(suppliers)}."
        elif suppliers:
            summary = "Поставщики: " + "; ".join(f"{supplier.name} (id={supplier.supplier_id})" for supplier in suppliers[:12])
            if len(suppliers) > 12:
                summary += f"; ещё {len(suppliers) - 12}"
        else:
            summary = "Активные поставщики не найдены."
        return _completed_tool("answer_database_query", _safe_database_query_arguments(query_spec), summary, refs)

    def _answer_inventory_database_query(self, query_spec: dict[str, object], message: str) -> dict[str, object]:
        metric = str(query_spec.get("metric") or "")
        if metric == "parts_count":
            parts = self._list_parts.execute().items
            stocked = [part for part in parts if part.quantity_on_hand > 0]
            available = [part for part in parts if part.available_quantity > 0]
            refs = [
                {"label": part.sku, "target_type": "inventory_part", "target_id": str(part.part_id), "href": "/inventory"}
                for part in parts[:10]
            ]
            label = "Складских позиций запчастей" if "запчаст" in message.casefold() else "Складских позиций"
            summary = f"{label}: {len(parts)}; с остатком на складе: {len(stocked)}; доступных к выдаче: {len(available)}."
            return _completed_tool("answer_database_query", _safe_database_query_arguments(query_spec), summary, refs)
        if metric == "reserved_total":
            reservations = [reservation for reservation in self._list_reservations.execute().items if reservation.status == "active"]
            total = sum(reservation.quantity for reservation in reservations)
            by_unit = _reserved_units(reservations, self._list_parts.execute().items)
            unit_summary = ", ".join(f"{quantity} {unit}" for unit, quantity in by_unit.items()) or f"{total} pcs"
            refs = [
                {"label": reservation.sku, "target_type": "reservation", "target_id": str(reservation.reservation_id), "href": "/inventory"}
                for reservation in reservations[:10]
            ]
            rows = "; ".join(f"{reservation.sku}: {reservation.quantity}" for reservation in reservations[:8])
            tail = f" Позиции: {rows}" if rows else ""
            return _completed_tool(
                "answer_database_query",
                _safe_database_query_arguments(query_spec),
                f"В активном резерве: {unit_summary}.{tail}",
                refs,
            )
        return self._check_part_stock(_query(message))

    def _answer_technician_database_query(self, query_spec: dict[str, object]) -> dict[str, object]:
        profiles = self._list_technician_profiles.execute().items
        active_profiles = [profile for profile in profiles if profile.staff_active and profile.active]
        refs = [
            {"label": profile.display_name, "target_type": "technician", "target_id": f"technician:{index + 1}", "href": "/admin"}
            for index, profile in enumerate(active_profiles[:10])
        ]
        rows: list[str] = []
        all_regions: list[str] = []
        for profile in active_profiles:
            regions = [region for region in profile.service_regions if region.strip()]
            all_regions.extend(regions)
            rows.append(f"{profile.display_name}: {', '.join(regions) if regions else 'районы не настроены'}")
        unique_regions = _unique_preserving_order(all_regions)
        if not rows:
            summary = "Активные мастера не найдены."
        else:
            prefix = "Покрываемые районы: " + (", ".join(unique_regions) if unique_regions else "не настроены")
            summary = prefix + ". По мастерам: " + "; ".join(rows[:10])
        return _completed_tool("answer_database_query", _safe_database_query_arguments(query_spec), summary, refs)

    def _answer_staff_database_query(self, query_spec: dict[str, object], message: str) -> dict[str, object]:
        accounts = self._list_staff_accounts.execute().items
        active_accounts = [account for account in accounts if account.active]
        if _is_count_question(message) and not _is_list_question(message):
            summary = f"Сотрудников: {len(accounts)}; активных: {len(active_accounts)}."
            refs: list[dict[str, object]] = []
        else:
            refs = [
                {"label": account.display_name, "target_type": "staff_account", "target_id": f"staff_account:{index + 1}", "href": "/admin"}
                for index, account in enumerate(active_accounts[:10])
            ]
            rows = "; ".join(f"{account.display_name}: {', '.join(account.roles)}" for account in active_accounts[:10])
            summary = "Сотрудники: " + (rows if rows else "активные сотрудники не найдены") + "."
        return _completed_tool("answer_database_query", _safe_database_query_arguments(query_spec), summary, refs)

    def _answer_appointment_database_query(self, query_spec: dict[str, object]) -> dict[str, object]:
        metric = str(query_spec.get("metric") or "")
        label = str(query_spec.get("date_label") or "") or "за выбранный период"
        if metric == "completed_visits":
            target_date = str(query_spec.get("date") or "")
            start_date = str(query_spec.get("start_date") or "")
            end_date = str(query_spec.get("end_date") or "")
            completed_statuses = ["completed", "closed"]
            rows = _request_rows_for_analysis(self._service_request_repository, include_timeline=True)
            matching = [
                row
                for row in rows
                if _request_row_matches_query_dates(row, completed_statuses, target_date, start_date, end_date)
                and _request_row_has_status(row, completed_statuses)
            ]
            refs = [
                {
                    "label": str(row["request_number"]),
                    "target_type": "request",
                    "target_id": str(row["request_number"]),
                    "href": f"/dispatcher?request={row['request_number']}",
                }
                for row in matching[:10]
                if row.get("request_number")
            ]
            return _completed_tool(
                "answer_database_query",
                _safe_database_query_arguments(query_spec),
                f"{label}: Выполненные визиты: {len(matching)}.",
                refs,
            )
        return _completed_tool(
            "answer_database_query",
            _safe_database_query_arguments(query_spec),
            "Для этого вопроса по визитам нет безопасного read-only аналитического представления в ассистенте.",
            [],
        )

    def _answer_capabilities(self) -> dict[str, object]:
        summary = (
            "Я могу отвечать по данным ServiceOps: заявки и статусы, заявки по датам и периодам, "
            "план визитов, мастера и зоны обслуживания, склад и резервы, поставщики и закупки, "
            "услуги сайта и поддерживаемые бренды, а также искать релевантные ремонтные инструкции в базе знаний. "
            "Изменения в данных не выполняю без явного подтверждения, а чувствительные контакты и секреты не раскрываю."
        )
        return _completed_tool("answer_capabilities", {"scope": "serviceops_staff_assistant"}, summary, [])

    def _answer_service_catalog(self, query: str) -> dict[str, object]:
        lowered = query.casefold()
        supported_brands = ["Jura", "Saeco", "DeLonghi", "La Marzocco", "Nuova Simonelli", "WMF", "Rancilio"]
        requested_brand = _requested_service_brand(query, supported_brands)
        refs = [{"label": "Coffee Fix services", "target_type": "service_catalog", "target_id": "seed://site/services", "href": "seed://site/services"}]
        if requested_brand and requested_brand.casefold() not in {brand.casefold() for brand in supported_brands}:
            return _completed_tool(
                "answer_service_catalog",
                _safe_query_arguments(query),
                (
                    f"По каталогу услуг не нашёл подтверждения, что мы ремонтируем кофемашины «{requested_brand}». "
                    "Подтверждённые бренды: " + ", ".join(supported_brands) + "."
                ),
                refs,
            )
        if _mentions_region_coverage(lowered):
            regions = _service_regions_from_profiles(self._list_technician_profiles.execute().items)
            summary = "Сервисные районы: " + (", ".join(regions) if regions else "районы не настроены в профилях мастеров") + "."
            return _completed_tool("answer_service_catalog", _safe_query_arguments(query), summary, refs)
        if requested_brand:
            return _completed_tool(
                "answer_service_catalog",
                _safe_query_arguments(query),
                f"В каталоге услуг есть подтверждение по бренду {requested_brand}. Поддерживаемые бренды: {', '.join(supported_brands)}.",
                refs,
            )
        return _completed_tool(
            "answer_service_catalog",
            _safe_query_arguments(query),
            (
                "На сайте Coffee Fix указаны услуги: ремонт кофемашин, диагностика, выезд мастера, "
                "обслуживание кофейного оборудования и подбор запчастей. Поддерживаемые бренды: "
                + ", ".join(supported_brands)
                + "."
            ),
            refs,
        )

    def _answer_staff_contacts(self, query: str) -> dict[str, object]:
        refs = [
            {"label": profile.display_name, "target_type": "technician", "target_id": "staff_contact_policy", "href": "/admin"}
            for profile in self._list_technician_profiles.execute().items[:10]
        ]
        return _completed_tool(
            "answer_staff_contacts",
            _safe_query_arguments(query),
            (
                "Телефоны мастеров через AI-помощника не выдаю. "
                "Проверь карточки сотрудников в админке или используй утверждённый рабочий канал связи."
            ),
            refs,
        )

    def _answer_procurement(self, query: str) -> dict[str, object]:
        purchases = self._list_purchase_requests.execute().items
        date_range = _extract_date_range(query)
        status_filter = _procurement_status_filter(query)
        status_label = _procurement_status_label(status_filter)
        matching = []
        for purchase in purchases:
            if status_filter and purchase.status != status_filter:
                continue
            row_date = _row_date(purchase.updated_at if status_filter in {"received", "cancelled"} else purchase.created_at)
            if date_range is not None and not _date_in_range(row_date, date_range):
                continue
            matching.append(purchase)
        received_count = sum(1 for purchase in matching if purchase.status == "received")
        label = date_range.label if date_range is not None else "за весь период"
        refs = [
            {
                "label": f"PR-{purchase.purchase_request_id}",
                "target_type": "purchase_request",
                "target_id": str(purchase.purchase_request_id),
                "href": "/procurement",
            }
            for purchase in matching[:10]
        ]
        if not matching:
            status_part = f" {status_label}" if status_label else ""
            return _completed_tool("answer_procurement", _safe_query_arguments(query) | {"status": status_filter}, f"Закупки{status_part} {label}: записей не найдено.", refs)
        rows: list[str] = []
        for purchase in matching[:8]:
            items = ", ".join(f"{item.sku} x{item.quantity}" for item in purchase.items[:4]) or "без позиций"
            rows.append(f"PR-{purchase.purchase_request_id} {purchase.status} {purchase.supplier_name}: {items}")
        if status_filter and _is_count_question(query) and not _is_list_question(query):
            summary = f"Закупки {status_label}: {len(matching)}."
        else:
            status_part = f" {status_label}" if status_label else ""
            summary = f"Закупки{status_part} {label}: всего: {len(matching)}, получено: {received_count}. " + "; ".join(rows)
        return _completed_tool("answer_procurement", _safe_query_arguments(query) | {"status": status_filter}, summary, refs)

    def _answer_request_metrics(self, message: str) -> dict[str, object]:
        dashboard = self._owner_dashboard.execute()
        report = self._owner_daily_report.execute()
        lowered = message.casefold()
        refs = [{"label": "dashboard_url", "target_type": "owner_dashboard", "target_id": "/owner", "href": "/owner"}]
        if "дневн" in lowered or "отчет" in lowered or "report" in lowered:
            summary = "Операционный отчет: " + "; ".join(report.highlights)
            return _completed_tool("generate_daily_report", _safe_query_arguments(message), summary, refs)
        metrics = dashboard.metrics
        parts: list[str] = []
        if any(marker in lowered for marker in ("нов", "new")):
            parts.append(f"Новые заявки: {metrics.new_requests}")
        if any(marker in lowered for marker in ("работ", "процесс", "in progress")):
            parts.append(f"В работе: {metrics.in_progress_requests}")
        if any(marker in lowered for marker in ("запчаст", "parts")):
            parts.append(f"Ожидают запчасти: {metrics.waiting_for_parts_requests}")
        if any(marker in lowered for marker in ("заверш", "закрыт", "completed", "closed")):
            parts.append(f"Завершено: {metrics.completed_requests}")
        if "sla" in lowered or "просроч" in lowered:
            parts.append(f"Просрочено по SLA: {metrics.overdue_requests}")
            parts.append(f"Близко к сроку: {metrics.near_deadline_requests}")
        if not parts or any(marker in lowered for marker in ("всего", "получено", "total", "сколько")):
            parts.insert(0, f"Всего заявок: {metrics.total_requests}")
        return _completed_tool("answer_requests", _safe_query_arguments(message), "; ".join(parts) + ".", refs)

    def _answer_schedule(self, message: str) -> dict[str, object]:
        schedule = self._service_request_repository.list_dispatcher_schedule()
        refs = [
            {
                "label": str(item["appointment"]["request_number"]),
                "target_type": "appointment",
                "target_id": str(item["appointment"]["appointment_id"]),
                "href": f"/dispatcher?request={item['appointment']['request_number']}",
            }
            for item in schedule[:10]
        ]
        if _is_count_question(message):
            return _completed_tool(
                "answer_schedule",
                _safe_query_arguments(message),
                f"Запланированных визитов мастеров: {len(schedule)}.",
                refs,
            )
        if not schedule:
            return _completed_tool("answer_schedule", _safe_query_arguments(message), "Запланированных визитов мастеров сейчас нет.", refs)
        rows = []
        for item in schedule[:5]:
            appointment = item["appointment"]
            rows.append(
                f"{appointment['request_number']}: {appointment['technician_name']}, "
                f"{appointment['window_label']}, {item['machine_label']}"
            )
        tail = "" if len(schedule) <= 5 else f"; ещё {len(schedule) - 5}"
        return _completed_tool("answer_schedule", _safe_query_arguments(message), "Запланированные визиты: " + "; ".join(rows) + tail, refs)

    def _answer_technicians(self, message: str) -> dict[str, object]:
        profiles = self._list_technician_profiles.execute().items
        active_profiles = [profile for profile in profiles if profile.staff_active and profile.active]
        requested_brand = _requested_brand(message)
        refs = [
            {
                "label": profile.display_name,
                "target_type": "technician",
                "target_id": f"technician:{index + 1}",
                "href": "/admin",
            }
            for index, profile in enumerate(active_profiles[:10])
        ]
        if requested_brand:
            matching = [
                profile
                for profile in active_profiles
                if any(skill.casefold() == requested_brand.casefold() for skill in profile.skill_brands)
            ]
            if not matching:
                return _completed_tool(
                    "answer_technicians",
                    _safe_query_arguments(message),
                    f"Активных мастеров с навыком {requested_brand} не нашёл.",
                    refs,
                )
            names = ", ".join(profile.display_name for profile in matching)
            return _completed_tool("answer_technicians", _safe_query_arguments(message), f"{requested_brand} умеют: {names}.", refs)
        if _is_count_question(message):
            return _completed_tool(
                "answer_technicians",
                _safe_query_arguments(message),
                f"Всего мастеров: {len(profiles)}; активных: {len(active_profiles)}.",
                refs,
            )
        if not profiles:
            return _completed_tool("answer_technicians", _safe_query_arguments(message), "Мастера в staff-каталоге не найдены.", refs)
        names = "; ".join(
            f"{profile.display_name}"
            + (f" — навыки: {', '.join(profile.skill_brands)}" if profile.skill_brands else "")
            for profile in profiles[:8]
        )
        return _completed_tool("answer_technicians", _safe_query_arguments(message), f"Мастера: {names}.", refs)

    def _search_knowledge(self, query: str) -> dict[str, object]:
        retrieval = self._retrieve_knowledge.execute(KnowledgeRetrievalPayload(query=query, limit=3))
        relevant_results = [result for result in retrieval.results if _knowledge_result_relevant(query, result)]
        refs = [
            {
                "label": result.document_title,
                "target_type": "knowledge_source",
                "target_id": result.source_uri or str(result.chunk_id),
                "href": result.source_uri,
            }
            for result in relevant_results
        ]
        source_labels = ", ".join(ref["target_id"] for ref in refs[:3])
        if not relevant_results:
            return _completed_tool(
                "search_knowledge_base",
                _safe_query_arguments(query),
                f"В базе знаний не нашёл уверенного источника по вопросу «{_safe_staff_question(query)[:160]}». Не подставляю похожие сценарии, чтобы не дать нерелевантную инструкцию.",
                refs,
            )
        snippets = "; ".join(_knowledge_snippet(result.content) for result in relevant_results[:2])
        return _completed_tool(
            "search_knowledge_base",
            _safe_query_arguments(query),
            f"Нашёл {len(relevant_results)} источника в базе знаний. Коротко: {snippets}"
            + (f" Источники: {source_labels}" if source_labels else ""),
            refs,
        )

    def _check_part_stock(self, query: str) -> dict[str, object]:
        parts = self._list_parts.execute().items
        if _is_low_stock_question(query):
            selected = [part for part in parts if part.is_low_stock]
            refs = [
                {"label": part.sku, "target_type": "inventory_part", "target_id": str(part.part_id), "href": "/inventory"}
                for part in selected[:10]
            ]
            if not selected:
                return _completed_tool("check_part_stock", _safe_stock_arguments(query), "Низких складских остатков сейчас нет.", refs)
            summary = "; ".join(_stock_summary(part) for part in selected[:8])
            return _completed_tool("check_part_stock", _safe_stock_arguments(query), f"Нужно проверить закупку по {len(selected)} позициям: {summary}", refs)

        selected = _matching_inventory_parts(query, parts)
        refs = [
            {"label": part.sku, "target_type": "inventory_part", "target_id": str(part.part_id), "href": "/inventory"}
            for part in selected[:5]
        ]
        if not selected:
            return _completed_tool(
                "check_part_stock",
                _safe_stock_arguments(query),
                f"По складу не нашёл совпадений для «{_safe_inventory_query_label(query)}». Не подставляю другие позиции, чтобы не дать нерелевантный остаток.",
                refs,
            )
        total_available = sum(part.available_quantity for part in selected)
        summary = "; ".join(_stock_summary(part) for part in selected[:5])
        prefix = f"Найдено складских позиций: {len(selected)}; всего доступно: {total_available}. "
        return _completed_tool("check_part_stock", _safe_stock_arguments(query), prefix + summary, refs)

    def _recommend_technician(self, request_number: str) -> dict[str, object]:
        recommendations = self._recommend_technicians.execute(request_number)
        top = recommendations.items[:3]
        refs = [
            {
                "label": item.display_name,
                "target_type": "technician",
                "target_id": f"technician_recommendation:{index + 1}",
                "href": f"/dispatcher?request={request_number}",
            }
            for index, item in enumerate(top)
        ]
        summary = "; ".join(
            f"{item.display_name}: score={item.score}, reasons={', '.join(item.reasons[:3])}, risks={', '.join(item.risks[:3])}"
            for item in top
        )
        return _completed_tool("recommend_technician", {"request_number": request_number}, f"{request_number}: {summary}", refs)

    def _create_purchase_draft(self, arguments: dict[str, object]) -> dict[str, object]:
        supplier_id = int(arguments["supplier_id"])
        part_id = int(arguments["part_id"])
        quantity = int(arguments["quantity"])
        record = self._create_purchase_request.execute_payload(
            CreatePurchaseRequestPayload(
                supplier_id=supplier_id,
                items=[PurchaseRequestItemPayload(part_id=part_id, quantity=quantity)],
                note="Created by confirmed staff assistant tool",
            )
        )
        return _completed_tool(
            "create_purchase_request_draft",
            arguments,
            f"Draft purchase request {record.purchase_request_id} created for {record.supplier_name}.",
            [
                {
                    "label": f"Purchase request {record.purchase_request_id}",
                    "target_type": "purchase_request",
                    "target_id": str(record.purchase_request_id),
                    "href": "/procurement",
                }
            ],
            policy="requires_confirmation",
        )


def _deterministic_plan(message: str) -> dict[str, object]:
    lowered = message.casefold()
    request_number = _request_number(message)
    guarded_plan = _guardrail_plan(message)
    if guarded_plan is not None:
        return guarded_plan
    if "черновик закуп" in lowered or "purchase" in lowered:
        return {
            "tool_name": "create_purchase_request_draft",
            "policy": "requires_confirmation",
            "arguments": _purchase_arguments(message),
        }
    if "просроч" in lowered or "overdue" in lowered:
        return {"tool_name": "list_overdue_requests", "policy": "read_only", "arguments": {}}
    if _is_reporting_question(lowered):
        return {"tool_name": "generate_daily_report", "policy": "read_only", "arguments": {}}
    if _is_capabilities_question(lowered):
        return {"tool_name": "answer_capabilities", "policy": "read_only", "arguments": {}}
    if _is_staff_contact_question(lowered):
        return {"tool_name": "answer_staff_contacts", "policy": "read_only", "arguments": {"query": _query(message)}}
    if _is_procurement_question(lowered):
        return {"tool_name": "answer_procurement", "policy": "read_only", "arguments": {"query": _query(message)}}
    if "баз" in lowered or "knowledge" in lowered or "поищи" in lowered or "search" in lowered:
        return {"tool_name": "search_knowledge_base", "policy": "read_only", "arguments": {"query": _query(message)}}
    if "склад" in lowered or "stock" in lowered or "остат" in lowered or "резерв" in lowered or "reserved" in lowered:
        return {"tool_name": "check_part_stock", "policy": "read_only", "arguments": {"query": _query(message)}}
    if "техник" in lowered or "мастер" in lowered or "recommend" in lowered:
        return {
            "tool_name": "recommend_technician",
            "policy": "read_only",
            "arguments": {"request_number": request_number or ""},
        }
    if _is_service_catalog_question(lowered):
        return {"tool_name": "answer_service_catalog", "policy": "read_only", "arguments": {"query": _query(message)}}
    if request_number:
        return {"tool_name": "find_request", "policy": "read_only", "arguments": {"request_number": request_number}}
    return {"tool_name": "search_knowledge_base", "policy": "read_only", "arguments": {"query": _query(message)}}


def _assistant_intent(message: str) -> str:
    lowered = message.casefold()
    if "черновик закуп" in lowered or "purchase" in lowered:
        return "purchase_draft"
    if _is_capabilities_question(lowered):
        return "capabilities"
    if _is_staff_contact_question(lowered):
        return "staff_contacts"
    if _is_procurement_question(lowered):
        return "procurement"
    if _request_ordinal_position(message) is not None and _mentions_request(message):
        return "request_lookup"
    if _request_number(message):
        if _is_recommendation_question(message):
            return "recommend_technician"
        return "request_lookup"
    if "просроч" in lowered or "overdue" in lowered:
        return "overdue_requests"
    if _mentions_schedule(lowered):
        return "schedule"
    if _mentions_technicians(lowered):
        return "technicians"
    if _is_service_catalog_question(lowered):
        return "service_catalog"
    if _mentions_request(message) or _is_reporting_question(lowered):
        return "requests"
    if _mentions_inventory(lowered):
        return "inventory"
    return "knowledge"


def _database_query_spec(message: str) -> dict[str, object] | None:
    plan = _structured_query_plan(message)
    if plan is None:
        return None
    if plan.domain == "requests":
        spec = {
            "domain": "requests",
            "entity": "service_requests",
            "metric": plan.metric,
            "question_type": plan.question_type,
            "required_facets": ["entity", "metric"],
        }
        if plan.date_range is not None:
            spec["start_date"] = plan.date_range.start.isoformat()
            spec["end_date"] = plan.date_range.end.isoformat()
            spec["date_label"] = plan.date_range.label
            spec["required_facets"].append("date_range")  # type: ignore[union-attr]
        if plan.date is not None:
            spec["date"] = plan.date.isoformat()
            spec["required_facets"].append("date")  # type: ignore[union-attr]
        if plan.status:
            spec["status"] = plan.status
            spec["status_label"] = plan.status_label
            spec["statuses"] = _request_status_group(plan.status)
            spec["required_facets"].append("status")  # type: ignore[union-attr]
        return spec
    if plan.domain == "appointments":
        spec = {
            "domain": "appointments",
            "entity": "request_appointments",
            "metric": plan.metric,
            "question_type": plan.question_type,
            "required_facets": ["entity", "metric"],
        }
        if plan.date is not None:
            spec["date"] = plan.date.isoformat()
            spec["date_label"] = _ru_date_label(plan.date.isoformat())
            spec["required_facets"].append("date")  # type: ignore[union-attr]
        if plan.date_range is not None:
            spec["start_date"] = plan.date_range.start.isoformat()
            spec["end_date"] = plan.date_range.end.isoformat()
            spec["date_label"] = plan.date_range.label
            spec["required_facets"].append("date_range")  # type: ignore[union-attr]
        if plan.status:
            spec["status"] = plan.status
            spec["status_label"] = plan.status_label
        return spec
    if plan.domain == "staff":
        return {
            "domain": "staff",
            "entity": "staff_accounts",
            "metric": plan.metric,
            "question_type": plan.question_type,
            "required_facets": ["entity", "metric"],
        }
    if plan.domain == "suppliers":
        return {
            "domain": "suppliers",
            "entity": "procurement_suppliers",
            "metric": "count" if _is_count_question(message) and not _is_list_question(message) else "list",
            "question_type": "count" if _is_count_question(message) and not _is_list_question(message) else "list",
            "required_facets": ["entity", "metric"],
        }
    if plan.domain == "inventory":
        metric = plan.metric or "reserved_total"
        entity = "inventory_parts" if metric == "parts_count" else "part_reservations"
        return {
            "domain": "inventory",
            "entity": entity,
            "metric": metric,
            "question_type": plan.question_type,
            "required_facets": ["entity", "metric"],
        }
    if plan.domain == "technicians":
        return {
            "domain": "technicians",
            "entity": "technician_profiles",
            "metric": "service_regions",
            "question_type": "list",
            "required_facets": ["entity", "metric"],
        }
    return None


def _structured_query_plan(message: str) -> AssistantQueryPlan | None:
    lowered = message.casefold()
    question_type = "count" if _is_count_question(message) and not _is_list_question(message) else "list"
    request_date_range = _extract_date_range(message)
    request_date = _extract_russian_date(message)
    if _mentions_request(message) and (request_date_range is not None or request_date is not None):
        status, label = _request_status_filter(lowered)
        return AssistantQueryPlan(
            domain="requests",
            entity="service_requests",
            metric="count",
            question_type=question_type,
            date=request_date,
            date_range=request_date_range,
            status=status,
            status_label=label,
        )
    if _mentions_schedule(lowered) and _is_completed_visit_question(lowered):
        return AssistantQueryPlan(
            domain="appointments",
            entity="request_appointments",
            metric="completed_visits",
            question_type=question_type,
            date=request_date,
            date_range=request_date_range,
            status="completed",
            status_label="Выполненные визиты",
        )
    if _mentions_staff_accounts(lowered):
        return AssistantQueryPlan(
            domain="staff",
            entity="staff_accounts",
            metric="count" if question_type == "count" else "list",
            question_type=question_type,
        )
    if _mentions_supplier(lowered):
        return AssistantQueryPlan(
            domain="suppliers",
            entity="procurement_suppliers",
            metric="count" if question_type == "count" else "list",
            question_type=question_type,
        )
    if _mentions_inventory(lowered) and _mentions_reservation(lowered):
        return AssistantQueryPlan(
            domain="inventory",
            entity="part_reservations",
            metric="reserved_total",
            question_type="sum",
        )
    if _is_inventory_positions_question(lowered):
        return AssistantQueryPlan(
            domain="inventory",
            entity="inventory_parts",
            metric="parts_count",
            question_type="count",
        )
    if _mentions_technicians(lowered) and _mentions_region_coverage(lowered):
        return AssistantQueryPlan(
            domain="technicians",
            entity="technician_profiles",
            metric="service_regions",
            question_type="list",
        )
    return None


def _intent_from_planned_tool(plan: dict[str, object], fallback: str) -> str:
    tool_name = str(plan.get("tool_name") or "")
    mapping = {
        "find_request": "request_lookup",
        "list_overdue_requests": "overdue_requests",
        "search_knowledge_base": "knowledge",
        "check_part_stock": "inventory",
        "recommend_technician": "recommend_technician",
        "generate_daily_report": "requests",
        "answer_requests": "requests",
        "answer_schedule": "schedule",
        "answer_technicians": "technicians",
        "answer_database_query": "database_query",
        "answer_capabilities": "capabilities",
        "answer_service_catalog": "service_catalog",
        "answer_staff_contacts": "staff_contacts",
        "answer_procurement": "procurement",
        "create_purchase_request_draft": "purchase_draft",
    }
    return mapping.get(tool_name, fallback)


def _assistant_answer_message(status: str, tool_name: str, result_summary: str = "") -> str:
    if status == "confirmation_required":
        return f"{tool_name} требует подтверждения сотрудника перед изменением данных ServiceOps."
    if status == "failed":
        return "Помощник не смог обработать запрос."
    return result_summary or f"{tool_name} completed."


def _self_check_tool(message: str, intent: str, tool_call: dict[str, object]) -> dict[str, object]:
    tool_name = str(tool_call["tool_name"])
    summary = str(tool_call.get("result_summary") or "")
    failures: list[str] = []
    if not summary.strip():
        failures.append("empty_answer")
    expected_tools = {
        "request_lookup": {"find_request"},
        "recommend_technician": {"recommend_technician"},
        "overdue_requests": {"list_overdue_requests"},
        "requests": {"answer_requests", "generate_daily_report"},
        "schedule": {"answer_schedule"},
        "technicians": {"answer_technicians"},
        "inventory": {"check_part_stock"},
        "knowledge": {"search_knowledge_base"},
        "database_query": {"answer_database_query"},
        "capabilities": {"answer_capabilities"},
        "service_catalog": {"answer_service_catalog"},
        "staff_contacts": {"answer_staff_contacts"},
        "procurement": {"answer_procurement"},
    }
    if intent in expected_tools and tool_name not in expected_tools[intent]:
        failures.append(f"tool_mismatch:{intent}->{tool_name}")
    lowered = message.casefold()
    if _is_capabilities_question(lowered) and tool_name != "answer_capabilities":
        failures.append("capabilities_question_not_answered_from_capabilities")
    if _is_staff_contact_question(lowered) and tool_name != "answer_staff_contacts":
        failures.append("contact_question_not_answered_from_contact_policy")
    if _is_procurement_question(lowered):
        procurement_status = _procurement_status_filter(message)
        arguments = dict(tool_call.get("arguments") or {})
        if tool_name != "answer_procurement":
            failures.append("procurement_question_not_answered_from_procurement")
        if procurement_status and arguments.get("status") != procurement_status:
            failures.append("procurement_status_filter_missing")
    if _is_service_catalog_question(lowered) and not _mentions_technicians(lowered) and tool_name != "answer_service_catalog":
        failures.append("service_question_not_answered_from_service_catalog")
    if _mentions_technicians(lowered) and tool_name not in {"answer_technicians", "recommend_technician", "answer_database_query", "answer_staff_contacts", "answer_schedule"}:
        failures.append("technician_question_routed_to_wrong_domain")
    if _mentions_schedule(lowered) and _is_completed_visit_question(lowered):
        arguments = dict(tool_call.get("arguments") or {})
        if tool_name != "answer_database_query" or arguments.get("metric") != "completed_visits":
            failures.append("completed_visit_question_without_completed_visit_metric")
    elif _mentions_schedule(lowered) and tool_name != "answer_schedule":
        failures.append("schedule_question_not_answered_from_schedule")
    if (_extract_russian_date(message) or _extract_date_range(message)) and _mentions_request(message):
        arguments = dict(tool_call.get("arguments") or {})
        if tool_name != "answer_database_query" or not (arguments.get("date") or arguments.get("start_date")):
            failures.append("date_filtered_request_question_without_date_query")
        request_status, _ = _request_status_filter(lowered)
        if request_status and arguments.get("status") != request_status:
            failures.append("date_filtered_request_question_without_status_filter")
    if _mentions_staff_accounts(lowered):
        arguments = dict(tool_call.get("arguments") or {})
        if tool_name != "answer_database_query" or arguments.get("domain") != "staff":
            failures.append("staff_question_not_answered_from_staff_accounts")
    if _mentions_supplier(lowered) and tool_name != "answer_database_query":
        failures.append("supplier_question_not_answered_from_database")
    if _mentions_inventory(lowered) and _mentions_reservation(lowered):
        arguments = dict(tool_call.get("arguments") or {})
        if tool_name != "answer_database_query" or arguments.get("metric") != "reserved_total":
            failures.append("reservation_question_not_answered_from_reservations")
    if _is_inventory_positions_question(lowered):
        arguments = dict(tool_call.get("arguments") or {})
        if tool_name != "answer_database_query" or arguments.get("metric") != "parts_count":
            failures.append("inventory_positions_question_not_answered_from_inventory_parts")
    if _mentions_technicians(lowered) and _mentions_region_coverage(lowered):
        arguments = dict(tool_call.get("arguments") or {})
        if tool_name != "answer_database_query" or arguments.get("metric") != "service_regions":
            failures.append("technician_region_question_without_regions")
    if intent == "inventory" and _mentions_inventory(lowered) and tool_name != "check_part_stock":
        failures.append("inventory_question_not_answered_from_inventory")
    if tool_name == "check_part_stock" and "По складу не нашёл совпадений" not in summary and not tool_call.get("result_refs"):
        failures.append("inventory_answer_without_matches_or_not_found")
    if tool_name == "check_part_stock" and "По складу не нашёл совпадений" not in summary and not _is_low_stock_question(message):
        terms = [term for term in _inventory_terms(message) if term not in {"сколько", "складе"}]
        if terms and not any(term in summary.casefold() for term in terms):
            failures.append("inventory_answer_missing_requested_entity")
    if tool_name == "search_knowledge_base" and summary.startswith("Knowledge results"):
        failures.append("knowledge_answer_is_raw_tool_summary")
    if (
        tool_name == "search_knowledge_base"
        and "не нашёл подходящих источников" not in summary
        and "не нашёл уверенного источника" not in summary
        and not tool_call.get("result_refs")
    ):
        failures.append("knowledge_answer_without_sources")
    request_number = _request_number(message)
    if request_number and tool_name in {"find_request", "recommend_technician"} and request_number not in summary:
        failures.append("request_number_missing_from_answer")
    if _contains_unredacted_sensitive_text(json.dumps(tool_call, ensure_ascii=False)):
        failures.append("privacy_leakage_detected")

    if failures:
        return _completed_tool(
            "assistant_self_check",
            {"intent": intent, "passed": False},
            "Самопроверка не пройдена: " + ", ".join(failures),
            [],
        ) | {"status": "failed"}
    return _completed_tool(
        "assistant_self_check",
        {"intent": intent, "passed": True},
        f"Самопроверка пройдена: вопрос относится к домену {intent}, ответ взят из {tool_name}.",
        [],
    )


def _is_capabilities_question(lowered_message: str) -> bool:
    return any(
        marker in lowered_message
        for marker in (
            "что ты умеешь",
            "что умеешь",
            "функционал",
            "чем ты можешь",
            "возможност",
            "как ты можешь помочь",
            "help",
            "capabilit",
        )
    )


def _is_staff_contact_question(lowered_message: str) -> bool:
    return any(marker in lowered_message for marker in ("телефон", "номер", "контакт", "phone", "contact")) and any(
        marker in lowered_message for marker in ("мастер", "техник", "сотрудник", "staff", "technician")
    )


def _mentions_staff_accounts(lowered_message: str) -> bool:
    if not any(marker in lowered_message for marker in ("сотрудник", "персонал", "staff", "employee", "работник")):
        return False
    return any(marker in lowered_message for marker in ("сколько", "число", "количество", "перечисл", "список", "кто", "company", "компани"))


def _is_procurement_question(lowered_message: str) -> bool:
    procurement_markers = ("закуп", "поставка", "поставк", "purchase request", "procurement")
    low_stock_markers = ("докупить", "низк", "не хватает", "low stock", "low-stock")
    if not any(marker in lowered_message for marker in procurement_markers):
        return False
    return any(
        marker in lowered_message
        for marker in ("заверш", "получ", "заказ", "статус", "последн", "дней", "список", "какие", "сколько", "received")
    ) and not any(marker in lowered_message for marker in low_stock_markers)


def _is_completed_procurement_question(message: str) -> bool:
    lowered = message.casefold()
    return any(marker in lowered for marker in ("заверш", "получ", "received", "completed", "done"))


def _procurement_status_filter(message: str) -> str:
    lowered = message.casefold()
    if any(marker in lowered for marker in ("согласован", "согласовании", "на соглас", "pending approval", "pending_approval")):
        return "pending_approval"
    if any(marker in lowered for marker in ("одобрен", "approved")):
        return "approved"
    if any(marker in lowered for marker in ("заказан", "ordered")):
        return "ordered"
    if any(marker in lowered for marker in ("отмен", "cancelled", "canceled")):
        return "cancelled"
    if _is_completed_procurement_question(message):
        return "received"
    return ""


def _procurement_status_label(status: str) -> str:
    return {
        "pending_approval": "на согласовании",
        "approved": "одобренные",
        "ordered": "заказанные",
        "received": "полученные",
        "cancelled": "отмененные",
    }.get(status, "")


def _request_status_filter(lowered_message: str) -> tuple[str, str]:
    if any(marker in lowered_message for marker in ("заверш", "закрыт", "completed", "closed")):
        return "completed", "Завершенные заявки"
    if any(marker in lowered_message for marker in ("нов", "создан", "created", "new")):
        return "new", "Новые заявки"
    if any(marker in lowered_message for marker in ("ожида", "запчаст", "waiting_for_parts")):
        return "waiting_for_parts", "Заявки в ожидании запчастей"
    if any(marker in lowered_message for marker in ("работ", "процесс", "repair_in_progress", "diagnostics")):
        return "repair_in_progress", "Заявки в работе"
    if any(marker in lowered_message for marker in ("заплан", "визит", "visit_scheduled")):
        return "visit_scheduled", "Заявки с запланированным визитом"
    if any(marker in lowered_message for marker in ("отмен", "cancelled", "canceled")):
        return "cancelled", "Отмененные заявки"
    return "", ""


def _request_status_group(status: str) -> list[str]:
    groups = {
        "completed": ["completed", "closed"],
        "repair_in_progress": ["diagnostics", "repair_in_progress", "technician_assigned", "visit_scheduled", "waiting_for_parts"],
    }
    return groups.get(status, [status] if status else [])


def _is_completed_visit_question(lowered_message: str) -> bool:
    return any(marker in lowered_message for marker in ("выполн", "заверш", "проведен", "проведён", "completed", "done"))


def _is_service_catalog_question(lowered_message: str) -> bool:
    if any(marker in lowered_message for marker in ("услуг", "сайт", "сервис", "service catalog")):
        return True
    if any(marker in lowered_message for marker in ("ремонтируем", "обслуживаем", "чин", "repair")) and any(
        marker in lowered_message for marker in ("кофемаш", "бренд", "brand", "jura", "saeco", "delong", "капибар")
    ):
        return True
    return False


def _requested_service_brand(message: str, known_brands: list[str]) -> str | None:
    known = _requested_brand(message)
    if known:
        return known
    quoted = re.search(r"[\"«“]([^\"»”]{2,60})[\"»”]", message)
    if quoted:
        return quoted.group(1).strip()
    lowered = message.casefold()
    for brand in known_brands:
        if brand.casefold() in lowered:
            return brand
    match = re.search(r"(?:ремонтируем|обслуживаем|чин(?:им|ите)?|repair)\s+(?:кофемашины?\s+)?([a-zа-яё0-9-]{3,40})", lowered)
    if match:
        candidate = match.group(1).strip(" ?.,!")
        if candidate not in {"кофемаш", "кофемашина", "кофемашины", "машины"}:
            return candidate
    return None


def _service_regions_from_profiles(profiles: object) -> list[str]:
    regions: list[str] = []
    for profile in profiles:  # type: ignore[assignment]
        if not getattr(profile, "staff_active", False) or not getattr(profile, "active", False):
            continue
        regions.extend(region.strip() for region in getattr(profile, "service_regions", []) if str(region).strip())
    return _unique_preserving_order(regions)


def _extract_date_range(message: str) -> AssistantDateRange | None:
    lowered = message.casefold()
    today = date.today()
    if "сегодня" in lowered or "today" in lowered:
        return AssistantDateRange(today, today, _ru_date_label(today.isoformat()))
    if "вчера" in lowered or "yesterday" in lowered:
        yesterday = today - timedelta(days=1)
        return AssistantDateRange(yesterday, yesterday, _ru_date_label(yesterday.isoformat()))
    match = re.search(r"(?:последн\w*|last)\s+(\d{1,3})\s+(?:дн|day)", lowered)
    if match:
        days = max(1, min(365, int(match.group(1))))
        return AssistantDateRange(today - timedelta(days=days - 1), today, f"за последние {days} дней")
    if "за неделю" in lowered or "последнюю неделю" in lowered or "last week" in lowered:
        return AssistantDateRange(today - timedelta(days=6), today, "за последние 7 дней")
    return None


def _date_in_range(row_date: str, date_range: AssistantDateRange) -> bool:
    if not row_date:
        return False
    return date_range.start.isoformat() <= row_date <= date_range.end.isoformat()


def _mentions_request(message: str) -> bool:
    lowered = message.casefold()
    return "заяв" in lowered or "request" in lowered or bool(_request_number(message))


def _mentions_schedule(lowered_message: str) -> bool:
    return any(marker in lowered_message for marker in ("визит", "распис", "заплан", "appointment", "schedule", "окн"))


def _mentions_technicians(lowered_message: str) -> bool:
    if any(marker in lowered_message for marker in ("мастер", "техник", "technician", "инженер", "специалист")):
        return True
    return "уме" in lowered_message and any(marker in lowered_message for marker in ("кто", "бренд", "jura", "saeco", "delonghi"))


def _mentions_inventory(lowered_message: str) -> bool:
    if _mentions_reservation(lowered_message):
        return True
    inventory_markers = (
        "склад",
        "остат",
        "запчаст",
        "детал",
        "таблет",
        "фильтр",
        "насос",
        "клапан",
        "проклад",
        "жиклер",
        "датчик",
        "кофемол",
        "stock",
        "part",
        "inventory",
        "flow-meter",
    )
    if any(marker in lowered_message for marker in inventory_markers):
        return True
    return _is_low_stock_question(lowered_message)


def _is_inventory_positions_question(lowered_message: str) -> bool:
    if not _is_count_question(lowered_message):
        return False
    if not any(marker in lowered_message for marker in ("склад", "stock", "inventory")):
        return False
    return any(marker in lowered_message for marker in ("позици", "номенклатур", "sku", "артикул"))


def _mentions_supplier(lowered_message: str) -> bool:
    return any(marker in lowered_message for marker in ("поставщик", "supplier", "vendor", "закупочн"))


def _mentions_reservation(lowered_message: str) -> bool:
    return any(marker in lowered_message for marker in ("резерв", "зарезерв", "reservation", "reserved"))


def _mentions_region_coverage(lowered_message: str) -> bool:
    return any(marker in lowered_message for marker in ("район", "регион", "зон", "покрыва", "обслужива", "coverage", "region"))


def _is_count_question(message: str) -> bool:
    lowered = message.casefold()
    return any(marker in lowered for marker in ("сколько", "число", "количество", "count", "how many"))


def _is_list_question(message: str) -> bool:
    lowered = message.casefold()
    return any(marker in lowered for marker in ("перечисл", "список", "покажи", "какие", "кто", "list", "show"))


def _is_recommendation_question(message: str) -> bool:
    lowered = message.casefold()
    return any(marker in lowered for marker in ("порекоменду", "подбери", "назначить", "recommend", "лучший мастер"))


def _requested_brand(message: str) -> str | None:
    known_brands = ("Jura", "La Marzocco", "Nuova Simonelli", "Saeco", "DeLonghi", "Eversys", "Franke", "WMF", "Rancilio")
    lowered = message.casefold()
    for brand in known_brands:
        if brand.casefold() in lowered:
            return brand
    return None


def _is_low_stock_question(message: str) -> bool:
    lowered = message.casefold()
    return any(marker in lowered for marker in ("докупить", "закуп", "низк", "не хватает", "low stock", "low-stock"))


def _matching_inventory_parts(query: str, parts: list[InventoryPartItem]) -> list[InventoryPartItem]:
    terms = _inventory_terms(query)
    if not terms:
        return []
    scored: list[tuple[int, str, InventoryPartItem]] = []
    for part in parts:
        haystacks = _part_search_texts(part)
        score = 0
        for term in terms:
            if any(term in text for text in haystacks):
                score += 2 if term in {part.sku.casefold(), str(part.brand or "").casefold()} else 1
        if score > 0:
            scored.append((score, part.sku, part))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [part for _, _, part in scored]


def _inventory_terms(query: str) -> list[str]:
    lowered = query.casefold()
    synonyms: list[str] = []
    if "очист" in lowered or "таблет" in lowered:
        synonyms.extend(["таблет", "очист", "clean", "cleaning", "tablet", "descaling"])
    if "jura" in lowered:
        synonyms.append("jura")
    if "делонг" in lowered or "delong" in lowered or "delongi" in lowered:
        synonyms.extend(["delonghi", "delongi", "делонг", "делонги"])
    if "фильтр" in lowered:
        synonyms.extend(["фильтр", "filter"])
    if "насос" in lowered or "помп" in lowered:
        synonyms.extend(["насос", "помп", "pump"])
    if "клапан" in lowered:
        synonyms.extend(["клапан", "valve"])
    if "проклад" in lowered or "уплотн" in lowered:
        synonyms.extend(["проклад", "уплотн", "gasket", "seal"])
    stopwords = {
        "сколько",
        "всего",
        "есть",
        "на",
        "у",
        "нас",
        "складе",
        "склад",
        "остаток",
        "остатки",
        "запчастей",
        "запчасти",
        "деталей",
        "детали",
        "для",
        "по",
        "проверь",
        "покажи",
        "available",
        "stock",
        "parts",
        "part",
    }
    raw_terms = [term.strip("-_.,:;!?()[]«»\"'") for term in re.split(r"\s+", lowered)]
    terms = [term for term in raw_terms + synonyms if len(term) >= 3 and term not in stopwords]
    seen: set[str] = set()
    unique: list[str] = []
    for term in terms:
        if term in seen:
            continue
        seen.add(term)
        unique.append(term)
    return unique[:12]


def _part_search_texts(part: InventoryPartItem) -> list[str]:
    values: list[str] = [
        part.sku,
        part.name,
        part.brand or "",
        part.model or "",
        part.compatibility_note or "",
        part.part_type or "",
        part.parameter_label or "",
        part.parameter_value or "",
        part.parameter_unit or "",
    ]
    for compatibility in part.compatibility:
        values.extend(
            [
                compatibility.brand or "",
                compatibility.model or "",
                compatibility.series or "",
                compatibility.machine_family or "",
                compatibility.note or "",
            ]
        )
    return [value.casefold() for value in values if value]


def _stock_summary(part: InventoryPartItem) -> str:
    return f"{part.sku} ({part.name}): доступно={part.available_quantity}, резерв={part.reserved_quantity}, на складе={part.quantity_on_hand}"


def _safe_inventory_query_label(query: str) -> str:
    return _safe_staff_question(query)[:120]


def _knowledge_snippet(content: str) -> str:
    cleaned = re.sub(r"\s+", " ", content).strip()
    if not cleaned:
        return "источник без короткого текста"
    sentence = re.split(r"(?<=[.!?])\s+", cleaned, maxsplit=1)[0]
    return sentence[:260]


def _knowledge_result_relevant(query: str, result: object) -> bool:
    query_terms = _knowledge_terms(query)
    if not query_terms:
        return False
    content = " ".join(
        str(getattr(result, field, "") or "")
        for field in ("document_title", "source_uri", "content")
    )
    content_terms = _knowledge_terms(content)
    if not content_terms:
        return False
    generic_terms = {
        "кофемашина",
        "кофемашины",
        "кофейный",
        "оборудование",
        "машина",
        "ремонт",
        "coffee",
        "machine",
        "repair",
        "что",
        "как",
        "если",
        "проверить",
        "проверьте",
        "проверка",
        "делать",
    }
    informative_terms = query_terms - generic_terms
    if not informative_terms:
        return False
    matches = informative_terms & content_terms
    if not matches:
        return False
    diagnostic_terms = informative_terms - {
        "jura",
        "saeco",
        "delonghi",
        "delongi",
        "delong",
        "marzocco",
        "simonelli",
        "rancilio",
        "wmf",
        "e61",
    }
    if diagnostic_terms:
        return bool(matches & diagnostic_terms)
    return len(matches) >= 1


def _knowledge_terms(value: str) -> set[str]:
    stopwords = {
        "что",
        "как",
        "если",
        "для",
        "при",
        "или",
        "это",
        "the",
        "and",
        "for",
        "with",
        "from",
        "после",
        "перед",
        "нужно",
        "может",
    }
    return {term for term in re.findall(r"[\wа-яА-ЯёЁ-]+", value.casefold()) if len(term) >= 3 and term not in stopwords}


def _completed_tool(
    tool_name: str,
    arguments: dict[str, object],
    result_summary: str,
    result_refs: list[dict[str, object]],
    policy: str = "read_only",
) -> dict[str, object]:
    return {
        "tool_name": tool_name,
        "policy": policy,
        "status": "completed",
        "arguments": arguments,
        "result_summary": safe_assistant_text(result_summary)[:2000],
        "result_refs": _safe_result_refs(result_refs),
    }


def _safe_result_refs(result_refs: list[dict[str, object]]) -> list[dict[str, object]]:
    safe_refs: list[dict[str, object]] = []
    for ref in result_refs:
        href = ref.get("href")
        safe_refs.append(
            {
                "label": safe_assistant_text(str(ref.get("label") or ""))[:180],
                "target_type": safe_assistant_text(str(ref.get("target_type") or ""))[:80],
                "target_id": safe_assistant_text(str(ref.get("target_id") or ""))[:180],
                "href": None if href is None else safe_assistant_text(str(href))[:300],
            }
        )
    return safe_refs


def _validate_planner_output(parsed: object, original_message: str) -> dict[str, object]:
    guarded_plan = _guardrail_plan(original_message)
    if guarded_plan is not None:
        return guarded_plan
    if not isinstance(parsed, dict):
        raise ValueError("Assistant planner output must be an object")
    tool_name = str(parsed.get("tool_name") or "").strip()
    if tool_name not in TOOL_POLICIES:
        raise ValueError("Assistant planner selected unsupported tool")
    arguments = parsed.get("arguments")
    if not isinstance(arguments, dict):
        arguments = {}
    cleaned_arguments = _validated_arguments(tool_name, arguments, original_message)
    return {"tool_name": tool_name, "policy": TOOL_POLICIES[tool_name], "arguments": cleaned_arguments}


def _validated_arguments(tool_name: str, arguments: dict[object, object], original_message: str) -> dict[str, object]:
    if tool_name == "find_request":
        request_number = _request_number(str(arguments.get("request_number") or "")) or _request_number(original_message)
        ordinal_position = _request_ordinal_position(arguments.get("ordinal_position")) or _request_ordinal_position(original_message)
        if ordinal_position is not None and not request_number:
            return {"ordinal_position": ordinal_position}
        if not request_number:
            raise ValueError("find_request requires a request number")
        return {"request_number": request_number}
    if tool_name == "recommend_technician":
        request_number = _request_number(str(arguments.get("request_number") or "")) or _request_number(original_message)
        if not request_number:
            raise ValueError("recommend_technician requires a request number")
        return {"request_number": request_number}
    if tool_name == "search_knowledge_base":
        return {"query": str(arguments.get("query") or original_message).strip() or original_message}
    if tool_name == "check_part_stock":
        return {"query": str(arguments.get("query") or original_message).strip() or original_message}
    if tool_name in {"answer_service_catalog", "answer_staff_contacts", "answer_procurement"}:
        return {"query": str(arguments.get("query") or original_message).strip() or original_message}
    if tool_name == "answer_capabilities":
        return {}
    if tool_name == "create_purchase_request_draft":
        return {
            "supplier_id": _coerce_explicit_int(arguments.get("supplier_id"), "supplier", original_message),
            "part_id": _coerce_explicit_int(arguments.get("part_id"), "part", original_message),
            "quantity": _coerce_explicit_int(arguments.get("quantity"), "qty|quantity", original_message),
        }
    return {}


def _coerce_explicit_int(value: object, marker_pattern: str, original_message: str) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return _extract_int(original_message, rf"(?:{marker_pattern})\s+(\d+)")


def _request_number(message: str) -> str | None:
    match = REQUEST_NUMBER_PATTERN.search(message)
    return match.group(0).upper() if match else None


def _guardrail_plan(message: str) -> dict[str, object] | None:
    ordinal_position = _request_ordinal_position(message)
    if ordinal_position is None:
        return None
    lowered = message.casefold()
    if "заяв" not in lowered and "request" not in lowered:
        return None
    if not any(marker in lowered for marker in ("найди", "найти", "покажи", "открой", "find", "show", "lookup")):
        return None
    return {"tool_name": "find_request", "policy": "read_only", "arguments": {"ordinal_position": ordinal_position}}


def _request_ordinal_position(value: object) -> int | None:
    if isinstance(value, int) and value > 0:
        return value
    message = str(value).casefold()
    digit_match = re.search(r"\b(\d{1,2})(?:\s*[-]?\s*(?:ю|ую|ая|ой|й))?\s+(?:заяв|request)", message)
    if digit_match:
        return int(digit_match.group(1))
    ordinal_words = {
        "перв": 1,
        "втор": 2,
        "трет": 3,
        "четверт": 4,
        "пят": 5,
        "шест": 6,
        "седьм": 7,
        "восьм": 8,
        "девят": 9,
        "десят": 10,
    }
    for stem, position in ordinal_words.items():
        if re.search(rf"\b{stem}\w*\s+(?:заяв|request)", message):
            return position
    if re.search(r"\b(?:последн|latest|last)\w*\s+(?:заяв|request)", message):
        return 1
    return None


def _query(message: str) -> str:
    cleaned = REQUEST_NUMBER_PATTERN.sub("", message)
    for marker in ("Поищи в базе знаний", "Проверь склад", "search", "stock"):
        cleaned = cleaned.replace(marker, "")
    return cleaned.strip() or message.strip()


def _is_reporting_question(lowered_message: str) -> bool:
    return (
        "дневн" in lowered_message
        or "отчет" in lowered_message
        or "report" in lowered_message
        or ("сколько" in lowered_message and "заяв" in lowered_message)
        or ("всего" in lowered_message and "заяв" in lowered_message)
        or ("получено" in lowered_message and "заяв" in lowered_message)
        or "total requests" in lowered_message
        or "all requests" in lowered_message
    )


def _extract_russian_date(message: str) -> date | None:
    lowered = message.casefold()
    month_numbers = {
        "январ": 1,
        "феврал": 2,
        "март": 3,
        "апрел": 4,
        "ма": 5,
        "июн": 6,
        "июл": 7,
        "август": 8,
        "сентябр": 9,
        "октябр": 10,
        "ноябр": 11,
        "декабр": 12,
    }
    for stem, month in month_numbers.items():
        match = re.search(rf"\b(\d{{1,2}})\s+{stem}\w*(?:\s+(\d{{4}}))?\b", lowered)
        if not match:
            continue
        day = int(match.group(1))
        year = int(match.group(2)) if match.group(2) else 2026
        try:
            return date(year, month, day)
        except ValueError:
            return None
    iso_match = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", lowered)
    if iso_match:
        try:
            return date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
        except ValueError:
            return None
    return None


def _row_date(value: object) -> str:
    raw = str(value or "")
    if not raw:
        return ""
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return raw[:10]


def _ru_date_label(iso_date: str) -> str:
    if not iso_date:
        return "За весь период"
    month_names = {
        1: "января",
        2: "февраля",
        3: "марта",
        4: "апреля",
        5: "мая",
        6: "июня",
        7: "июля",
        8: "августа",
        9: "сентября",
        10: "октября",
        11: "ноября",
        12: "декабря",
    }
    try:
        parsed = date.fromisoformat(iso_date)
    except ValueError:
        return iso_date
    return f"{parsed.day} {month_names[parsed.month]} {parsed.year}"


def _request_rows_for_analysis(repository: AssistantRequestReader, *, include_timeline: bool = False) -> list[dict[str, object]]:
    owner_rows = getattr(repository, "list_owner_dashboard_requests", None)
    if callable(owner_rows) and not include_timeline:
        return [dict(row) for row in owner_rows()]
    rows = [dict(row) for row in repository.list_dispatcher_requests()]
    if not include_timeline:
        return rows
    detailed_rows: list[dict[str, object]] = []
    for row in rows:
        request_number = str(row.get("request_number") or "")
        if not request_number:
            detailed_rows.append(row)
            continue
        try:
            detail = dict(repository.get_dispatcher_request(request_number))
        except Exception:
            detailed_rows.append(row)
            continue
        merged = dict(row)
        merged["timeline"] = detail.get("timeline") if isinstance(detail.get("timeline"), list) else []
        detailed_rows.append(merged)
    return detailed_rows


def _request_row_has_status(row: dict[str, object], statuses: list[str]) -> bool:
    if not statuses:
        return True
    current_status = str(row.get("status") or "")
    if current_status in statuses:
        return True
    return any(str(event.get("status") or "") in statuses for event in _request_row_events(row))


def _request_row_matches_query_dates(row: dict[str, object], statuses: list[str], target_date: str, start_date: str, end_date: str) -> bool:
    if not target_date and not start_date and not end_date:
        return True
    if statuses and statuses != ["new"]:
        event_dates = [_row_date(event.get("created_at")) for event in _request_row_events(row) if str(event.get("status") or "") in statuses]
        return any(_date_matches_bounds(event_date, target_date, start_date, end_date) for event_date in event_dates)
    return _date_matches_bounds(_row_date(row.get("created_at")), target_date, start_date, end_date)


def _request_row_events(row: dict[str, object]) -> list[dict[str, object]]:
    timeline = row.get("timeline")
    if not isinstance(timeline, list):
        return []
    return [dict(event) for event in timeline if isinstance(event, dict)]


def _date_matches_bounds(row_date: str, target_date: str, start_date: str, end_date: str) -> bool:
    if not row_date:
        return False
    return (not target_date or row_date == target_date) and (not start_date or row_date >= start_date) and (not end_date or row_date <= end_date)


def _reserved_units(reservations: list[object], parts: list[InventoryPartItem]) -> dict[str, int]:
    units_by_part_id = {part.part_id: part.unit for part in parts}
    totals: dict[str, int] = {}
    for reservation in reservations:
        part_id = int(getattr(reservation, "part_id"))
        unit = units_by_part_id.get(part_id) or "pcs"
        totals[unit] = totals.get(unit, 0) + int(getattr(reservation, "quantity"))
    return totals


def _unique_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def _safe_database_query_arguments(query_spec: dict[str, object]) -> dict[str, object]:
    allowed_keys = {
        "domain",
        "entity",
        "metric",
        "date",
        "start_date",
        "end_date",
        "date_label",
        "status",
        "statuses",
        "status_label",
        "question_type",
        "required_facets",
    }
    return {key: value for key, value in query_spec.items() if key in allowed_keys}


def _safe_query_arguments(query: str) -> dict[str, object]:
    request_numbers = sorted({match.group(0).upper() for match in REQUEST_NUMBER_PATTERN.finditer(query)})
    return {"query_summary": "free_text", "request_numbers": request_numbers[:5]}


def _safe_stock_arguments(query: str) -> dict[str, object]:
    _ = query
    return {"query_summary": "stock_lookup"}


def _purchase_arguments(message: str) -> dict[str, object]:
    supplier = _extract_int(message, r"supplier\s+(\d+)")
    part = _extract_int(message, r"part\s+(\d+)")
    quantity = _extract_int(message, r"(?:qty|quantity)\s+(\d+)")
    return {"supplier_id": supplier, "part_id": part, "quantity": quantity}


def _extract_int(message: str, pattern: str) -> int:
    match = re.search(pattern, message, flags=re.IGNORECASE)
    if not match:
        raise ValueError("Assistant purchase draft requests must include supplier, part, and quantity ids")
    return int(match.group(1))


def _mutation_preview(tool_name: str, arguments: dict[str, object]) -> str:
    if tool_name == "create_purchase_request_draft":
        return (
            "Confirmation required before creating a draft purchase request "
            f"for supplier {arguments.get('supplier_id')}, part {arguments.get('part_id')}, "
            f"quantity {arguments.get('quantity')}."
        )
    return "Confirmation required before running this tool."


def _machine_label(machine: dict[str, object]) -> str:
    return f"{machine.get('brand', '')} {machine.get('model', '')}".strip()


def safe_assistant_message(message: str, tool_name: str = "unknown") -> str:
    request_numbers = sorted({match.group(0).upper() for match in REQUEST_NUMBER_PATTERN.finditer(message)})
    numeric_ids = [match.group(1) for match in re.finditer(r"\b(?:supplier|part|qty|quantity)\s+(\d+)\b", message, flags=re.IGNORECASE)]
    parts = [f"Вопрос: {_safe_staff_question(message)}", f"инструмент: {tool_name}"]
    if request_numbers:
        parts.append(f"заявки={','.join(request_numbers[:5])}")
    if numeric_ids:
        parts.append(f"ids={','.join(numeric_ids[:6])}")
    return "; ".join(parts)


def _safe_staff_question(message: str) -> str:
    cleaned = safe_assistant_text(message.strip())
    return cleaned[:220] if cleaned else "[empty]"


def safe_assistant_text(text: str) -> str:
    cleaned = str(text)
    request_numbers: dict[str, str] = {}
    sku_like_tokens: dict[str, str] = {}

    def _keep_request_number(match: re.Match[str]) -> str:
        placeholder = f"__SERVICEOPS_REQUEST_{len(request_numbers)}__"
        request_numbers[placeholder] = match.group(0).upper()
        return placeholder

    def _keep_sku_like_token(match: re.Match[str]) -> str:
        placeholder = f"__SERVICEOPS_SKU_{len(sku_like_tokens)}__"
        sku_like_tokens[placeholder] = match.group(0)
        return placeholder

    cleaned = REQUEST_NUMBER_PATTERN.sub(_keep_request_number, cleaned)
    cleaned = re.sub(r"\b(?=[A-Z0-9-]*[A-Z])(?=[A-Z0-9-]*\d)[A-Z][A-Z0-9-]{5,}\b", _keep_sku_like_token, cleaned)
    cleaned = re.sub(r"Authorization:\s*Bearer\s+\S+", "[credential redacted]", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", "[credential redacted]", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"\b(?:password|webhook[_\s-]?secret|token|api[_\s-]?key|x-serviceops-callback-secret)\b\s*(?:[:=]|\s)\s*[A-Za-z0-9._~+/=-]{6,}",
        "[credential redacted]",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\bapi-key\s*:\s*\S+", "[credential redacted]", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\+?\d[\d\s()\-]{7,}\d", "[phone redacted]", cleaned)
    cleaned = re.sub(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", "[email redacted]", cleaned)
    cleaned = re.sub(r"(?<![\w.\-])@\w[\w.\-]{2,}", "[telegram redacted]", cleaned)
    cleaned = re.sub(
        r"\b(?:internal|private)\s+note\s*:\s*[^;.\n]*",
        "internal/private note: [redacted]",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\b(?:внутренняя|приватная|частная)\s+заметка\s*:\s*[^;.\n]*",
        "внутренняя заметка: [redacted]",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\baddress\s*:\s*[^;.\n]*", "address: [redacted]", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bадрес\s*:\s*[^;.\n]*", "адрес: [redacted]", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    for placeholder, request_number in request_numbers.items():
        cleaned = cleaned.replace(placeholder, request_number)
    for placeholder, sku_like_token in sku_like_tokens.items():
        cleaned = cleaned.replace(placeholder, sku_like_token)
    return cleaned


def _contains_unredacted_sensitive_text(text: str) -> bool:
    cleaned = REQUEST_NUMBER_PATTERN.sub("", text)
    cleaned = re.sub(r"\b(?=[A-Z0-9-]*[A-Z])(?=[A-Z0-9-]*\d)[A-Z][A-Z0-9-]{5,}\b", "", cleaned)
    return bool(
        re.search(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", cleaned)
        or re.search(r"\+\d[\d\s()\-]{7,}\d", cleaned)
        or re.search(r"\b(?:phone|телефон|tel)\b\s*[:=]?\s*\d[\d\s()\-]{7,}\d", cleaned, flags=re.IGNORECASE)
        or re.search(r"Authorization:\s*Bearer\s+\S+", cleaned, flags=re.IGNORECASE)
        or re.search(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", cleaned, flags=re.IGNORECASE)
        or re.search(r"\b(?:password|webhook[_\s-]?secret|token|api[_\s-]?key|x-serviceops-callback-secret)\b\s*(?:[:=]|\s)\s*[A-Za-z0-9._~+/=-]{6,}", cleaned, flags=re.IGNORECASE)
    )


def _ordinal_request_label(ordinal_position: int) -> str:
    labels = {
        1: "First request",
        2: "Second request",
        3: "Third request",
        4: "Fourth request",
        5: "Fifth request",
        6: "Sixth request",
        7: "Seventh request",
        8: "Eighth request",
        9: "Ninth request",
        10: "Tenth request",
    }
    return labels.get(ordinal_position, f"Request #{ordinal_position}")


def create_assistant_planner(settings: object) -> AssistantPlanner | None:
    provider_name = str(getattr(settings, "ai_provider", "deterministic")).strip().lower()
    if provider_name == "deterministic":
        return None
    if provider_name == "openai-compatible":
        api_key = str(getattr(settings, "ai_api_key", "")).strip()
        if not api_key:
            raise ValueError("SERVICEOPS_AI_API_KEY is required when SERVICEOPS_AI_PROVIDER=openai-compatible")
        model = str(getattr(settings, "ai_model", "")).strip()
        if not model:
            raise ValueError("SERVICEOPS_AI_MODEL is required when SERVICEOPS_AI_PROVIDER=openai-compatible")
        return OpenAiCompatibleAssistantPlanner(
            api_base_url=str(getattr(settings, "ai_api_base_url", "https://api.openai.com/v1")),
            api_key=api_key,
            model=model,
            timeout_seconds=float(getattr(settings, "ai_timeout_seconds", 20.0)),
            max_retries=int(getattr(settings, "ai_max_retries", 2)),
        )
    raise ValueError(f"Unsupported SERVICEOPS_AI_PROVIDER: {provider_name}")
