import asyncio
import re

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
        "attachment_metadata": [
            {
                "filename": "leak.jpg",
                "content_type": "image/jpeg",
                "size_bytes": 34822,
            }
        ],
    }


async def post_service_request(repository: ServiceRequestRepository, payload: dict[str, object]) -> httpx.Response:
    app = create_app(service_request_repository=repository)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post("/service-requests", json=payload)


async def options_service_request(repository: ServiceRequestRepository) -> httpx.Response:
    app = create_app(service_request_repository=repository)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.options(
            "/service-requests",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )


def test_create_service_request_persists_intake_data() -> None:
    repository = ServiceRequestRepository.in_memory()

    response = asyncio.run(post_service_request(repository, valid_payload()))

    assert response.status_code == 201
    body = response.json()
    assert body == {
        "request_number": body["request_number"],
        "status": "new",
        "message": "Service request created",
    }
    assert body["request_number"].startswith("CFX-")
    assert re.fullmatch(r"CFX-\d{8}-\d{6}", body["request_number"])

    stored = repository.get_request_snapshot(body["request_number"])
    assert stored == {
        "request": {
            "request_number": body["request_number"],
            "status": "new",
            "problem": "Machine leaks water under the brew group.",
            "address": "Tverskaya district",
            "urgency": "today",
        },
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
        "attachments": [
            {
                "filename": "leak.jpg",
                "content_type": "image/jpeg",
                "size_bytes": 34822,
            }
        ],
    }


def test_create_service_request_allows_optional_telegram_and_attachments() -> None:
    repository = ServiceRequestRepository.in_memory()
    payload = valid_payload()
    payload["customer"] = {
        "name": "Ivan Ivanov",
        "phone": "+7 999 444-55-66",
        "client_type": "private",
    }
    payload.pop("attachment_metadata")

    response = asyncio.run(post_service_request(repository, payload))

    assert response.status_code == 201
    stored = repository.get_request_snapshot(response.json()["request_number"])
    assert stored["customer"]["telegram"] is None
    assert stored["attachments"] == []


def test_create_service_request_rejects_missing_required_fields() -> None:
    repository = ServiceRequestRepository.in_memory()

    response = asyncio.run(
        post_service_request(
            repository,
            {
                "customer": {
                    "name": "",
                    "phone": "",
                    "client_type": "private",
                },
                "machine": {
                    "brand": "",
                    "location_type": "home",
                },
                "problem": "",
                "address": "",
                "urgency": "today",
            },
        )
    )

    assert response.status_code == 422


def test_service_request_route_allows_local_web_origin_preflight() -> None:
    repository = ServiceRequestRepository.in_memory()

    response = asyncio.run(options_service_request(repository))

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
