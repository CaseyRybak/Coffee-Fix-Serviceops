# AI ServiceOps Platform Agent Map

This repository is built for agent-first development. The repository is the system of record for product intent, architecture, plans, domain context, review loops, and reusable project knowledge.

## Start Here

1. Read `project_notes.md` for current status, recent changes, active focus, and next steps.
2. Read `ARCHITECTURE.md` for the system map and domain boundaries.
3. Read `docs/execution-plans/index.md` to choose the active slice.
4. Read the relevant `domains/<domain>/AGENTS.md` before working inside a domain.
5. Read `docs/review/subagent-review-protocol.md` before marking a slice ready.

## Product Context

- Product vision: `docs/product/vision.md`
- MVP scope: `docs/product/mvp-scope.md`
- Figma reference notes: `docs/product/figma-reference-review.md`
- User intent log: `docs/user-intent/2026-06-05-project-intent.md`

## Architecture Context

- Harness engineering approach: `docs/architecture/harness-engineering.md`
- DDD and hexagonal architecture: `docs/architecture/domain-architecture.md`
- Tech stack: `docs/architecture/tech-stack.md`
- Domain index: `docs/domain-maps/index.md`

## Plans

Implementation is sliced into phases. Each phase is reviewed independently by a subagent before the next phase starts.

- Phase index: `docs/execution-plans/index.md`
- Phase slice maps: `docs/execution-plans/phases/`
- Completed plans: `docs/execution-plans/completed/`

Before executing any phase, first create a detailed implementation plan for that phase. The phase files in `docs/execution-plans/phases/` are slice maps; they are not detailed implementation plans by themselves.

## Repository Skills

Repo-specific skill drafts live in `docs/agent-skills/`. They are written as portable `SKILL.md` files and can be installed into the agent skill directory when the project is ready to activate them.

Skill catalog: `docs/agent-skills/skill-catalog.md`
