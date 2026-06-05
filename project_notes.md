# Project Notes

## Current Status

The repository currently contains a Figma-exported React/Vite reference in `reference/figma` and a documentation harness for agent-first development. Phase 00 repository harness work is implemented: Git is initialized, the detailed implementation plan exists, the documentation check script exists, and local documentation verification passes.

## Latest Changes

- 2026-06-05: Captured product vision, stack choices, harness-engineering approach, DDD/hexagonal direction, Figma reference assessment, and phased implementation strategy as repository artifacts.
- 2026-06-05: Added `project_notes.md` as the operational status file for future agent runs.
- 2026-06-05: Added phase-based execution plans with subagent review gates.
- 2026-06-05: Removed the redundant operational status file naming path; `project_notes.md` is the single operational status file.
- 2026-06-05: Added the process decision that each phase requires a detailed implementation plan before execution.
- 2026-06-05: Started Phase 00 execution and added `docs/execution-plans/detailed/00-repository-harness-implementation.md`.
- 2026-06-05: Completed Phase 00 repository harness implementation after Git initialization became available.
- 2026-06-05: Added `.gitignore` so local `.agents/` runtime files stay out of repository commits.
- 2026-06-05: Added `.gitkeep` placeholders for empty scaffold directories and extended repo checks to validate required directories.
- 2026-06-05: Renamed the initial Git branch to `main` for GitHub readiness and saved the Phase 00 review artifact in `docs/review/phase-00-review.md`.

## Active Focus

Phase 01 planning is the active focus: create a detailed implementation plan for `docs/execution-plans/phases/01-foundation-runtime.md` before generating application runtime code.

## Next Steps

1. Create a detailed implementation plan for Phase 01.
2. Review the Phase 01 plan before execution.
3. Execute Phase 01 only after the detailed plan exists.
4. Keep `python3 tools/repo-checks/check_docs.py` passing after harness changes.

## Active Artifacts

- Plan index: `docs/execution-plans/index.md`
- Completed phase slice: `docs/execution-plans/phases/00-repository-harness.md`
- Detailed Phase 00 plan: `docs/execution-plans/detailed/00-repository-harness-implementation.md`
- Next phase slice: `docs/execution-plans/phases/01-foundation-runtime.md`
- Architecture map: `ARCHITECTURE.md`
- Domain map: `docs/domain-maps/index.md`
- Review protocol: `docs/review/subagent-review-protocol.md`
- Phase 00 review: `docs/review/phase-00-review.md`

## Recent Decisions

- The backend is a modular monolith with DDD/hexagonal boundaries.
- PostgreSQL with pgvector is the default SQL and RAG store.
- The Figma reference drives the public client UI, but exported code is treated as a reference, not production structure.
- AI features are operational workflows with human confirmation, not decorative client-facing claims.
- `AGENTS.md` files act as maps and context entry points.
- Repo-specific skills are stored as portable drafts in `docs/agent-skills` until the project is ready to activate them.
- Before executing any phase, create a detailed implementation plan for that phase; current phase files are slice maps, not execution-ready implementation plans.
- Phase 00 local documentation verification command is `python3 tools/repo-checks/check_docs.py`.
