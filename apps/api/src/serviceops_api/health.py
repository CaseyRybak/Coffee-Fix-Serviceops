from pydantic import BaseModel

from serviceops_api.config import Settings


class DependencyStatus(BaseModel):
    postgres: str
    redis: str


class HealthStatus(BaseModel):
    service: str
    status: str
    environment: str
    dependencies: DependencyStatus


def build_health_status(settings: Settings) -> HealthStatus:
    return HealthStatus(
        service=settings.service_name,
        status="healthy",
        environment=settings.environment,
        dependencies=DependencyStatus(
            postgres="configured",
            redis="configured",
        ),
    )

