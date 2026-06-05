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
    "docs/harness/repository-map.md",
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
    "docs/review/phase-00-review.md",
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
    "05-knowledge-base-rag.md",
    "06-ai-agent-workflows.md",
    "07-technician-and-inventory.md",
    "08-deployment-and-operations.md",
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

    scan_for_markers()
    validate_local_links()
    print("documentation harness check passed")


if __name__ == "__main__":
    main()
