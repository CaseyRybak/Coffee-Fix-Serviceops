import httpx
import pytest

from serviceops_api.main import create_app


@pytest.mark.anyio
async def test_health_returns_service_status() -> None:
    transport = httpx.ASGITransport(app=create_app())

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "serviceops-api",
        "status": "healthy",
        "environment": "local",
        "dependencies": {
            "postgres": "configured",
            "redis": "configured",
        },
    }
