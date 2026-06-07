import asyncio

import httpx

from serviceops_api.ai_agents.models import AiSuggestionCreate
from serviceops_api.ai_agents.repository import SqliteAiSuggestionRepository
from serviceops_api.config import get_settings
from serviceops_api.knowledge_base.repository import SqliteKnowledgeBaseRepository
from serviceops_api.knowledge_base.seed_documents import REPAIR_KNOWLEDGE_SEED_DOCUMENTS
from serviceops_api.main import create_app
from serviceops_api.service_requests.repository import ServiceRequestRepository


def request_payload() -> dict[str, object]:
    return {
        "customer": {
            "name": "Anna Petrova",
            "phone": "+7 999 111-22-33",
            "telegram": "@anna_fix",
            "client_type": "coffee_shop",
        },
        "machine": {
            "brand": "Rocket",
            "model": "Appartamento",
            "location_type": "coffee_shop",
        },
        "problem": "E61 group overheats after descaling.",
        "address": "Tverskaya district",
        "urgency": "today",
    }


def suggestion(kind: str = "diagnostic_question", content: str = "Когда перегревается группа?") -> AiSuggestionCreate:
    return AiSuggestionCreate(
        kind=kind,  # type: ignore[arg-type]
        title="AI suggestion",
        content=content,
        rationale="Диспетчер должен проверить подсказку перед действием.",
        confidence=0.7,
    )


def test_sqlite_ai_suggestion_repository_tracks_lifecycle() -> None:
    repository = SqliteAiSuggestionRepository.in_memory()

    saved = repository.save_suggestions(
        "CFX-20260607-000001",
        [suggestion(), suggestion("customer_reply", "Черновик ответа клиенту.")],
    )
    accepted = repository.mark_accepted(int(saved[0]["suggestion_id"]))
    ignored = repository.mark_ignored(int(saved[1]["suggestion_id"]))
    listed = repository.list_suggestions("CFX-20260607-000001")

    assert [item["suggestion_id"] for item in listed] == [saved[1]["suggestion_id"], saved[0]["suggestion_id"]]
    assert accepted["status"] == "accepted"
    assert ignored["status"] == "ignored"
    assert repository.get_suggestion(int(saved[0]["suggestion_id"]))["status"] == "accepted"


def test_dispatcher_ai_suggestion_lifecycle_accepts_question_and_ignores_draft() -> None:
    async def scenario() -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
        service_repository = ServiceRequestRepository.in_memory()
        knowledge_repository = SqliteKnowledgeBaseRepository.in_memory()
        ai_repository = SqliteAiSuggestionRepository.in_memory()
        app = create_app(
            service_request_repository=service_repository,
            knowledge_base_repository=knowledge_repository,
            ai_suggestion_repository=ai_repository,
        )
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            login = await client.post(
                "/staff/login",
                json={"username": "dispatcher@coffeefix.local", "password": "dispatcher-local"},
            )
            token = str(login.json()["access_token"])
            headers = {"Authorization": f"Bearer {token}"}
            created = await client.post("/service-requests", json=request_payload())
            request_number = str(created.json()["request_number"])
            await client.post(
                "/knowledge-base/documents",
                json=REPAIR_KNOWLEDGE_SEED_DOCUMENTS[0].model_dump(),
            )

            generated = await client.post(
                f"/dispatcher/service-requests/{request_number}/ai-suggestions/generate",
                json={},
                headers=headers,
            )
            listed = await client.get(
                f"/dispatcher/service-requests/{request_number}/ai-suggestions",
                headers=headers,
            )
            diagnostic = next(
                suggestion
                for suggestion in listed.json()["suggestions"]
                if suggestion["kind"] == "diagnostic_question"
            )
            reply = next(
                suggestion
                for suggestion in listed.json()["suggestions"]
                if suggestion["kind"] == "customer_reply"
            )
            accepted = await client.post(
                f"/dispatcher/service-requests/{request_number}/ai-suggestions/{diagnostic['suggestion_id']}/accept-clarification",
                headers=headers,
            )
            ignored = await client.post(
                f"/dispatcher/service-requests/{request_number}/ai-suggestions/{reply['suggestion_id']}/ignore",
                headers=headers,
            )
            public_status = await client.get(f"/service-requests/{request_number}/status")
            detail = await client.get(f"/dispatcher/service-requests/{request_number}", headers=headers)
        return generated.json(), accepted.json(), ignored.json(), {"public": public_status.json(), "detail": detail.json()}

    generated, accepted, ignored, snapshots = asyncio.run(scenario())

    assert len(generated["suggestions"]) == 5
    assert accepted["suggestion"]["status"] == "accepted"
    assert ignored["suggestion"]["status"] == "ignored"
    assert snapshots["public"]["clarification"]["question"] == accepted["suggestion"]["content"]
    assert "ai_suggestions" not in snapshots["public"]
    assert len(snapshots["detail"]["ai_suggestions"]) == 5


def test_ai_suggestion_generation_respects_configured_limit(monkeypatch) -> None:
    monkeypatch.setenv("SERVICEOPS_AI_SUGGESTION_LIMIT", "3")
    get_settings.cache_clear()

    async def scenario() -> dict[str, object]:
        service_repository = ServiceRequestRepository.in_memory()
        app = create_app(
            service_request_repository=service_repository,
            knowledge_base_repository=SqliteKnowledgeBaseRepository.in_memory(),
            ai_suggestion_repository=SqliteAiSuggestionRepository.in_memory(),
        )
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            login = await client.post(
                "/staff/login",
                json={"username": "dispatcher@coffeefix.local", "password": "dispatcher-local"},
            )
            token = str(login.json()["access_token"])
            created = await client.post("/service-requests", json=request_payload())
            request_number = str(created.json()["request_number"])
            generated = await client.post(
                f"/dispatcher/service-requests/{request_number}/ai-suggestions/generate",
                json={},
                headers={"Authorization": f"Bearer {token}"},
            )
        return generated.json()

    try:
        generated = asyncio.run(scenario())
    finally:
        get_settings.cache_clear()

    assert len(generated["suggestions"]) == 3
