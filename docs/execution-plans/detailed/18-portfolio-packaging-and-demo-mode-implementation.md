# Portfolio Packaging And Demo Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the implemented ServiceOps system into a safe, clear portfolio case that an external reviewer can understand and try.

**Architecture:** Keep Phase 18 as a documentation and demo-safety packaging slice. Do not add runtime demo switches, production database reset commands, or new product behavior; instead, document a safe demo policy, a guided walkthrough, screenshot capture guidance, and portfolio entry points that point at existing application and operations capabilities. Existing API, web, n8n, Telegram, inventory, scheduling, and AI/RAG behavior remain the source of truth.

**Tech Stack:** Markdown documentation, existing React/Vite web routes, FastAPI API routes, deterministic AI/RAG defaults, Docker Compose/Dokploy operations evidence, n8n workflow exports, Telegram opt-in flow, `tools/repo-checks/check_docs.py`.

---

## File Structure

- Modify `README.md`: rewrite the public entry point as a portfolio case with demo URL, safe credential guidance, business problem, workflows, architecture, stack, setup, production evidence, and skills demonstrated.
- Create `docs/product/portfolio-demo-guide.md`: durable demo policy, guided reviewer scenarios, safe demo data examples, screenshot checklist, and reset guidance that does not mutate production data.
- Create `docs/execution-plans/detailed/18-portfolio-packaging-and-demo-mode-implementation.md`: this plan.
- Modify `docs/execution-plans/index.md`: move the active phase to Phase 19 after Phase 18 is packaged and list this detailed plan as completed.
- Modify `project_notes.md`: record Phase 18 completion and point the next active focus to frontend decomposition.
- Modify `docs/harness/repository-map.md`: list the Phase 18 detailed plan, portfolio demo guide, and Phase 18 review artifact.
- Create `docs/review/phase-18-review.md`: phase closure review artifact covering external clarity, demo safety, secret redaction, screenshot relevance, and capability accuracy.

## Scope Decisions

- Demo mode is a policy and workflow guide, not a new runtime feature.
- No seed/reset code is added in this slice because the current public demo is a pet-project production-like environment, not a disposable database.
- Demo credentials are described as operator-provisioned disposable staff accounts. The repository must not publish reusable usernames/passwords for production staff access.
- Screenshot guidance is documented instead of committing screenshots, because screenshots of live staff, n8n, Telegram, and operations surfaces can accidentally expose secrets or personal data.

## Task 1: Detailed Plan

**Files:**
- Create: `docs/execution-plans/detailed/18-portfolio-packaging-and-demo-mode-implementation.md`

- [ ] **Step 1: Write the detailed implementation plan**

Create this file with goal, architecture, file structure, scope decisions, tasks, verification commands, and review gate.

- [ ] **Step 2: Verify the plan avoids forbidden production changes**

Check that the plan does not instruct workers to truncate production tables, publish admin credentials, store secrets, or switch live AI providers for normal demo review.

Expected: the plan keeps demo data safe and treats reset flows as disposable-environment-only.

## Task 2: Portfolio README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the terse README with a portfolio narrative**

Include these sections:

- `Live Demo`
- `What It Demonstrates`
- `Core Workflows`
- `Architecture`
- `AI, RAG, And Automation`
- `Demo Safety`
- `Local Development`
- `Production And Operations Evidence`
- `Roadmap`
- `Skills Demonstrated`

- [ ] **Step 2: Keep claims tied to implemented capabilities**

Mention owner dashboard, procurement, richer technician recommendation, and tool-using AI only as roadmap items. Do not describe them as shipped.

- [ ] **Step 3: Link to deeper docs**

Use local links to `docs/product/portfolio-demo-guide.md`, `ARCHITECTURE.md`, `docs/execution-plans/index.md`, `docs/operations/public-demo-launch-evidence.md`, `docs/operations/n8n-workflows.md`, `docs/operations/ai-providers.md`, and `docs/operations/deployment-runbook.md`.

## Task 3: Portfolio Demo Guide

**Files:**
- Create: `docs/product/portfolio-demo-guide.md`

- [ ] **Step 1: Document safe demo policy**

State that demo data must be fake, staff accounts must be disposable, live secrets must stay in deployment configuration, deterministic AI is the default for portfolio review, and production reset is not part of Phase 18.

- [ ] **Step 2: Document reviewer scenarios**

Cover:

- public request intake;
- public status by request number or token;
- Telegram opt-in;
- dispatcher triage and clarification;
- AI suggestions with source-backed RAG and knowledge-gap behavior;
- structured scheduling;
- technician diagnosis, repair result, and parts used;
- inventory catalog, stock, compatibility, reservations, low stock, and movements;
- n8n notification delivery evidence;
- operations evidence review.

- [ ] **Step 3: Document screenshot checklist**

Provide a capture list for landing, success state, status page, dispatcher card, AI suggestions, technician workspace, inventory reservations, n8n workflow, Telegram notification, and operations evidence. Include redaction rules for phones, Telegram ids, staff personal data, secrets, provider payloads, and internal notes.

- [ ] **Step 4: Document reset guidance**

State that live production-like demo data is reset manually by creating fresh fake requests and optionally deactivating old disposable staff accounts. Any destructive database reset belongs only in a separate disposable environment.

## Task 4: Harness Updates

**Files:**
- Modify: `docs/execution-plans/index.md`
- Modify: `project_notes.md`
- Modify: `docs/harness/repository-map.md`

- [ ] **Step 1: Update phase index**

Set Phase 19 as the active phase and list the Phase 18 detailed plan among completed detailed plans.

- [ ] **Step 2: Update project notes**

Record Phase 18 as completed and make Phase 19 frontend workspace decomposition the active focus. Preserve operational decisions about secret redaction, public status safety, deterministic AI defaults, and no production database reset.

- [ ] **Step 3: Update repository map**

Add the Phase 18 detailed plan, the portfolio demo guide, and the Phase 18 review artifact to the correct sections.

## Task 5: Review Artifact And Verification

**Files:**
- Create: `docs/review/phase-18-review.md`

- [ ] **Step 1: Create the review artifact**

Record files reviewed, verification commands, blocking issues, non-blocking issues, suggested follow-up slice, documentation updates, and final recommendation.

- [ ] **Step 2: Run documentation verification**

Run:

```bash
python3 tools/repo-checks/check_docs.py
```

Expected:

```text
documentation harness check passed
```

- [ ] **Step 3: Run whitespace verification**

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 4: Inspect the changed-file list**

Run:

```bash
git status --short
```

Expected: only Phase 18 documentation and harness files are changed.

## Review Gate

Before Phase 18 is considered closed, review these points from `docs/review/subagent-review-protocol.md`:

- external reviewer can understand the project from the README in under one minute;
- demo policy does not expose real customer data, real Telegram chat ids, reusable staff credentials, provider payloads, API keys, webhook secrets, or passwords;
- screenshots are either absent or covered by explicit redaction guidance;
- README links to architecture, roadmap, and operations evidence without overwhelming the first read;
- future roadmap items are not described as implemented behavior;
- local setup and production demo sections do not contradict operations docs.
