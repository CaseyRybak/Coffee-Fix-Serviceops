import asyncio
from datetime import date
from pathlib import Path
from unittest.mock import patch

import httpx

from serviceops_api.config import Settings
from serviceops_api.ai_agents.assistant_tools import OpenAiCompatibleAssistantPlanner, create_assistant_planner, safe_assistant_text
from serviceops_api.ai_agents.models import AssistantRunPayload
from serviceops_api.inventory.models import CreatePartPayload, ReservationPayload, SupplierPayload
from serviceops_api.inventory.repository import SqliteInventoryRepository
from serviceops_api.inventory.use_cases import CreatePart, CreatePurchaseRequest, CreateSupplier, ReservePart, SetStockCount
from serviceops_api.ai_agents.use_cases import ConfirmStaffAssistantTool, RunStaffAssistant
from serviceops_api.knowledge_base.models import IngestKnowledgeDocumentPayload
from serviceops_api.knowledge_base.repository import SqliteKnowledgeBaseRepository
from serviceops_api.main import create_app
from serviceops_api.service_requests.repository import ServiceRequestRepository
from serviceops_api.staff_auth import hash_staff_password
from serviceops_api.staff_management.models import CreateStaffAccountPayload
from serviceops_api.staff_management.repository import SqliteStaffAccountRepository
from serviceops_api.technicians.repository import SqliteTechnicianProfileRepository


class FixedAssistantDate(date):
    @classmethod
    def today(cls) -> date:
        return cls(2026, 6, 19)


def intake_payload(*, brand: str = "Jura", problem: str = "Machine leaks water under brew group.") -> dict[str, object]:
    return {
        "customer": {
            "name": "Anna Petrova",
            "phone": "+7 999 111-22-33",
            "telegram": "@anna_fix",
            "client_type": "coffee_shop",
        },
        "machine": {"brand": brand, "model": "E8", "location_type": "coffee_shop"},
        "problem": problem,
        "address": "Tverskaya district",
        "urgency": "today",
    }


def create_staff(repository: SqliteStaffAccountRepository, username: str, roles: list[str]) -> None:
    repository.create_account(
        CreateStaffAccountPayload(
            username=username,
            first_name=username.split("@", 1)[0].title(),
            last_name="User",
            phone="+7 999 000-00-00",
            password="temporary-pass-1",
            roles=roles,  # type: ignore[arg-type]
        ),
        password_hash=hash_staff_password("temporary-pass-1"),
        actor="system",
    )


def create_repositories() -> tuple[
    ServiceRequestRepository,
    SqliteKnowledgeBaseRepository,
    SqliteInventoryRepository,
    SqliteStaffAccountRepository,
    SqliteTechnicianProfileRepository,
]:
    service_repository = ServiceRequestRepository.in_memory()
    knowledge_repository = SqliteKnowledgeBaseRepository.in_memory()
    inventory_repository = SqliteInventoryRepository.in_memory()
    staff_repository = SqliteStaffAccountRepository.in_memory()
    profile_repository = SqliteTechnicianProfileRepository.in_memory()
    create_staff(staff_repository, "dispatcher@coffeefix.local", ["dispatcher"])
    create_staff(staff_repository, "inventory@coffeefix.local", ["inventory"])
    create_staff(staff_repository, "admin@coffeefix.local", ["admin"])
    create_staff(staff_repository, "pavel@coffeefix.local", ["technician"])
    profile_repository.upsert_profile(
        "pavel@coffeefix.local",
        active=True,
        skill_brands=["Jura"],
        service_regions=["Tverskaya"],
        notes="Senior technician private note",
    )
    return service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository


def build_app(
    service_repository: ServiceRequestRepository,
    knowledge_repository: SqliteKnowledgeBaseRepository,
    inventory_repository: SqliteInventoryRepository,
    staff_repository: SqliteStaffAccountRepository,
    profile_repository: SqliteTechnicianProfileRepository,
):
    return create_app(
        service_request_repository=service_repository,
        knowledge_base_repository=knowledge_repository,
        inventory_repository=inventory_repository,
        staff_account_repository=staff_repository,
        technician_profile_repository=profile_repository,
    )


async def login(client: httpx.AsyncClient, username: str) -> str:
    response = await client.post(
        "/staff/login",
        json={"username": username, "password": "temporary-pass-1"},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


async def create_request(client: httpx.AsyncClient, **overrides: object) -> str:
    response = await client.post("/service-requests", json=intake_payload(**overrides))
    assert response.status_code == 201
    return str(response.json()["request_number"])


async def post_assistant(client: httpx.AsyncClient, token: str, message: str) -> httpx.Response:
    return await client.post("/assistant/runs", json={"message": message}, headers={"Authorization": f"Bearer {token}"})


def set_request_created_at(repository: ServiceRequestRepository, request_number: str, created_at: str) -> None:
    repository._connection.execute(  # type: ignore[attr-defined]
        "UPDATE service_requests SET created_at = ? WHERE request_number = ?",
        (created_at, request_number),
    )


def set_latest_status_event_created_at(repository: ServiceRequestRepository, request_number: str, status: str, created_at: str) -> None:
    repository._connection.execute(  # type: ignore[attr-defined]
        """
        UPDATE status_events
        SET created_at = ?
        WHERE id = (
            SELECT se.id
            FROM status_events se
            JOIN service_requests sr ON sr.id = se.service_request_id
            WHERE sr.request_number = ? AND se.status = ?
            ORDER BY se.id DESC
            LIMIT 1
        )
        """,
        (created_at, request_number, status),
    )


def test_assistant_text_sanitizer_preserves_sku_like_tokens_and_redacts_contacts() -> None:
    text = safe_assistant_text(
        "SKU SMOKE-DELONGHI-GRINDER-1781884328277 phone +7 999 100-00-01 "
        "token ABCDEF12345 api key SECRET12345 webhook secret hook-123456 email admin@coffeefix.local"
    )

    assert "SMOKE-DELONGHI-GRINDER-1781884328277" in text
    assert "+7 999 100-00-01" not in text
    assert "admin@coffeefix.local" not in text
    assert "[phone redacted]" in text
    assert "[email redacted]" in text
    assert "ABCDEF12345" not in text
    assert "SECRET12345" not in text
    assert "hook-123456" not in text
    assert text.count("[credential redacted]") == 3


def test_assistant_read_only_tools_are_staff_only_and_store_safe_history() -> None:
    async def scenario() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository = create_repositories()
        app = build_app(service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            token = await login(client, "dispatcher@coffeefix.local")
            request_number = await create_request(client)

            anonymous = await client.post("/assistant/runs", json={"message": f"find {request_number}"})
            found = await post_assistant(
                client,
                token,
                f"Найди заявку {request_number}, телефон +7 999 111-22-33, telegram @anna_fix",
            )
            history = await client.get("/assistant/runs", headers={"Authorization": f"Bearer {token}"})
            public_status = await client.get(f"/service-requests/{request_number}/status")
        return anonymous.json(), found.json(), {"history": history.json(), "public": public_status.json()}

    anonymous, found, snapshots = asyncio.run(scenario())

    assert anonymous["detail"] == "Staff authentication required"
    assert found["status"] == "completed"
    assert found["tool_calls"][0]["tool_name"] == "find_request"
    assert found["tool_calls"][0]["policy"] == "read_only"
    assert found["tool_calls"][0]["status"] == "completed"
    body_text = str(found)
    assert "CFX-" in body_text
    assert "+7 999 111-22-33" not in body_text
    assert "@anna_fix" not in body_text
    history_text = str(snapshots["history"])
    assert "+7 999 111-22-33" not in history_text
    assert "@anna_fix" not in history_text
    public_text = str(snapshots["public"])
    assert "assistant" not in public_text.lower()
    assert "tool_calls" not in public_text


def test_assistant_can_run_reporting_knowledge_stock_and_recommendation_tools() -> None:
    async def scenario() -> list[dict[str, object]]:
        service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository = create_repositories()
        app = build_app(service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            dispatcher_token = await login(client, "dispatcher@coffeefix.local")
            admin_token = await login(client, "admin@coffeefix.local")
            request_number = await create_request(client, problem="E61 group overheats after descaling.")
            service_repository._connection.execute(
                "UPDATE service_requests SET created_at = ? WHERE request_number = ?",
                ("2026-06-17T03:00:00+00:00", request_number),
            )
            await client.post(
                "/knowledge-base/documents",
                json=IngestKnowledgeDocumentPayload(
                    title="E61 overheating guide",
                    source_uri="seed://repair/e61-overheating",
                    body="E61 group overheating after descaling can involve thermosiphon restriction.",
                ).model_dump(),
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            inventory_token = await login(client, "inventory@coffeefix.local")
            part = CreatePart(inventory_repository).execute(
                CreatePartPayload(sku="FLOW-METER", name="Flow meter", unit="pcs")
            )
            SetStockCount(inventory_repository).execute(part.part_id, quantity_on_hand=1, low_stock_threshold=2)

            prompts = [
                (admin_token, "Покажи просроченные заявки"),
                (dispatcher_token, "Поищи в базе знаний E61 overheating"),
                (inventory_token, "Проверь склад FLOW-METER"),
                (dispatcher_token, f"Порекомендуй техника для {request_number}"),
                (admin_token, "Собери дневной отчет"),
                (admin_token, "сколько всего получено заявок?"),
            ]
            results = []
            for token, prompt in prompts:
                response = await post_assistant(client, token, prompt)
                results.append(response.json())
        return results

    with patch("serviceops_api.ai_agents.assistant_tools.date", FixedAssistantDate):
        results = asyncio.run(scenario())

    assert [result["status"] for result in results] == ["completed"] * 6
    assert [result["tool_calls"][0]["tool_name"] for result in results] == [
        "list_overdue_requests",
        "search_knowledge_base",
        "check_part_stock",
        "recommend_technician",
        "generate_daily_report",
        "answer_requests",
    ]
    assert "CFX-" in str(results[0])
    assert "seed://repair/e61-overheating" in str(results[1])
    assert "FLOW-METER" in str(results[2])
    assert "Pavel User" in str(results[3])
    assert "pavel@coffeefix.local" not in str(results[3]["tool_calls"])
    assert "Senior technician private note" not in str(results[3])
    assert "dashboard_url" in str(results[4])
    assert "Всего заявок: 1" in str(results[5])
    assert "Всего заявок: 1" in results[5]["assistant_message"]


def test_assistant_answers_fifteen_broad_serviceops_questions_with_self_check() -> None:
    async def scenario() -> tuple[list[dict[str, object]], dict[str, str]]:
        service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository = create_repositories()
        create_staff(staff_repository, "irina@coffeefix.local", ["technician"])
        profile_repository.upsert_profile(
            "irina@coffeefix.local",
            active=True,
            skill_brands=["Saeco"],
            service_regions=["Arbat"],
            notes="Private technician note must stay out",
        )
        cleaning = CreatePart(inventory_repository).execute(
            CreatePartPayload(
                sku="JURA-CLEAN-TABS",
                name="Таблетки для очистки Jura",
                brand="Jura",
                unit="pcs",
                part_type="cleaning",
            )
        )
        valve = CreatePart(inventory_repository).execute(
            CreatePartPayload(sku="JURA-VALVE", name="Клапан Jura", brand="Jura", unit="pcs")
        )
        pump = CreatePart(inventory_repository).execute(
            CreatePartPayload(sku="PUMP-ULKA", name="Ulka pump", brand="Ulka", unit="pcs")
        )
        SetStockCount(inventory_repository).execute(cleaning.part_id, quantity_on_hand=12, low_stock_threshold=3)
        SetStockCount(inventory_repository).execute(valve.part_id, quantity_on_hand=4, low_stock_threshold=2)
        SetStockCount(inventory_repository).execute(pump.part_id, quantity_on_hand=1, low_stock_threshold=3)

        app = build_app(service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            dispatcher_token = await login(client, "dispatcher@coffeefix.local")
            admin_token = await login(client, "admin@coffeefix.local")
            inventory_token = await login(client, "inventory@coffeefix.local")
            first = await create_request(client, brand="Jura", problem="Machine leaks water under brew group.")
            second = await create_request(client, brand="Saeco", problem="No coffee flow from group.")
            third = await create_request(client, brand="La Marzocco", problem="Machine does not power on.")
            service_repository._connection.execute(
                "UPDATE service_requests SET created_at = ? WHERE request_number = ?",
                ("2026-06-17T03:00:00+00:00", first),
            )
            await client.post(
                f"/dispatcher/service-requests/{first}/appointments",
                json={
                    "technician_identifier": "pavel@coffeefix.local",
                    "technician_name": "Pavel User",
                    "starts_at": "2026-06-20T14:00:00+03:00",
                    "ends_at": "2026-06-20T16:00:00+03:00",
                    "window_label": "20 июня 14:00-16:00",
                },
                headers={"Authorization": f"Bearer {dispatcher_token}"},
            )
            await client.post(
                "/knowledge-base/documents",
                json=IngestKnowledgeDocumentPayload(
                    title="Coffee Fix services",
                    source_uri="seed://site/services",
                    body="На сайте Coffee Fix указаны услуги: ремонт кофемашин, диагностика, выезд мастера и обслуживание кофейного оборудования.",
                ).model_dump(),
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            await client.post(
                "/knowledge-base/documents",
                json=IngestKnowledgeDocumentPayload(
                    title="No power startup",
                    source_uri="seed://repair/no-power-startup",
                    body="Если кофемашина не включается, сначала проверьте питание, розетку, сетевой кабель, кнопку включения и предохранитель.",
                ).model_dump(),
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            cases = [
                (admin_token, "сколько всего получено заявок на ремонт?", "answer_requests", ["Всего заявок: 3"], []),
                (admin_token, "покажи просроченные заявки", "list_overdue_requests", [first], []),
                (dispatcher_token, "найди вторую заявку", "find_request", [second], [third]),
                (dispatcher_token, f"покажи заявку {third}", "find_request", [third, "La Marzocco"], []),
                (dispatcher_token, f"порекомендуй мастера для {first}", "recommend_technician", ["Pavel User"], ["Private technician note", "pavel@coffeefix.local"]),
                (dispatcher_token, "как зовут мастеров?", "answer_technicians", ["Pavel User", "Irina User"], ["Private technician note", "pavel@coffeefix.local", "irina@coffeefix.local"]),
                (dispatcher_token, "сколько мастеров у нас всего?", "answer_technicians", ["Всего мастеров: 2", "активных: 2"], []),
                (dispatcher_token, "кто умеет Jura?", "answer_technicians", ["Jura умеют", "Pavel User"], ["pavel@coffeefix.local", "irina@coffeefix.local"]),
                (dispatcher_token, "сколько визитов мастеров сейчас в плане?", "answer_schedule", ["Запланированных визитов мастеров: 1"], []),
                (dispatcher_token, "какие визиты запланированы?", "answer_schedule", [first, "20 июня 14:00-16:00"], []),
                (inventory_token, "сколько на складе таблеток для очистки?", "check_part_stock", ["JURA-CLEAN-TABS", "доступно=12"], ["PUMP-ULKA"]),
                (inventory_token, "сколько запчастей Jura на складе?", "check_part_stock", ["Найдено складских позиций: 2", "JURA-VALVE"], ["PUMP-ULKA"]),
                (inventory_token, "что надо докупить?", "check_part_stock", ["PUMP-ULKA"], ["JURA-CLEAN-TABS"]),
                (dispatcher_token, "какие услуги есть на сайте?", "answer_service_catalog", ["ремонт кофемашин", "seed://site/services"], []),
                (dispatcher_token, "что делать если Jura не включается?", "search_knowledge_base", ["питание", "seed://repair/no-power-startup"], ["JURA-CLEAN-TABS"]),
            ]
            results = []
            for token, question, expected_tool, expected_texts, forbidden_texts in cases:
                response = await post_assistant(client, token, question)
                results.append(
                    {
                        "question": question,
                        "expected_tool": expected_tool,
                        "expected_texts": expected_texts,
                        "forbidden_texts": forbidden_texts,
                        "body": response.json(),
                    }
                )
        return results, {"first": first, "second": second, "third": third}

    results, _numbers = asyncio.run(scenario())

    assert len(results) == 15
    for result in results:
        body = result["body"]
        assert body["status"] == "completed", result["question"]
        assert body["tool_calls"][0]["tool_name"] == result["expected_tool"], result["question"]
        assert body["tool_calls"][-1]["tool_name"] == "assistant_self_check", result["question"]
        assert body["tool_calls"][-1]["status"] == "completed", result["question"]
        assert body["tool_calls"][-1]["arguments"]["passed"] is True, result["question"]
        body_text = str(body)
        for expected in result["expected_texts"]:
            assert expected in body_text, result["question"]
        for forbidden in result["forbidden_texts"]:
            assert forbidden not in body_text, result["question"]


def test_assistant_answers_database_wide_operational_questions_with_fact_checks() -> None:
    async def scenario() -> dict[str, dict[str, object]]:
        service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository = create_repositories()
        CreateSupplier(inventory_repository, actor="inventory@coffeefix.local").execute(
            SupplierPayload(name="North Parts", contact_name="Olga Buyer", phone="+7 999 100-00-01", email="north@example.test")
        )
        CreateSupplier(inventory_repository, actor="inventory@coffeefix.local").execute(
            SupplierPayload(name="South Spares", contact_name="Ivan Buyer", phone="+7 999 100-00-02", email="south@example.test")
        )
        grinder = CreatePart(inventory_repository).execute(
            CreatePartPayload(sku="DELONGHI-GRINDER", name="Кофемолка DeLonghi", brand="DeLonghi", unit="pcs")
        )
        pump = CreatePart(inventory_repository).execute(
            CreatePartPayload(sku="JURA-PUMP", name="Помпа Jura", brand="Jura", unit="pcs")
        )
        SetStockCount(inventory_repository).execute(grinder.part_id, quantity_on_hand=7, low_stock_threshold=2)
        SetStockCount(inventory_repository).execute(pump.part_id, quantity_on_hand=5, low_stock_threshold=2)

        app = build_app(service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            admin_token = await login(client, "admin@coffeefix.local")
            inventory_token = await login(client, "inventory@coffeefix.local")
            dispatcher_token = await login(client, "dispatcher@coffeefix.local")
            first = await create_request(client, brand="Jura", problem="First request on target date.")
            second = await create_request(client, brand="Saeco", problem="Second request on target date.")
            third = await create_request(client, brand="DeLonghi", problem="Other date request.")
            service_repository._connection.execute(
                "UPDATE service_requests SET created_at = ? WHERE request_number = ?",
                ("2026-06-17T03:00:00+00:00", first),
            )
            service_repository._connection.execute(
                "UPDATE service_requests SET created_at = ? WHERE request_number = ?",
                ("2026-06-17T09:00:00+00:00", second),
            )
            service_repository._connection.execute(
                "UPDATE service_requests SET created_at = ? WHERE request_number = ?",
                ("2026-06-15T09:00:00+00:00", third),
            )
            ReservePart(inventory_repository, actor="inventory@coffeefix.local").execute(
                ReservationPayload(request_number=first, part_id=grinder.part_id, quantity=2)
            )
            ReservePart(inventory_repository, actor="inventory@coffeefix.local").execute(
                ReservationPayload(request_number=second, part_id=pump.part_id, quantity=1)
            )

            questions = {
                "new_17": (admin_token, "сколько новых заявок было получено 17 июня?"),
                "new_15": (admin_token, "сколько новых заявок было получено 15 июня?"),
                "suppliers_count": (inventory_token, "сколько у нас поставщиков?"),
                "suppliers_list": (inventory_token, "перечисли наших поставщиков"),
                "reserved_total": (inventory_token, "сколько запчастей в резерве?"),
                "active_reserves": (inventory_token, "есть активные резервы?"),
                "inventory_positions": (inventory_token, "сколько на складе позиций?"),
                "inventory_part_positions": (inventory_token, "сколько на складе позиций запчастей?"),
                "technician_regions": (dispatcher_token, "какие районы покрывают наши мастера?"),
                "delonghi_stock": (inventory_token, "сколько запчастей делонги на складе?"),
            }
            results = {}
            for key, (token, question) in questions.items():
                response = await post_assistant(client, token, question)
                results[key] = response.json()
        return results

    with patch("serviceops_api.ai_agents.assistant_tools.date", FixedAssistantDate):
        results = asyncio.run(scenario())

    assert results["new_17"]["status"] == "completed"
    assert "17 июня 2026" in results["new_17"]["assistant_message"]
    assert "Новые заявки: 2" in results["new_17"]["assistant_message"]
    assert "Всего заявок: 3" not in results["new_17"]["assistant_message"]
    assert results["new_15"]["status"] == "completed"
    assert "15 июня 2026" in results["new_15"]["assistant_message"]
    assert "Новые заявки: 1" in results["new_15"]["assistant_message"]

    assert results["suppliers_count"]["tool_calls"][0]["tool_name"] == "answer_database_query"
    assert "Поставщиков: 2" in results["suppliers_count"]["assistant_message"]
    assert "Coffee Fix указаны услуги" not in results["suppliers_count"]["assistant_message"]
    assert "North Parts" in results["suppliers_list"]["assistant_message"]
    assert "South Spares" in results["suppliers_list"]["assistant_message"]
    assert "+7 999" not in str(results["suppliers_list"])

    assert "В активном резерве: 3 pcs" in results["reserved_total"]["assistant_message"]
    assert results["active_reserves"]["status"] == "completed"
    assert results["active_reserves"]["tool_calls"][0]["tool_name"] == "answer_database_query"
    assert "В активном резерве: 3 pcs" in results["active_reserves"]["assistant_message"]
    assert results["active_reserves"]["tool_calls"][-1]["arguments"]["passed"] is True
    assert results["inventory_positions"]["status"] == "completed"
    assert results["inventory_positions"]["tool_calls"][0]["tool_name"] == "answer_database_query"
    assert "Складских позиций: 2" in results["inventory_positions"]["assistant_message"]
    assert "не нашёл совпадений" not in results["inventory_positions"]["assistant_message"]
    assert results["inventory_part_positions"]["tool_calls"][0]["tool_name"] == "answer_database_query"
    assert "Складских позиций запчастей: 2" in results["inventory_part_positions"]["assistant_message"]
    assert "DELONGHI-GRINDER" in results["delonghi_stock"]["assistant_message"]
    assert "доступно=5" in results["delonghi_stock"]["assistant_message"]
    assert "Tverskaya" in results["technician_regions"]["assistant_message"]
    assert results["technician_regions"]["tool_calls"][-1]["arguments"]["passed"] is True


def test_assistant_handles_service_site_procurement_relative_date_and_meta_questions() -> None:
    async def scenario() -> dict[str, dict[str, object]]:
        service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository = create_repositories()
        create_staff(staff_repository, "irina@coffeefix.local", ["technician"])
        profile_repository.upsert_profile(
            "irina@coffeefix.local",
            active=True,
            skill_brands=["Saeco"],
            service_regions=["Arbat"],
            notes="Private note must not leak",
        )
        supplier = CreateSupplier(inventory_repository, actor="inventory@coffeefix.local").execute(
            SupplierPayload(name="Parts Partner", contact_name="Olga Buyer", phone="+7 999 100-00-01")
        )
        pump = CreatePart(inventory_repository).execute(
            CreatePartPayload(sku="SMOKE-FLOW-PUMP", name="Ulka pump smoke", brand="Ulka", unit="pcs")
        )
        purchase = CreatePurchaseRequest(inventory_repository, actor="inventory@coffeefix.local").execute(
            supplier.supplier_id,
            items=[{"part_id": pump.part_id, "quantity": 1, "note": None}],  # type: ignore[list-item]
            note="planned stock refill",
        )
        inventory_repository.submit_purchase_request(purchase.purchase_request_id, actor="inventory@coffeefix.local")
        inventory_repository.approve_purchase_request(purchase.purchase_request_id, actor="admin@coffeefix.local")
        inventory_repository.mark_purchase_request_ordered(purchase.purchase_request_id, actor="inventory@coffeefix.local")
        inventory_repository.receive_purchase_request(purchase.purchase_request_id, actor="inventory@coffeefix.local", note="arrived")
        inventory_repository._connection.execute(  # type: ignore[attr-defined]
            "UPDATE purchase_requests SET created_at = ?, updated_at = ? WHERE id = ?",
            ("2026-06-19T10:00:00+00:00", "2026-06-19T10:00:00+00:00", purchase.purchase_request_id),
        )

        app = build_app(service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            admin_token = await login(client, "admin@coffeefix.local")
            dispatcher_token = await login(client, "dispatcher@coffeefix.local")
            inventory_token = await login(client, "inventory@coffeefix.local")
            await client.post(
                "/knowledge-base/documents",
                json=IngestKnowledgeDocumentPayload(
                    title="Coffee Fix service catalog",
                    source_uri="seed://site/services",
                    body=(
                        "Coffee Fix service catalog: ремонт кофемашин, диагностика, выезд мастера, "
                        "обслуживание кофейного оборудования, подбор запчастей. Бренды в каталоге: Jura, Saeco, "
                        "DeLonghi, La Marzocco, Nuova Simonelli, WMF, Rancilio."
                    ),
                ).model_dump(),
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            await client.post(
                "/knowledge-base/documents",
                json=IngestKnowledgeDocumentPayload(
                    title="No power startup",
                    source_uri="seed://repair/no-power-startup",
                    body=(
                        "Если кофемашина не включается, проверьте питание, розетку, кабель и предохранитель. "
                        "Что проверить при проблеме питания: кнопку включения, предохранитель и сетевой кабель."
                    ),
                ).model_dump(),
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            today_first = await create_request(client, brand="Jura", problem="Today request one.")
            today_second = await create_request(client, brand="Saeco", problem="Today request two.")
            old_request = await create_request(client, brand="DeLonghi", problem="Old request.")
            service_repository._connection.execute(
                "UPDATE service_requests SET created_at = ? WHERE request_number = ?",
                ("2026-06-19T08:00:00+00:00", today_first),
            )
            service_repository._connection.execute(
                "UPDATE service_requests SET created_at = ? WHERE request_number = ?",
                ("2026-06-19T09:00:00+00:00", today_second),
            )
            service_repository._connection.execute(
                "UPDATE service_requests SET created_at = ? WHERE request_number = ?",
                ("2026-06-11T09:00:00+00:00", old_request),
            )
            questions = {
                "capabilities": (dispatcher_token, "что ты умеешь?"),
                "functional": (dispatcher_token, "какой у тебя функционал?"),
                "service_regions": (dispatcher_token, "какие районы обслуживает наш сервис?"),
                "technician_phones": (dispatcher_token, "дай номера телефонов мастеров"),
                "today_new": (admin_token, "сколько новых заявок за сегодня?"),
                "recent_procurement": (inventory_token, "какие закупки завершены за последние 7 дней?"),
                "unknown_brand": (dispatcher_token, 'мы ремонтируем кофемашины "капибара"?'),
                "weak_repair_match": (dispatcher_token, "кофемашина трещит, что проверить?"),
            }
            results = {}
            for key, (token, question) in questions.items():
                response = await post_assistant(client, token, question)
                results[key] = response.json()
        return results

    with patch("serviceops_api.ai_agents.assistant_tools.date", FixedAssistantDate):
        results = asyncio.run(scenario())

    assert results["capabilities"]["tool_calls"][0]["tool_name"] == "answer_capabilities"
    assert "заяв" in results["capabilities"]["assistant_message"].casefold()
    assert "закуп" in results["capabilities"]["assistant_message"].casefold()
    assert "источник" not in results["capabilities"]["assistant_message"].casefold()
    assert results["functional"]["tool_calls"][0]["tool_name"] == "answer_capabilities"

    assert results["service_regions"]["tool_calls"][0]["tool_name"] == "answer_service_catalog"
    assert "Tverskaya" in results["service_regions"]["assistant_message"]
    assert "Arbat" in results["service_regions"]["assistant_message"]
    assert "dispatcher@coffeefix.local" not in str(results["service_regions"]["tool_calls"])

    assert results["technician_phones"]["tool_calls"][0]["tool_name"] == "answer_staff_contacts"
    assert "+7 999" not in str(results["technician_phones"]["tool_calls"])
    assert "@coffeefix.local" not in str(results["technician_phones"]["tool_calls"])
    assert "не выдаю" in results["technician_phones"]["assistant_message"].casefold()

    assert results["today_new"]["tool_calls"][0]["tool_name"] == "answer_database_query"
    assert "19 июня 2026" in results["today_new"]["assistant_message"]
    assert "Новые заявки: 2" in results["today_new"]["assistant_message"]
    assert "Всего заявок: 3" not in results["today_new"]["assistant_message"]

    assert results["recent_procurement"]["tool_calls"][0]["tool_name"] == "answer_procurement"
    assert "получено: 1" in results["recent_procurement"]["assistant_message"].casefold()
    assert "SMOKE-FLOW-PUMP" in results["recent_procurement"]["assistant_message"]
    assert results["recent_procurement"]["tool_calls"][0]["result_refs"][0]["href"] == "/procurement"
    assert "check_part_stock" not in str(results["recent_procurement"])

    assert results["unknown_brand"]["tool_calls"][0]["tool_name"] == "answer_service_catalog"
    assert "капибара" in results["unknown_brand"]["assistant_message"].casefold()
    assert "не нашёл подтверждения" in results["unknown_brand"]["assistant_message"].casefold()
    assert "ремонт кофемашин" not in results["unknown_brand"]["assistant_message"]

    assert results["weak_repair_match"]["tool_calls"][0]["tool_name"] == "search_knowledge_base"
    assert "не нашёл уверенного" in results["weak_repair_match"]["assistant_message"].casefold()
    assert "не включается" not in results["weak_repair_match"]["assistant_message"].casefold()


def test_assistant_uses_structured_filters_for_status_staff_visits_and_procurement_questions() -> None:
    async def scenario() -> dict[str, dict[str, object]]:
        service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository = create_repositories()
        create_staff(staff_repository, "irina@coffeefix.local", ["dispatcher"])
        supplier = CreateSupplier(inventory_repository, actor="inventory@coffeefix.local").execute(
            SupplierPayload(name="Approval Parts", contact_name="Olga Buyer", phone="+7 999 100-00-01")
        )
        gasket = CreatePart(inventory_repository).execute(
            CreatePartPayload(sku="APPROVAL-GASKET", name="Approval gasket", brand="Jura", unit="pcs")
        )
        purchase = CreatePurchaseRequest(inventory_repository, actor="inventory@coffeefix.local").execute(
            supplier.supplier_id,
            items=[{"part_id": gasket.part_id, "quantity": 4, "note": None}],  # type: ignore[list-item]
            note="needs approval",
        )
        inventory_repository.submit_purchase_request(purchase.purchase_request_id, actor="inventory@coffeefix.local")

        app = build_app(service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            admin_token = await login(client, "admin@coffeefix.local")
            inventory_token = await login(client, "inventory@coffeefix.local")
            dispatcher_token = await login(client, "dispatcher@coffeefix.local")
            first = await create_request(client, brand="Jura", problem="Target date new request one.")
            second = await create_request(client, brand="Saeco", problem="Target date new request two.")
            completed_today = await create_request(client, brand="DeLonghi", problem="Completed today.")
            completed_on_17 = await create_request(client, brand="Jura", problem="Created earlier, completed on target date.")
            closed_on_17 = await create_request(client, brand="Saeco", problem="Created earlier, closed on target date.")
            scheduled = await create_request(client, brand="Jura", problem="Scheduled visit on another date.")
            completed_visit = await create_request(client, brand="Jura", problem="Visit completed on target date.")
            set_request_created_at(service_repository, first, "2026-06-17T08:00:00+00:00")
            set_request_created_at(service_repository, second, "2026-06-17T09:00:00+00:00")
            set_request_created_at(service_repository, completed_today, "2026-06-18T09:00:00+00:00")
            set_request_created_at(service_repository, completed_on_17, "2026-06-15T09:00:00+00:00")
            set_request_created_at(service_repository, closed_on_17, "2026-06-15T10:00:00+00:00")
            set_request_created_at(service_repository, completed_visit, "2026-06-09T09:00:00+00:00")
            service_repository.add_status_event(completed_today, "completed", "Ремонт завершен", "Done", "technician")
            service_repository.add_status_event(completed_on_17, "completed", "Ремонт завершен", "Done", "technician")
            service_repository.add_status_event(closed_on_17, "closed", "Заявка закрыта", "Closed", "dispatcher")
            set_latest_status_event_created_at(service_repository, completed_today, "completed", "2026-06-19T13:00:00+00:00")
            set_latest_status_event_created_at(service_repository, completed_on_17, "completed", "2026-06-17T10:00:00+00:00")
            set_latest_status_event_created_at(service_repository, closed_on_17, "closed", "2026-06-17T11:00:00+00:00")
            await client.post(
                f"/dispatcher/service-requests/{scheduled}/appointments",
                json={
                    "technician_identifier": "pavel@coffeefix.local",
                    "technician_name": "Pavel User",
                    "starts_at": "2026-06-11T14:00:00+03:00",
                    "ends_at": "2026-06-11T16:00:00+03:00",
                    "window_label": "11 июня 14:00-16:00",
                },
                headers={"Authorization": f"Bearer {dispatcher_token}"},
            )
            await client.post(
                f"/dispatcher/service-requests/{completed_visit}/appointments",
                json={
                    "technician_identifier": "pavel@coffeefix.local",
                    "technician_name": "Pavel User",
                    "starts_at": "2026-06-10T10:00:00+03:00",
                    "ends_at": "2026-06-10T12:00:00+03:00",
                    "window_label": "10 июня 10:00-12:00",
                },
                headers={"Authorization": f"Bearer {dispatcher_token}"},
            )
            service_repository.add_status_event(completed_visit, "completed", "Ремонт завершен", "Done", "technician")
            set_latest_status_event_created_at(service_repository, completed_visit, "completed", "2026-06-10T12:30:00+00:00")

            questions = {
                "completed_17": (admin_token, "сколько завершенных заявок за 17 июня?"),
                "completed_today": (admin_token, "сколько завершенных заявок за сегодня?"),
                "staff_count": (admin_token, "сколько сотрудников в компании?"),
                "completed_visits": (dispatcher_token, "сколько визитов выполнено 10 июня?"),
                "pending_procurement": (inventory_token, "сколько закупок на согласовании?"),
            }
            results = {}
            for key, (token, question) in questions.items():
                response = await post_assistant(client, token, question)
                results[key] = response.json()
        return results

    with patch("serviceops_api.ai_agents.assistant_tools.date", FixedAssistantDate):
        results = asyncio.run(scenario())

    assert results["completed_17"]["status"] == "completed"
    assert results["completed_17"]["tool_calls"][0]["tool_name"] == "answer_database_query"
    assert results["completed_17"]["tool_calls"][0]["arguments"]["status"] == "completed"
    assert results["completed_17"]["tool_calls"][0]["arguments"]["statuses"] == ["completed", "closed"]
    assert "17 июня 2026: Завершенные заявки: 2" in results["completed_17"]["assistant_message"]
    assert "Заявки: 2" not in results["completed_17"]["assistant_message"]

    assert results["completed_today"]["tool_calls"][0]["arguments"]["status"] == "completed"
    assert "19 июня 2026: Завершенные заявки: 1" in results["completed_today"]["assistant_message"]

    assert results["staff_count"]["status"] == "completed"
    assert results["staff_count"]["tool_calls"][0]["tool_name"] == "answer_database_query"
    assert "Сотрудников: 5" in results["staff_count"]["assistant_message"]
    assert "Телефоны мастеров" not in results["staff_count"]["assistant_message"]

    assert results["completed_visits"]["status"] == "completed"
    assert "10 июня 2026: Выполненные визиты: 1" in results["completed_visits"]["assistant_message"]
    assert "Запланированных визитов" not in results["completed_visits"]["assistant_message"]

    assert results["pending_procurement"]["status"] == "completed"
    assert results["pending_procurement"]["tool_calls"][0]["tool_name"] == "answer_procurement"
    assert "на согласовании: 1" in results["pending_procurement"]["assistant_message"].casefold()
    assert "received" not in results["pending_procurement"]["assistant_message"].casefold()


def test_assistant_finds_ordinal_request_and_keeps_safe_question_in_history() -> None:
    async def scenario() -> dict[str, object]:
        service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository = create_repositories()
        app = build_app(service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            admin_token = await login(client, "admin@coffeefix.local")
            first = await create_request(client, brand="Jura", problem="First created request.")
            second = await create_request(client, brand="Nuova Simonelli", problem="Second created request.")
            latest = await create_request(client, brand="La Marzocco", problem="Latest created request.")

            response = await post_assistant(client, admin_token, "найди вторую заявку")
            history = await client.get("/assistant/runs", headers={"Authorization": f"Bearer {admin_token}"})
        return {
            "response": response.json(),
            "history": history.json(),
            "numbers": {"first": first, "second": second, "latest": latest},
        }

    state = asyncio.run(scenario())
    response = state["response"]
    numbers = state["numbers"]

    assert response["status"] == "completed"
    assert response["tool_calls"][0]["tool_name"] == "find_request"
    assert response["tool_calls"][0]["arguments"] == {"ordinal_position": 2}
    assert numbers["second"] in response["assistant_message"]
    assert numbers["latest"] not in response["assistant_message"]
    assert response["safe_message"] == "tool=find_request"
    assert "найди вторую заявку" not in str(state["history"])


def test_assistant_enforces_stock_role_boundary_and_redacts_secret_like_prompts() -> None:
    async def scenario() -> tuple[dict[str, object], dict[str, object]]:
        service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository = create_repositories()
        part = CreatePart(inventory_repository).execute(
            CreatePartPayload(sku="FLOW-METER", name="Flow meter", unit="pcs")
        )
        SetStockCount(inventory_repository).execute(part.part_id, quantity_on_hand=1, low_stock_threshold=2)
        app = build_app(service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            dispatcher_token = await login(client, "dispatcher@coffeefix.local")
            inventory_token = await login(client, "inventory@coffeefix.local")
            dispatcher_stock = await post_assistant(client, dispatcher_token, "Проверь склад FLOW-METER")
            inventory_kb = await post_assistant(client, inventory_token, "какие услуги есть на сайте?")
            await post_assistant(
                client,
                dispatcher_token,
                "Поищи в базе знаний Authorization: Bearer kb.secret телефон +7 999 111-22-33 внутренняя заметка: менять цену",
            )
            await post_assistant(
                client,
                inventory_token,
                "Проверь склад FLOW-METER password=secret webhook_secret=hook-123 @anna_fix",
            )
            await post_assistant(
                client,
                inventory_token,
                "stock Authorization: Bearer ABCDEF",
            )
            secret_prompt = await post_assistant(
                client,
                dispatcher_token,
                "Найди CFX-20260617-000001 password=secret Authorization: Bearer abc.def webhook_secret=hook-123 внутренняя заметка: звонить директору",
            )
            dispatcher_history = await client.get("/assistant/runs", headers={"Authorization": f"Bearer {dispatcher_token}"})
            inventory_history = await client.get("/assistant/runs", headers={"Authorization": f"Bearer {inventory_token}"})
        return dispatcher_stock.json(), {
            "inventory_kb": inventory_kb.json(),
            "secret_prompt": secret_prompt.json(),
            "history": {
                "dispatcher": dispatcher_history.json(),
                "inventory": inventory_history.json(),
            },
        }

    dispatcher_stock, secret_state = asyncio.run(scenario())

    assert dispatcher_stock["detail"] == "Staff role is not allowed"
    assert secret_state["inventory_kb"]["detail"] == "Staff role is not allowed"
    history_text = str(secret_state["history"])
    assert "Bearer" not in history_text
    assert "password" not in history_text
    assert "webhook_secret" not in history_text
    assert "звонить директору" not in history_text
    assert "менять цену" not in history_text
    assert "kb.secret" not in history_text
    assert "ABCDEF" not in history_text
    assert "@anna_fix" not in history_text
    assert "CFX-20260617-000001" in history_text


def test_assistant_redacts_sensitive_knowledge_base_content_from_answer_and_history() -> None:
    async def scenario() -> dict[str, object]:
        service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository = create_repositories()
        app = build_app(service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            admin_token = await login(client, "admin@coffeefix.local")
            dispatcher_token = await login(client, "dispatcher@coffeefix.local")
            await client.post(
                "/knowledge-base/documents",
                json=IngestKnowledgeDocumentPayload(
                    title="Poisoned callback diagnostic",
                    source_uri="seed://repair/poisoned-callback",
                    body=(
                        "Poisoned callback diagnostic guide Authorization: Bearer secret-token-123 "
                        "X-ServiceOps-Callback-Secret: callback-secret customer phone +7 999 111-22-33. api-key: api-secret. "
                        "private note: call owner at +7 999 111-22-33 and @private_tech. "
                        "For no power, first check socket and fuse."
                    ),
                ).model_dump(),
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            response = await post_assistant(client, dispatcher_token, "poisoned callback diagnostic no power")
            history = await client.get("/assistant/runs", headers={"Authorization": f"Bearer {dispatcher_token}"})
        return {"response": response.json(), "history": history.json()}

    state = asyncio.run(scenario())

    assert state["response"]["status"] == "completed"
    text = str(state)
    assert "secret-token-123" not in text
    assert "callback-secret" not in text
    assert "api-secret" not in text
    assert "+7 999 111-22-33" not in text
    assert "@private_tech" not in text
    assert "call owner" not in text
    assert "[credential redacted]" in text
    assert "[phone redacted]" in text


def test_assistant_provider_or_planner_failure_records_safe_failed_run() -> None:
    class SavingHistory:
        saved: dict[str, object] | None = None

        def save_run(self, **kwargs: object) -> dict[str, object]:
            self.saved = dict(kwargs)
            tool_calls = list(kwargs["tool_calls"])  # type: ignore[arg-type]
            return {
                "run_id": 77,
                "actor_username": kwargs["actor_username"],
                "safe_message": kwargs["safe_message"],
                "status": kwargs["status"],
                "assistant_message": kwargs["assistant_message"],
                "tool_calls": [
                    {
                        "tool_call_id": 1,
                        **dict(tool_calls[0]),  # type: ignore[arg-type]
                        "created_at": "2026-06-17T12:00:00+00:00",
                        "updated_at": "2026-06-17T12:00:00+00:00",
                    }
                ],
                "created_at": "2026-06-17T12:00:00+00:00",
                "updated_at": "2026-06-17T12:00:00+00:00",
            }

    class FailingPlanner:
        def plan(self, message: str) -> dict[str, object]:
            assert "Bearer secret-token" in message
            raise RuntimeError("provider unavailable with Bearer secret-token")

    history = SavingHistory()
    staff = type("Staff", (), {"username": "dispatcher@coffeefix.local", "roles": ["dispatcher"]})()

    response = RunStaffAssistant(history, FailingPlanner()).execute(  # type: ignore[arg-type]
        AssistantRunPayload(message="Поищи в базе знаний Authorization: Bearer secret-token"),
        staff,
    )

    assert response.status == "failed"
    assert response.safe_message == "tool=unknown"
    assert response.tool_calls[0].result_summary == "Assistant tool request failed."
    assert history.saved is not None
    assert "Bearer" not in str(history.saved)
    assert "secret-token" not in str(history.saved)


def test_openai_compatible_assistant_planner_uses_existing_ai_provider_settings() -> None:
    captured: dict[str, object] = {}

    def fake_post_json(url: str, body: dict[str, object], headers: dict[str, str], timeout: float) -> dict[str, object]:
        captured["url"] = url
        captured["body"] = body
        captured["headers"] = headers
        captured["timeout"] = timeout
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"tool_name":"generate_daily_report","arguments":{}}',
                    }
                }
            ]
        }

    planner = OpenAiCompatibleAssistantPlanner(
        api_base_url="https://llm.example/v1",
        api_key="secret-key",
        model="serviceops-router",
        post_json=fake_post_json,
    )

    plan = planner.plan("сколько всего получено заявок на ремонт? token ABCDEF12345 телефон +7 999 100-00-01 email admin@coffeefix.local")

    assert plan == {"tool_name": "generate_daily_report", "policy": "read_only", "arguments": {}}
    assert captured["url"] == "https://llm.example/v1/chat/completions"
    assert captured["headers"] == {"Authorization": "Bearer secret-key", "Content-Type": "application/json"}
    assert captured["timeout"] == 20.0
    assert "generate_daily_report" in str(captured["body"])
    assert "сколько всего получено заявок" in str(captured["body"])
    assert "ABCDEF12345" not in str(captured["body"])
    assert "+7 999 100-00-01" not in str(captured["body"])
    assert "admin@coffeefix.local" not in str(captured["body"])
    assert "[credential redacted]" in str(captured["body"])
    assert "[phone redacted]" in str(captured["body"])
    assert "[email redacted]" in str(captured["body"])


def test_assistant_planner_factory_follows_ai_provider_settings() -> None:
    deterministic = create_assistant_planner(Settings(ai_provider="deterministic"))
    live = create_assistant_planner(
        Settings(
            ai_provider="openai-compatible",
            ai_api_key="secret-key",
            ai_model="serviceops-router",
            ai_api_base_url="https://llm.example/v1",
        )
    )

    assert deterministic is None
    assert isinstance(live, OpenAiCompatibleAssistantPlanner)


def test_assistant_mutating_tool_requires_confirmation_before_purchase_draft_creation() -> None:
    async def scenario() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository = create_repositories()
        supplier = CreateSupplier(inventory_repository, actor="inventory@coffeefix.local").execute(
            SupplierPayload(name="Parts Partner", phone="+100")
        )
        part = CreatePart(inventory_repository).execute(
            CreatePartPayload(sku="PUMP-ULKA", name="Ulka pump", unit="pcs")
        )
        app = build_app(service_repository, knowledge_repository, inventory_repository, staff_repository, profile_repository)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            token = await login(client, "inventory@coffeefix.local")
            preview = await post_assistant(
                client,
                token,
                f"Создай черновик закупки supplier {supplier.supplier_id} part {part.part_id} qty 2",
            )
            before_confirm = await client.get(
                "/inventory/procurement/purchase-requests",
                headers={"Authorization": f"Bearer {token}"},
            )
            confirmed = await client.post(
                f"/assistant/runs/{preview.json()['run_id']}/confirm",
                headers={"Authorization": f"Bearer {token}"},
            )
            replay = await client.post(
                f"/assistant/runs/{preview.json()['run_id']}/confirm",
                headers={"Authorization": f"Bearer {token}"},
            )
            after_confirm = await client.get(
                "/inventory/procurement/purchase-requests",
                headers={"Authorization": f"Bearer {token}"},
            )
        return preview.json(), before_confirm.json(), {
            "confirmed": confirmed.json(),
            "replay": replay.json(),
            "after": after_confirm.json(),
        }

    preview, before_confirm, after = asyncio.run(scenario())

    assert preview["status"] == "confirmation_required"
    assert preview["tool_calls"][0]["tool_name"] == "create_purchase_request_draft"
    assert preview["tool_calls"][0]["policy"] == "requires_confirmation"
    assert before_confirm["items"] == []
    assert after["confirmed"]["status"] == "completed"
    assert after["confirmed"]["tool_calls"][0]["status"] == "completed"
    assert after["replay"]["detail"] == "Assistant run does not require confirmation"
    assert after["after"]["items"][0]["status"] == "draft"
    assert after["after"]["items"][0]["items"][0]["quantity"] == 2
    assert len(after["after"]["items"]) == 1


def test_assistant_confirmation_finalization_failure_marks_run_failed() -> None:
    class FailingFinalizationHistory:
        marked_failed = False

        def claim_run_for_confirmation(self, run_id: int, actor_username: str) -> dict[str, object]:
            assert run_id == 42
            assert actor_username == "inventory@coffeefix.local"
            return {
                "run_id": run_id,
                "actor_username": actor_username,
                "safe_message": "tool=create_purchase_request_draft; numeric_ids=1,2,3",
                "status": "executing",
                "assistant_message": "create_purchase_request_draft requires staff confirmation before changing ServiceOps data.",
                "created_at": "2026-06-17T12:05:00+00:00",
                "updated_at": "2026-06-17T12:05:00+00:00",
                "tool_calls": [
                    {
                        "tool_call_id": 10,
                        "tool_name": "create_purchase_request_draft",
                        "policy": "requires_confirmation",
                        "status": "executing",
                        "arguments": {"supplier_id": 1, "part_id": 2, "quantity": 3},
                        "result_summary": "Confirmation required before creating a draft purchase request.",
                        "result_refs": [],
                        "created_at": "2026-06-17T12:05:00+00:00",
                        "updated_at": "2026-06-17T12:05:00+00:00",
                    }
                ],
            }

        def update_run_after_confirmation(self, **kwargs: object) -> dict[str, object]:
            raise RuntimeError("database write failed")

        def mark_run_failed(self, run_id: int, actor_username: str, result_summary: str) -> dict[str, object]:
            assert "history finalization failed" in result_summary
            assert "Check procurement records before retrying" in result_summary
            self.marked_failed = True
            return {
                "run_id": run_id,
                "actor_username": actor_username,
                "safe_message": "tool=create_purchase_request_draft; numeric_ids=1,2,3",
                "status": "failed",
                "assistant_message": "Assistant tool request failed.",
                "created_at": "2026-06-17T12:05:00+00:00",
                "updated_at": "2026-06-17T12:06:00+00:00",
                "tool_calls": [
                    {
                        "tool_call_id": 10,
                        "tool_name": "create_purchase_request_draft",
                        "policy": "requires_confirmation",
                        "status": "failed",
                        "arguments": {"supplier_id": 1, "part_id": 2, "quantity": 3},
                        "result_summary": result_summary,
                        "result_refs": [],
                        "created_at": "2026-06-17T12:05:00+00:00",
                        "updated_at": "2026-06-17T12:06:00+00:00",
                    }
                ],
            }

    class CompletedToolRegistry:
        def execute(self, tool_name: str, arguments: dict[str, object], staff: object) -> dict[str, object]:
            assert tool_name == "create_purchase_request_draft"
            assert arguments == {"supplier_id": 1, "part_id": 2, "quantity": 3}
            return {
                "tool_name": tool_name,
                "policy": "requires_confirmation",
                "status": "completed",
                "arguments": arguments,
                "result_summary": "Draft purchase request 9 created for Parts Partner.",
                "result_refs": [],
            }

    history = FailingFinalizationHistory()
    staff = type("Staff", (), {"username": "inventory@coffeefix.local", "roles": ["inventory"]})()

    response = ConfirmStaffAssistantTool(history, CompletedToolRegistry()).execute(42, staff)  # type: ignore[arg-type]

    assert history.marked_failed
    assert response.status == "failed"
    assert response.tool_calls[0].status == "failed"
    assert "history finalization failed" in response.tool_calls[0].result_summary


def test_ai_assistant_migration_contract() -> None:
    migration_sql = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "serviceops_api"
        / "migrations"
        / "0015_ai_assistant_runs.sql"
    ).read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS ai_assistant_runs" in migration_sql
    assert "safe_message" in migration_sql
    assert "raw_provider_body" not in migration_sql
    assert "CREATE TABLE IF NOT EXISTS ai_assistant_tool_calls" in migration_sql
    assert "requires_confirmation" in migration_sql
