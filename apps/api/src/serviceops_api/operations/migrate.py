from __future__ import annotations

import json

from serviceops_api.ai_agents.repository import create_ai_suggestion_repository
from serviceops_api.config import Settings, get_settings
from serviceops_api.inventory.repository import create_inventory_repository
from serviceops_api.knowledge_base.repository import create_knowledge_base_repository
from serviceops_api.notifications.repository import create_notification_repository
from serviceops_api.service_requests.repository import create_service_request_repository
from serviceops_api.staff_management.repository import create_staff_account_repository


def run_migrations(settings: Settings | None = None) -> dict[str, str]:
    resolved_settings = settings or get_settings()
    database_url = resolved_settings.database_url.strip()
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        raise RuntimeError("Production migrations require PostgreSQL")

    create_service_request_repository(resolved_settings, initialize=True)
    create_knowledge_base_repository(resolved_settings, initialize=True)
    create_ai_suggestion_repository(resolved_settings, initialize=True)
    create_inventory_repository(resolved_settings, initialize=True)
    create_staff_account_repository(resolved_settings, initialize=True)
    create_notification_repository(resolved_settings, initialize=True)
    return {"status": "ok", "database": "postgres"}


def main() -> None:
    print(json.dumps(run_migrations(), sort_keys=True))


if __name__ == "__main__":
    main()
