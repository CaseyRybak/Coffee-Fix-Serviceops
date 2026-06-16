#!/usr/bin/env python3
"""Validate the repository documentation harness."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    ".gitignore",
    "AGENTS.md",
    "ARCHITECTURE.md",
    "README.md",
    "project_notes.md",
    "package.json",
    "docs/harness/repository-map.md",
    "docs/harness/project-history.md",
    "docs/execution-plans/index.md",
    "docs/review/subagent-review-protocol.md",
    "docs/product/vision.md",
    "docs/product/mvp-scope.md",
    "docs/product/figma-reference-review.md",
    "docs/architecture/harness-engineering.md",
    "docs/architecture/domain-architecture.md",
    "docs/architecture/tech-stack.md",
    "docs/domain-maps/index.md",
    "docs/user-intent/2026-06-05-project-intent.md",
    "docs/execution-plans/detailed/00-repository-harness-implementation.md",
    "docs/execution-plans/detailed/01-foundation-runtime-implementation.md",
    "docs/execution-plans/detailed/02-service-request-intake-implementation.md",
    "docs/execution-plans/detailed/03-client-status-and-notifications-implementation.md",
    "docs/execution-plans/detailed/03a-postgres-persistence-implementation.md",
    "docs/execution-plans/detailed/04-dispatcher-mvp-implementation.md",
    "docs/execution-plans/detailed/05-staff-access-and-roles-implementation.md",
    "docs/execution-plans/detailed/06-knowledge-base-rag-implementation.md",
    "docs/execution-plans/detailed/07-ai-agent-workflows-implementation.md",
    "docs/execution-plans/detailed/08-technician-and-inventory-implementation.md",
    "docs/execution-plans/detailed/09-staff-admin-and-user-management-implementation.md",
    "docs/execution-plans/detailed/10-deployment-and-operations-implementation.md",
    "docs/execution-plans/detailed/11-production-launch-readiness-implementation.md",
    "docs/execution-plans/detailed/12-notification-automation-implementation.md",
    "docs/execution-plans/detailed/13-live-ai-provider-and-knowledge-base-content-implementation.md",
    "docs/execution-plans/detailed/14-operational-hardening-implementation.md",
    "docs/execution-plans/detailed/15-scheduling-depth-implementation.md",
    "docs/execution-plans/detailed/16-inventory-reservations-implementation.md",
    "docs/execution-plans/detailed/README.md",
    "docs/execution-plans/completed/README.md",
    "docker-compose.production.yml",
    "docs/operations/deployment-runbook.md",
    "docs/operations/backup-restore.md",
    "docs/operations/launch-smoke-evidence.md",
    "docs/operations/smoke-tests.md",
    "docs/operations/operational-diagnostics.md",
    "docs/operations/incident-response.md",
    "docs/operations/ai-providers.md",
    "docs/operations/n8n-workflows.md",
    "docs/operations/n8n-workflows/request-created-dispatcher-alert.json",
    "docs/operations/n8n-workflows/status-changed-customer-notification.json",
    "docs/operations/n8n-workflows/clarification-customer-notification.json",
    "docs/operations/n8n-workflows/customer-answered-dispatcher-alert.json",
    "docs/operations/self-hosted-n8n-vps-evidence-2026-06-16.md",
    "tools/operations/postgres_backup.sh",
    "tools/operations/postgres_restore.sh",
    "tools/operations/smoke_test.sh",
    "tools/operations/test_smoke_script_contract.py",
    "docs/review/phase-00-review.md",
    "docs/review/phase-01-review.md",
    "docs/review/phase-02-review.md",
    "docs/review/phase-03-review.md",
    "docs/review/phase-04-review.md",
    "docs/review/phase-05-review.md",
    "docs/review/phase-06-review.md",
    "docs/review/phase-07-review.md",
    "docs/review/phase-08-review.md",
    "docs/review/phase-09-review.md",
    "docs/review/phase-10-review.md",
    "docs/review/phase-11-review.md",
    "docs/review/phase-12-review.md",
    "docs/review/phase-13-review.md",
    "docs/review/phase-14-review.md",
    "docs/review/phase-15-review.md",
    "docs/review/phase-16-review.md",
    "docs/review/documentation-audit-2026-06-07.md",
    "docs/review/documentation-audit-2026-06-10.md",
    "docs/review/documentation-audit-2026-06-15.md",
    "docs/review/documentation-audit-2026-06-15-current-state.md",
    "docs/review/documentation-audit-2026-06-16.md",
    ".env.example",
    "docker-compose.yml",
    "apps/api/Dockerfile",
    "apps/api/pyproject.toml",
    "apps/api/uv.lock",
    "apps/api/src/serviceops_api/main.py",
    "apps/api/src/serviceops_api/ai_agents/api.py",
    "apps/api/src/serviceops_api/ai_agents/models.py",
    "apps/api/src/serviceops_api/ai_agents/prompting.py",
    "apps/api/src/serviceops_api/ai_agents/providers.py",
    "apps/api/src/serviceops_api/ai_agents/repository.py",
    "apps/api/src/serviceops_api/ai_agents/use_cases.py",
    "apps/api/src/serviceops_api/inventory/api.py",
    "apps/api/src/serviceops_api/inventory/models.py",
    "apps/api/src/serviceops_api/inventory/repository.py",
    "apps/api/src/serviceops_api/inventory/use_cases.py",
    "apps/api/src/serviceops_api/staff_auth.py",
    "apps/api/src/serviceops_api/staff_management/api.py",
    "apps/api/src/serviceops_api/staff_management/models.py",
    "apps/api/src/serviceops_api/staff_management/repository.py",
    "apps/api/src/serviceops_api/staff_management/seed_local_staff.py",
    "apps/api/src/serviceops_api/staff_management/use_cases.py",
    "apps/api/src/serviceops_api/operations/bootstrap_admin.py",
    "apps/api/src/serviceops_api/operations/seed_knowledge_base.py",
    "apps/api/src/serviceops_api/technicians/api.py",
    "apps/api/src/serviceops_api/technicians/models.py",
    "apps/api/src/serviceops_api/technicians/use_cases.py",
    "apps/api/src/serviceops_api/knowledge_base/api.py",
    "apps/api/src/serviceops_api/knowledge_base/chunking.py",
    "apps/api/src/serviceops_api/knowledge_base/embeddings.py",
    "apps/api/src/serviceops_api/knowledge_base/evaluation.py",
    "apps/api/src/serviceops_api/knowledge_base/models.py",
    "apps/api/src/serviceops_api/knowledge_base/repository.py",
    "apps/api/src/serviceops_api/knowledge_base/seed_documents.py",
    "apps/api/src/serviceops_api/knowledge_base/use_cases.py",
    "apps/api/src/serviceops_api/notifications/api.py",
    "apps/api/src/serviceops_api/notifications/models.py",
    "apps/api/src/serviceops_api/notifications/n8n.py",
    "apps/api/src/serviceops_api/notifications/repository.py",
    "apps/api/src/serviceops_api/notifications/use_cases.py",
    "apps/api/src/serviceops_api/service_requests/api.py",
    "apps/api/src/serviceops_api/service_requests/models.py",
    "apps/api/src/serviceops_api/service_requests/repository.py",
    "apps/api/src/serviceops_api/service_requests/use_cases.py",
    "apps/api/src/serviceops_api/migrations/0001_service_request_intake.sql",
    "apps/api/src/serviceops_api/migrations/0002_knowledge_base_rag.sql",
    "apps/api/src/serviceops_api/migrations/0003_ai_suggestions.sql",
    "apps/api/src/serviceops_api/migrations/0004_technician_inventory.sql",
    "apps/api/src/serviceops_api/migrations/0005_staff_management.sql",
    "apps/api/src/serviceops_api/migrations/0006_notification_delivery.sql",
    "apps/api/src/serviceops_api/migrations/0007_scheduling_appointments.sql",
    "apps/api/src/serviceops_api/migrations/0008_inventory_reservations.sql",
    "apps/api/src/serviceops_api/migrations/0009_part_compatibility.sql",
    "apps/api/src/serviceops_api/migrations/0010_inventory_russian_catalog.sql",
    "apps/api/src/serviceops_api/migrations/0011_request_number_sequence.sql",
    "apps/api/src/serviceops_api/migrations/0012_staff_profile_fields.sql",
    "apps/api/tests/test_health.py",
    "apps/api/tests/test_ai_agent_prompting.py",
    "apps/api/tests/test_ai_agent_suggestions.py",
    "apps/api/tests/test_knowledge_base_api.py",
    "apps/api/tests/test_knowledge_base_chunking.py",
    "apps/api/tests/test_knowledge_base_seed.py",
    "apps/api/tests/test_live_ai_provider.py",
    "apps/api/tests/test_live_embedding_provider.py",
    "apps/api/tests/test_inventory_parts.py",
    "apps/api/tests/test_technician_workflow.py",
    "apps/api/tests/test_repository_selection.py",
    "apps/api/tests/test_staff_management.py",
    "apps/api/tests/test_operations_bootstrap_admin.py",
    "apps/api/tests/test_operations_seed_knowledge_base.py",
    "apps/api/tests/test_notification_automation.py",
    "apps/api/tests/test_dispatcher_requests.py",
    "apps/api/tests/test_service_request_intake.py",
    "apps/api/tests/test_service_request_status.py",
    "apps/web/Dockerfile",
    "apps/web/package.json",
    "apps/web/package-lock.json",
    "apps/web/src/App.tsx",
    "apps/web/src/App.test.tsx",
    "apps/worker/Dockerfile",
    "apps/worker/pyproject.toml",
    "apps/worker/uv.lock",
    "apps/worker/src/serviceops_worker/celery_app.py",
    "apps/worker/src/serviceops_worker/knowledge_base_tasks.py",
    "apps/worker/tests/test_celery_app.py",
    "apps/worker/tests/test_knowledge_base_tasks.py",
    "apps/telegram-bot/Dockerfile",
    "apps/telegram-bot/pyproject.toml",
    "apps/telegram-bot/uv.lock",
    "apps/telegram-bot/src/serviceops_telegram_bot/main.py",
    "apps/telegram-bot/src/serviceops_telegram_bot/serviceops_client.py",
    "apps/telegram-bot/tests/test_config.py",
    "apps/telegram-bot/tests/test_opt_in_flow.py",
]

REQUIRED_DIRS = [
    "apps/api",
    "apps/web",
    "apps/worker",
    "apps/telegram-bot",
    "packages/shared-kernel",
    "packages/observability",
    "packages/test-harness",
    "tools/agent-context",
    "tools/doc-gardening",
    "tools/repo-checks",
    "docs/execution-plans/completed",
    "docs/execution-plans/detailed",
    "docs/execution-plans/phases",
]

DOMAINS = [
    "ai-agents",
    "billing",
    "customers",
    "inventory",
    "knowledge-base",
    "machines",
    "notifications",
    "scheduling",
    "service-requests",
    "technicians",
]

PHASE_SLICE_MAPS = [
    "00-repository-harness.md",
    "01-foundation-runtime.md",
    "02-service-request-intake.md",
    "03-client-status-and-notifications.md",
    "04-dispatcher-mvp.md",
    "05-staff-access-and-roles.md",
    "06-knowledge-base-rag.md",
    "07-ai-agent-workflows.md",
    "08-technician-and-inventory.md",
    "09-staff-admin-and-user-management.md",
    "10-deployment-and-operations.md",
    "11-production-launch-readiness.md",
    "12-notification-automation.md",
    "13-live-ai-provider-and-knowledge-base-content.md",
    "14-operational-hardening.md",
    "15-scheduling-depth.md",
    "16-inventory-reservations.md",
]

SKILL_DRAFTS = [
    "agent-context-gardening",
    "dokploy-deployment",
    "fastapi-hexagonal-usecase",
    "figma-reference-implementation",
    "n8n-automation-design",
    "rag-knowledge-ingestion",
    "serviceops-domain-modeling",
    "telegram-serviceops-flows",
]

SCAN_ROOTS = [
    "AGENTS.md",
    "ARCHITECTURE.md",
    "README.md",
    "project_notes.md",
    "docs",
    "domains",
]

ENTRY_DOCS = [
    "AGENTS.md",
    "README.md",
    "ARCHITECTURE.md",
    "project_notes.md",
    "docs/harness/project-history.md",
    "docs/harness/repository-map.md",
    "docs/execution-plans/index.md",
]

LOCAL_PATH_PREFIXES = (
    "AGENTS.md",
    "ARCHITECTURE.md",
    "README.md",
    "project_notes.md",
    "docs/",
    "domains/",
    "tools/",
    "apps/",
    "packages/",
    "reference/",
)


def fail(message: str) -> None:
    raise SystemExit(f"documentation harness check failed: {message}")


def require_file(relative_path: str) -> None:
    path = ROOT / relative_path
    if not path.is_file():
        fail(f"missing required file: {relative_path}")


def require_dir(relative_path: str) -> None:
    path = ROOT / relative_path
    if not path.is_dir():
        fail(f"missing required directory: {relative_path}")


def require_text(relative_path: str, expected_text: str) -> None:
    path = ROOT / relative_path
    text = path.read_text(encoding="utf-8")
    if expected_text not in text:
        fail(f"missing expected text in {relative_path}: {expected_text}")


def scan_for_markers() -> None:
    markers = ("TODO", "TBD")
    for root in SCAN_ROOTS:
        path = ROOT / root
        files = [path] if path.is_file() else sorted(path.rglob("*.md"))
        for file_path in files:
            text = file_path.read_text(encoding="utf-8")
            for marker in markers:
                if marker in text:
                    fail(f"{marker} marker found in {file_path.relative_to(ROOT)}")


def path_exists_from_doc(doc_path: Path, target: str) -> bool:
    clean_target = target.split("#", 1)[0]
    if not clean_target:
        return True

    candidates = [
        ROOT / clean_target,
        doc_path.parent / clean_target,
    ]
    return any(candidate.exists() for candidate in candidates)


def validate_local_links() -> None:
    markdown_link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    backtick_pattern = re.compile(r"`([^`]+)`")

    for relative_doc in ENTRY_DOCS:
        doc_path = ROOT / relative_doc
        text = doc_path.read_text(encoding="utf-8")

        for target in markdown_link_pattern.findall(text):
            if target.startswith(("http://", "https://", "#", "mailto:", "tel:")):
                continue
            if not path_exists_from_doc(doc_path, target):
                fail(f"broken markdown link in {relative_doc}: {target}")

        for token in backtick_pattern.findall(text):
            if " " in token or "<" in token or ">" in token:
                continue
            if not token.startswith(LOCAL_PATH_PREFIXES):
                continue
            if not path_exists_from_doc(doc_path, token):
                fail(f"broken local path reference in {relative_doc}: {token}")


def main() -> None:
    for relative_path in REQUIRED_FILES:
        require_file(relative_path)

    for relative_path in REQUIRED_DIRS:
        require_dir(relative_path)

    if (ROOT / "project_nodes.md").exists():
        fail("project_nodes.md should not exist; use project_notes.md")

    for domain in DOMAINS:
        require_dir(f"domains/{domain}/plans")
        require_dir(f"domains/{domain}/decisions")
        require_file(f"domains/{domain}/AGENTS.md")
        require_file(f"domains/{domain}/domain.md")

    for phase in PHASE_SLICE_MAPS:
        require_file(f"docs/execution-plans/phases/{phase}")

    for skill in SKILL_DRAFTS:
        require_file(f"docs/agent-skills/{skill}/SKILL.md")

    require_text("apps/web/Dockerfile", "ARG VITE_SERVICEOPS_API_BASE_URL")
    require_text("docker-compose.yml", "VITE_SERVICEOPS_API_BASE_URL")
    require_text("docker-compose.yml", "127.0.0.1:${SERVICEOPS_API_PORT:-8000}:8000")
    require_text("docker-compose.yml", "127.0.0.1:${SERVICEOPS_WEB_PORT:-3000}:80")
    require_text("docker-compose.yml", "127.0.0.1:${POSTGRES_PORT:-5432}:5432")
    require_text("docker-compose.yml", "127.0.0.1:6379:6379")
    require_text("docker-compose.production.yml", "n8n:")
    require_text("docker-compose.production.yml", "pgvector/pgvector:pg16")
    require_text("docker-compose.production.yml", "SERVICEOPS_STAFF_AUTH_SECRET")
    require_text(".env.example", "SERVICEOPS_BOOTSTRAP_ADMIN_USERNAME")
    require_text(".env.example", "SERVICEOPS_SMOKE_STAFF_USERNAME")
    require_text(".env.example", "SERVICEOPS_PUBLIC_API_BASE_URL")
    require_text(".env.example", "N8N_WEBHOOK_URL")
    require_text(".env.example", "SERVICEOPS_BACKUP_DIR")
    require_text("project_notes.md", "current operating dashboard")
    require_text("project_notes.md", "documentation-audit-2026-06-16.md")
    require_text("project_notes.md", "Self-hosted n8n VPS production handoff")
    require_text("docs/harness/project-history.md", "Deferred Work Ledger")
    require_text("docs/harness/project-history.md", "Hardened production paths after Phase 16")
    require_text("docs/harness/project-history.md", "self-hosted VPS n8n service")
    require_text("docs/harness/repository-map.md", "compact current operating dashboard")
    require_text("docs/harness/repository-map.md", "documentation-audit-2026-06-16.md")
    require_text("docs/harness/repository-map.md", "self-hosted-n8n-vps-evidence-2026-06-16.md")
    require_text("docs/operations/ai-providers.md", "RAG Coverage And Knowledge Gaps")
    require_text("domains/ai-agents/domain.md", "Current RAG Fallback Behavior")
    require_text("domains/knowledge-base/domain.md", "Current Retrieval-To-Prompt Boundary")
    require_text("domains/service-requests/domain.md", "service_request_number_seq")
    require_text("domains/scheduling/domain.md", "exclusion constraint")
    require_text("domains/inventory/domain.md", "lock the relevant stock and reservation rows")
    require_text("docs/operations/deployment-runbook.md", "serviceops_api.operations.bootstrap_admin")
    require_text("docs/operations/deployment-runbook.md", "http://n8n:5678")
    require_text("docs/operations/operational-diagnostics.md", "one Telegram bot token means one active polling process")
    require_text("docs/operations/n8n-workflows.md", "Production VPS Runtime")
    require_text("docs/operations/self-hosted-n8n-vps-evidence-2026-06-16.md", "CFX-20260616-000008")
    require_text("docs/operations/launch-smoke-evidence.md", "Go/No-Go")

    scan_for_markers()
    validate_local_links()
    print("documentation harness check passed")


if __name__ == "__main__":
    main()
