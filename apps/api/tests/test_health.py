from serviceops_api.config import Settings
from serviceops_api.health import build_health_status
from serviceops_api.main import create_app


def test_health_route_returns_service_status() -> None:
    app = create_app()

    route = next(route for route in app.routes if route.path == "/health")
    status = route.endpoint()

    assert status.model_dump() == {
        "service": "serviceops-api",
        "status": "healthy",
        "environment": "local",
        "dependencies": {
            "postgres": "configured",
            "redis": "configured",
        },
    }


def test_health_status_returns_service_contract() -> None:
    status = build_health_status(Settings())

    assert status.model_dump() == {
        "service": "serviceops-api",
        "status": "healthy",
        "environment": "local",
        "dependencies": {
            "postgres": "configured",
            "redis": "configured",
        },
    }
