import asyncio

import httpx

from serviceops_api.main import create_app
from serviceops_api.service_requests.repository import ServiceRequestRepository
from serviceops_api.staff_auth import hash_staff_password
from serviceops_api.staff_management.models import CreateStaffAccountPayload
from serviceops_api.staff_management.repository import SqliteStaffAccountRepository
from serviceops_api.technicians.repository import SqliteTechnicianProfileRepository


def request_payload(*, brand: str = "Jura", address: str = "Tverskaya district") -> dict[str, object]:
    return {
        "customer": {
            "name": "Anna Petrova",
            "phone": "+7 999 111-22-33",
            "telegram": "@anna_fix",
            "client_type": "coffee_shop",
        },
        "machine": {
            "brand": brand,
            "model": "E8",
            "location_type": "coffee_shop",
        },
        "problem": "Machine leaks water under the brew group.",
        "address": address,
        "urgency": "today",
    }


async def post_json(
    service_repository: ServiceRequestRepository,
    staff_repository: SqliteStaffAccountRepository,
    profile_repository: SqliteTechnicianProfileRepository,
    path: str,
    body: dict[str, object],
    token: str | None = None,
) -> httpx.Response:
    app = create_app(
        service_request_repository=service_repository,
        staff_account_repository=staff_repository,
        technician_profile_repository=profile_repository,
    )
    headers = {"Authorization": f"Bearer {token}"} if token else None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(path, json=body, headers=headers)


async def get_json(
    service_repository: ServiceRequestRepository,
    staff_repository: SqliteStaffAccountRepository,
    profile_repository: SqliteTechnicianProfileRepository,
    path: str,
    token: str | None = None,
) -> httpx.Response:
    app = create_app(
        service_request_repository=service_repository,
        staff_account_repository=staff_repository,
        technician_profile_repository=profile_repository,
    )
    headers = {"Authorization": f"Bearer {token}"} if token else None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path, headers=headers)


def create_staff(
    repository: SqliteStaffAccountRepository,
    username: str,
    roles: list[str],
    *,
    first_name: str = "Test",
    last_name: str = "User",
    phone: str = "+7 999 000-00-00",
    password: str = "temporary-pass-1",
) -> None:
    repository.create_account(
        CreateStaffAccountPayload(
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            password=password,
            roles=roles,  # type: ignore[arg-type]
        ),
        password_hash=hash_staff_password(password),
        actor="system",
    )


async def login(
    service_repository: ServiceRequestRepository,
    staff_repository: SqliteStaffAccountRepository,
    profile_repository: SqliteTechnicianProfileRepository,
    username: str,
    password: str = "temporary-pass-1",
) -> str:
    response = await post_json(
        service_repository,
        staff_repository,
        profile_repository,
        "/staff/login",
        {"username": username, "password": password},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


async def create_request(
    service_repository: ServiceRequestRepository,
    staff_repository: SqliteStaffAccountRepository,
    profile_repository: SqliteTechnicianProfileRepository,
    *,
    brand: str = "Jura",
    address: str = "Tverskaya district",
) -> str:
    response = await post_json(
        service_repository,
        staff_repository,
        profile_repository,
        "/service-requests",
        request_payload(brand=brand, address=address),
    )
    assert response.status_code == 201
    return str(response.json()["request_number"])


def repositories() -> tuple[ServiceRequestRepository, SqliteStaffAccountRepository, SqliteTechnicianProfileRepository]:
    return (
        ServiceRequestRepository.in_memory(),
        SqliteStaffAccountRepository.in_memory(),
        SqliteTechnicianProfileRepository.in_memory(),
    )


def test_admin_can_upsert_and_list_technician_profiles() -> None:
    service_repository, staff_repository, profile_repository = repositories()
    create_staff(staff_repository, "admin@coffeefix.local", ["admin"], first_name="Admin", last_name="User")
    create_staff(
        staff_repository,
        "pavel@coffeefix.local",
        ["technician"],
        first_name="Pavel",
        last_name="Sokolov",
        phone="+7 999 111-22-33",
    )
    admin_token = asyncio.run(login(service_repository, staff_repository, profile_repository, "admin@coffeefix.local"))

    upsert_response = asyncio.run(
        post_json(
            service_repository,
            staff_repository,
            profile_repository,
            "/admin/technician-profiles/pavel%40coffeefix.local",
            {
                "active": True,
                "skill_brands": [" Jura ", "jura", "Rocket"],
                "service_regions": ["Tverskaya", "ЦАО"],
                "notes": "Senior espresso machines specialist.",
            },
            token=admin_token,
        )
    )
    list_response = asyncio.run(
        get_json(service_repository, staff_repository, profile_repository, "/admin/technician-profiles", token=admin_token)
    )

    assert upsert_response.status_code == 200
    assert upsert_response.json()["staff_username"] == "pavel@coffeefix.local"
    assert upsert_response.json()["display_name"] == "Pavel Sokolov"
    assert upsert_response.json()["skill_brands"] == ["Jura", "Rocket"]
    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["service_regions"] == ["Tverskaya", "ЦАО"]
    audit = staff_repository.list_audit_events()
    assert audit[0]["action"] == "technician_profile.upserted"
    assert "Senior espresso" not in str(audit[0]["metadata"])


def test_technician_profile_routes_require_admin_and_technician_staff_link() -> None:
    service_repository, staff_repository, profile_repository = repositories()
    create_staff(staff_repository, "admin@coffeefix.local", ["admin"], first_name="Admin", last_name="User")
    create_staff(staff_repository, "dispatcher@coffeefix.local", ["dispatcher"], first_name="Dispatcher", last_name="User")
    admin_token = asyncio.run(login(service_repository, staff_repository, profile_repository, "admin@coffeefix.local"))
    dispatcher_token = asyncio.run(login(service_repository, staff_repository, profile_repository, "dispatcher@coffeefix.local"))

    unauthenticated = asyncio.run(
        get_json(service_repository, staff_repository, profile_repository, "/admin/technician-profiles")
    )
    wrong_role = asyncio.run(
        get_json(
            service_repository,
            staff_repository,
            profile_repository,
            "/admin/technician-profiles",
            token=dispatcher_token,
        )
    )
    non_technician = asyncio.run(
        post_json(
            service_repository,
            staff_repository,
            profile_repository,
            "/admin/technician-profiles/dispatcher%40coffeefix.local",
            {"active": True, "skill_brands": ["Jura"], "service_regions": ["Tverskaya"]},
            token=admin_token,
        )
    )
    missing = asyncio.run(
        post_json(
            service_repository,
            staff_repository,
            profile_repository,
            "/admin/technician-profiles/missing%40coffeefix.local",
            {"active": True, "skill_brands": ["Jura"], "service_regions": ["Tverskaya"]},
            token=admin_token,
        )
    )

    assert unauthenticated.status_code == 401
    assert wrong_role.status_code == 403
    assert non_technician.status_code == 400
    assert non_technician.json()["detail"] == "Staff account must have technician role"
    assert missing.status_code == 404


def test_dispatcher_gets_explainable_technician_recommendations() -> None:
    service_repository, staff_repository, profile_repository = repositories()
    create_staff(staff_repository, "dispatcher@coffeefix.local", ["dispatcher"], first_name="Dispatcher", last_name="User")
    create_staff(staff_repository, "pavel@coffeefix.local", ["technician"], first_name="Pavel", last_name="Sokolov")
    create_staff(staff_repository, "sergey@coffeefix.local", ["technician"], first_name="Sergey", last_name="Morozov")
    create_staff(staff_repository, "inactive@coffeefix.local", ["technician"], first_name="Inactive", last_name="Tech")
    profile_repository.upsert_profile(
        "pavel@coffeefix.local",
        active=True,
        skill_brands=["Jura"],
        service_regions=["Tverskaya"],
        notes=None,
    )
    profile_repository.upsert_profile(
        "sergey@coffeefix.local",
        active=True,
        skill_brands=["Rocket"],
        service_regions=["ЦАО"],
        notes=None,
    )
    profile_repository.upsert_profile(
        "inactive@coffeefix.local",
        active=False,
        skill_brands=["Jura"],
        service_regions=["Tverskaya"],
        notes=None,
    )
    request_number = asyncio.run(
        create_request(service_repository, staff_repository, profile_repository, brand="Jura", address="Tverskaya district")
    )
    dispatcher_token = asyncio.run(
        login(service_repository, staff_repository, profile_repository, "dispatcher@coffeefix.local")
    )

    response = asyncio.run(
        get_json(
            service_repository,
            staff_repository,
            profile_repository,
            f"/dispatcher/service-requests/{request_number}/technician-recommendations",
            token=dispatcher_token,
        )
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["staff_username"] for item in items] == [
        "pavel@coffeefix.local",
        "sergey@coffeefix.local",
        "inactive@coffeefix.local",
    ]
    assert "Brand match: Jura" in items[0]["reasons"]
    assert "Region match: Tverskaya" in items[0]["reasons"]
    assert "Brand mismatch: request Jura" in items[1]["risks"]
    assert "Profile is inactive" in items[2]["risks"]
    assert response.json()["request"]["brand"] == "Jura"


def test_technician_recommendation_route_requires_dispatcher_role() -> None:
    service_repository, staff_repository, profile_repository = repositories()
    create_staff(staff_repository, "admin@coffeefix.local", ["admin"], first_name="Admin", last_name="User")
    create_staff(staff_repository, "technician@coffeefix.local", ["technician"], first_name="Tech", last_name="User")
    request_number = asyncio.run(create_request(service_repository, staff_repository, profile_repository))
    admin_token = asyncio.run(login(service_repository, staff_repository, profile_repository, "admin@coffeefix.local"))
    technician_token = asyncio.run(
        login(service_repository, staff_repository, profile_repository, "technician@coffeefix.local")
    )

    unauthenticated = asyncio.run(
        get_json(
            service_repository,
            staff_repository,
            profile_repository,
            f"/dispatcher/service-requests/{request_number}/technician-recommendations",
        )
    )
    admin_response = asyncio.run(
        get_json(
            service_repository,
            staff_repository,
            profile_repository,
            f"/dispatcher/service-requests/{request_number}/technician-recommendations",
            token=admin_token,
        )
    )
    technician_response = asyncio.run(
        get_json(
            service_repository,
            staff_repository,
            profile_repository,
            f"/dispatcher/service-requests/{request_number}/technician-recommendations",
            token=technician_token,
        )
    )

    assert unauthenticated.status_code == 401
    assert admin_response.status_code == 403
    assert technician_response.status_code == 403


def test_recommendations_keep_inactive_staff_visible_but_below_active_technicians() -> None:
    service_repository, staff_repository, profile_repository = repositories()
    create_staff(staff_repository, "dispatcher@coffeefix.local", ["dispatcher"], first_name="Dispatcher", last_name="User")
    create_staff(staff_repository, "inactive@coffeefix.local", ["technician"], first_name="Inactive", last_name="Expert")
    create_staff(staff_repository, "active@coffeefix.local", ["technician"], first_name="Active", last_name="Generalist")
    profile_repository.upsert_profile(
        "inactive@coffeefix.local",
        active=True,
        skill_brands=["Jura"],
        service_regions=["Tverskaya"],
        notes=None,
    )
    profile_repository.upsert_profile(
        "active@coffeefix.local",
        active=True,
        skill_brands=["Rocket"],
        service_regions=["North"],
        notes=None,
    )
    staff_repository.set_active("inactive@coffeefix.local", False, actor="admin@coffeefix.local")
    request_number = asyncio.run(
        create_request(service_repository, staff_repository, profile_repository, brand="Jura", address="Tverskaya district")
    )
    dispatcher_token = asyncio.run(
        login(service_repository, staff_repository, profile_repository, "dispatcher@coffeefix.local")
    )

    response = asyncio.run(
        get_json(
            service_repository,
            staff_repository,
            profile_repository,
            f"/dispatcher/service-requests/{request_number}/technician-recommendations",
            token=dispatcher_token,
        )
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["staff_username"] for item in items] == [
        "active@coffeefix.local",
        "inactive@coffeefix.local",
    ]
    assert "Staff account is inactive" in items[1]["risks"]


def test_recommendations_include_schedule_conflict_risk_without_mutating_assignment() -> None:
    service_repository, staff_repository, profile_repository = repositories()
    create_staff(staff_repository, "dispatcher@coffeefix.local", ["dispatcher"], first_name="Dispatcher", last_name="User")
    create_staff(staff_repository, "pavel@coffeefix.local", ["technician"], first_name="Pavel", last_name="Sokolov")
    profile_repository.upsert_profile(
        "pavel@coffeefix.local",
        active=True,
        skill_brands=["Jura"],
        service_regions=["Tverskaya"],
        notes=None,
    )
    first_request = asyncio.run(create_request(service_repository, staff_repository, profile_repository))
    second_request = asyncio.run(create_request(service_repository, staff_repository, profile_repository))
    dispatcher_token = asyncio.run(
        login(service_repository, staff_repository, profile_repository, "dispatcher@coffeefix.local")
    )
    appointment = asyncio.run(
        post_json(
            service_repository,
            staff_repository,
            profile_repository,
            f"/dispatcher/service-requests/{first_request}/appointments",
            {
                "technician_identifier": "pavel@coffeefix.local",
                "starts_at": "2026-06-19T10:00:00+03:00",
                "ends_at": "2026-06-19T12:00:00+03:00",
                "window_label": "19 июня 10:00-12:00",
            },
            token=dispatcher_token,
        )
    )

    response = asyncio.run(
        get_json(
            service_repository,
            staff_repository,
            profile_repository,
            (
                f"/dispatcher/service-requests/{second_request}/technician-recommendations"
                "?starts_at=2026-06-19T11%3A00%3A00%2B03%3A00&ends_at=2026-06-19T13%3A00%3A00%2B03%3A00"
            ),
            token=dispatcher_token,
        )
    )
    detail = asyncio.run(
        get_json(
            service_repository,
            staff_repository,
            profile_repository,
            f"/dispatcher/service-requests/{second_request}",
            token=dispatcher_token,
        )
    ).json()

    assert appointment.status_code == 200
    assert response.status_code == 200
    assert response.json()["items"][0]["scheduled_visit_count"] == 1
    assert "Scheduling conflict in requested window" in response.json()["items"][0]["risks"]
    assert detail["assignment"]["technician_name"] is None
    assert detail["appointment"] is None


def test_recommendations_rank_available_technician_above_conflicted_brand_match() -> None:
    service_repository, staff_repository, profile_repository = repositories()
    create_staff(staff_repository, "dispatcher@coffeefix.local", ["dispatcher"], first_name="Dispatcher", last_name="User")
    create_staff(staff_repository, "pavel@coffeefix.local", ["technician"], first_name="Pavel", last_name="Sokolov")
    create_staff(staff_repository, "anna@coffeefix.local", ["technician"], first_name="Anna", last_name="Smirnova")
    profile_repository.upsert_profile(
        "pavel@coffeefix.local",
        active=True,
        skill_brands=["Jura"],
        service_regions=["Tverskaya"],
        notes=None,
    )
    profile_repository.upsert_profile(
        "anna@coffeefix.local",
        active=True,
        skill_brands=["Saeco"],
        service_regions=["North"],
        notes=None,
    )
    first_request = asyncio.run(create_request(service_repository, staff_repository, profile_repository))
    second_request = asyncio.run(create_request(service_repository, staff_repository, profile_repository))
    dispatcher_token = asyncio.run(
        login(service_repository, staff_repository, profile_repository, "dispatcher@coffeefix.local")
    )
    appointment = asyncio.run(
        post_json(
            service_repository,
            staff_repository,
            profile_repository,
            f"/dispatcher/service-requests/{first_request}/appointments",
            {
                "technician_identifier": "pavel@coffeefix.local",
                "starts_at": "2026-06-19T10:00:00+03:00",
                "ends_at": "2026-06-19T12:00:00+03:00",
                "window_label": "19 июня 10:00-12:00",
            },
            token=dispatcher_token,
        )
    )

    response = asyncio.run(
        get_json(
            service_repository,
            staff_repository,
            profile_repository,
            (
                f"/dispatcher/service-requests/{second_request}/technician-recommendations"
                "?starts_at=2026-06-19T11%3A00%3A00%2B03%3A00&ends_at=2026-06-19T13%3A00%3A00%2B03%3A00"
            ),
            token=dispatcher_token,
        )
    )

    assert appointment.status_code == 200
    assert response.status_code == 200
    assert [item["staff_username"] for item in response.json()["items"]] == [
        "anna@coffeefix.local",
        "pavel@coffeefix.local",
    ]
    assert "No scheduling conflict in requested window" in response.json()["items"][0]["reasons"]
    assert "Scheduling conflict in requested window" in response.json()["items"][1]["risks"]


def test_public_status_does_not_expose_technician_profile_or_recommendation_internals() -> None:
    service_repository, staff_repository, profile_repository = repositories()
    create_staff(staff_repository, "dispatcher@coffeefix.local", ["dispatcher"], first_name="Dispatcher", last_name="User")
    create_staff(staff_repository, "pavel@coffeefix.local", ["technician"], first_name="Pavel", last_name="Sokolov")
    profile_repository.upsert_profile(
        "pavel@coffeefix.local",
        active=True,
        skill_brands=["Jura"],
        service_regions=["Tverskaya"],
        notes="Private profile note",
    )
    request_number = asyncio.run(create_request(service_repository, staff_repository, profile_repository))
    dispatcher_token = asyncio.run(
        login(service_repository, staff_repository, profile_repository, "dispatcher@coffeefix.local")
    )
    asyncio.run(
        get_json(
            service_repository,
            staff_repository,
            profile_repository,
            f"/dispatcher/service-requests/{request_number}/technician-recommendations",
            token=dispatcher_token,
        )
    )

    public_status = asyncio.run(
        get_json(
            service_repository,
            staff_repository,
            profile_repository,
            f"/service-requests/{request_number}/status",
        )
    )

    assert public_status.status_code == 200
    public_text = str(public_status.json())
    assert "skill_brands" not in public_text
    assert "service_regions" not in public_text
    assert "Brand match" not in public_text
    assert "Private profile note" not in public_text
