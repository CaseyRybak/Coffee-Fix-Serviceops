import asyncio

import httpx

from serviceops_api.main import create_app
from serviceops_api.service_requests.repository import ServiceRequestRepository


def valid_payload() -> dict[str, object]:
    return {
        "customer": {
            "name": "Anna Petrova",
            "phone": "+7 999 111-22-33",
            "telegram": "@anna_fix",
            "client_type": "coffee_shop",
        },
        "machine": {
            "brand": "Jura",
            "model": "E8",
            "location_type": "coffee_shop",
        },
        "problem": "Machine leaks water under the brew group.",
        "address": "Tverskaya district",
        "urgency": "today",
    }


async def create_request(repository: ServiceRequestRepository) -> str:
    app = create_app(service_request_repository=repository)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/service-requests", json=valid_payload())

    assert response.status_code == 201
    return str(response.json()["request_number"])


async def get_json(repository: ServiceRequestRepository, path: str) -> httpx.Response:
    app = create_app(service_request_repository=repository)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path)


async def post_json(repository: ServiceRequestRepository, path: str, payload: dict[str, object]) -> httpx.Response:
    app = create_app(service_request_repository=repository)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(path, json=payload)


def test_public_status_returns_timeline_clarification_and_safe_customer_snapshot() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository))
    repository.add_status_event(
        request_number=request_number,
        status="needs_clarification",
        title="Нужно уточнить симптомы",
        description="Диспетчер попросил фото ошибки на дисплее.",
        actor="dispatcher",
    )
    repository.ask_clarification(
        request_number=request_number,
        question="Пришлите, пожалуйста, код ошибки на дисплее.",
    )

    response = asyncio.run(get_json(repository, f"/service-requests/{request_number}/status"))

    assert response.status_code == 200
    body = response.json()
    assert body["request_number"] == request_number
    assert body["status"] == "needs_clarification"
    assert body["customer"] == {
        "name": "Anna Petrova",
        "phone_masked": "+7 999 ***-**-33",
        "telegram": "@anna_fix",
    }
    assert body["machine"] == {"brand": "Jura", "model": "E8"}
    assert body["problem_summary"] == "Machine leaks water under the brew group."
    assert body["timeline"][0]["status"] == "new"
    assert body["timeline"][0]["title"] == "Заявка создана"
    assert body["timeline"][1]["status"] == "needs_clarification"
    assert body["clarification"] == {
        "question_id": body["clarification"]["question_id"],
        "question": "Пришлите, пожалуйста, код ошибки на дисплее.",
        "answer": None,
        "answered_at": None,
    }
    assert body["telegram_opt_in"]["enabled"] is False
    assert body["telegram_opt_in"]["link"].endswith(f"/service-requests/{request_number}/telegram-opt-in")
    assert body["public_token"]


def test_status_can_be_opened_by_public_token() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository))
    token = repository.ensure_public_access_token(request_number)

    response = asyncio.run(get_json(repository, f"/status/{token}"))

    assert response.status_code == 200
    assert response.json()["request_number"] == request_number


def test_customer_answer_is_recorded_and_added_to_timeline() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository))
    question_id = repository.ask_clarification(
        request_number=request_number,
        question="Когда кофемашина последний раз проходила декальцинацию?",
    )

    response = asyncio.run(
        post_json(
            repository,
            f"/service-requests/{request_number}/answers",
            {"question_id": question_id, "answer": "Около трех месяцев назад."},
        )
    )

    assert response.status_code == 200
    assert response.json() == {
        "request_number": request_number,
        "status": "needs_clarification",
        "message": "Customer answer recorded",
    }

    status_response = asyncio.run(get_json(repository, f"/service-requests/{request_number}/status"))
    body = status_response.json()
    assert body["clarification"]["answer"] == "Около трех месяцев назад."
    assert body["timeline"][-1]["title"] == "Клиент ответил на уточнение"


def test_asking_clarification_adds_visible_timeline_event() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository))

    repository.ask_clarification(
        request_number=request_number,
        question="Пришлите фото шильдика с моделью кофемашины.",
    )

    status_response = asyncio.run(get_json(repository, f"/service-requests/{request_number}/status"))
    body = status_response.json()
    assert body["status"] == "needs_clarification"
    assert body["timeline"][-1]["status"] == "needs_clarification"
    assert body["timeline"][-1]["title"] == "Нужно уточнить детали"
    assert body["timeline"][-1]["actor"] == "dispatcher"


def test_telegram_opt_in_returns_token_and_link_contract() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository))

    response = asyncio.run(
        post_json(
            repository,
            f"/service-requests/{request_number}/telegram-opt-in",
            {"telegram": "@anna_fix"},
        )
    )

    assert response.status_code == 200
    body = response.json()
    assert body["request_number"] == request_number
    assert body["telegram"] == "@anna_fix"
    assert body["token"]
    assert body["link"].endswith(f"?start={body['token']}")


def test_telegram_opt_in_token_can_be_linked_to_chat_for_bot_confirmation() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository))
    opt_in = asyncio.run(
        post_json(
            repository,
            f"/service-requests/{request_number}/telegram-opt-in",
            {"telegram": "@anna_fix"},
        )
    ).json()

    app = create_app(
        service_request_repository=repository,
        telegram_bot_api_secret="bot-secret",
    )
    transport = httpx.ASGITransport(app=app)

    async def link_chat() -> httpx.Response:
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.post(
                f"/notifications/telegram/opt-ins/{opt_in['token']}/link",
                json={"chat_id": 123456789, "username": "anna_fix"},
                headers={"X-ServiceOps-Telegram-Bot-Secret": "bot-secret"},
            )

    response = asyncio.run(link_chat())

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "request_number": request_number,
        "status": "new",
        "customer_name": "Anna Petrova",
        "machine_label": "Jura E8",
        "public_status_url": body["public_status_url"],
        "message": "Telegram notifications linked",
    }
    assert repository.get_request_snapshot(request_number)["customer"]["telegram_chat_id"] == "123456789"
