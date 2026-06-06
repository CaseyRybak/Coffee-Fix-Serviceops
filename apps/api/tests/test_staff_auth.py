import asyncio

import httpx

from serviceops_api.main import create_app
from serviceops_api.service_requests.repository import ServiceRequestRepository


def payload() -> dict[str, object]:
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


async def post_json(
    repository: ServiceRequestRepository,
    path: str,
    body: dict[str, object],
    token: str | None = None,
) -> httpx.Response:
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


async def login(repository: ServiceRequestRepository, username: str, password: str) -> httpx.Response:
    return await post_json(repository, "/staff/login", {"username": username, "password": password})


async def create_request(repository: ServiceRequestRepository) -> str:
    response = await post_json(repository, "/service-requests", payload())
    assert response.status_code == 201
    return str(response.json()["request_number"])


def test_staff_login_returns_token_for_dev_dispatcher_user() -> None:
    repository = ServiceRequestRepository.in_memory()

    response = asyncio.run(login(repository, "dispatcher@coffeefix.local", "dispatcher-local"))

    assert response.status_code == 200
    body = response.json()
    assert body["staff"] == {
        "username": "dispatcher@coffeefix.local",
        "roles": ["dispatcher"],
    }
    assert body["access_token"]
    assert body["token_type"] == "bearer"


def test_staff_login_rejects_bad_password() -> None:
    repository = ServiceRequestRepository.in_memory()

    response = asyncio.run(login(repository, "dispatcher@coffeefix.local", "wrong"))

    assert response.status_code == 401


def test_dispatcher_api_requires_staff_token() -> None:
    repository = ServiceRequestRepository.in_memory()
    asyncio.run(create_request(repository))

    response = asyncio.run(get_json(repository, "/dispatcher/service-requests"))

    assert response.status_code == 401


def test_dispatcher_role_can_access_dispatcher_api() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository))
    login_response = asyncio.run(login(repository, "dispatcher@coffeefix.local", "dispatcher-local"))
    token = str(login_response.json()["access_token"])

    response = asyncio.run(get_json(repository, "/dispatcher/service-requests", token=token))

    assert response.status_code == 200
    assert response.json()["items"][0]["request_number"] == request_number


def test_wrong_staff_role_cannot_access_dispatcher_api() -> None:
    repository = ServiceRequestRepository.in_memory()
    asyncio.run(create_request(repository))
    login_response = asyncio.run(login(repository, "technician@coffeefix.local", "technician-local"))
    token = str(login_response.json()["access_token"])

    response = asyncio.run(get_json(repository, "/dispatcher/service-requests", token=token))

    assert response.status_code == 403
