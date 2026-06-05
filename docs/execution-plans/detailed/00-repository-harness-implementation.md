# Repository Harness Implementation Plan

> **For implementation workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Phase 00 by making the repository harness executable, verifiable, and ready to hand off to Phase 01.

**Architecture:** This phase changes repository metadata and documentation only. It does not introduce application runtime code. The core output is a lightweight documentation check script plus updated contributor entry points.

**Tech Stack:** Python standard library for repo checks, Git for repository initialization, Markdown documentation.

---

## Execution Status

- Completed: detailed Phase 00 plan created.
- Completed: documentation harness check script created.
- Completed: repository map and plan index updated.
- Completed: local documentation check passes with `python3 tools/repo-checks/check_docs.py`.
- Completed: subagent review performed.
- Completed: Git repository initialized and `git status --short` exits successfully.
- Completed: follow-up subagent review performed after Git initialization.
- Completed: `docs/execution-plans/index.md` now points to Phase 01 as the active phase.

## Completion Evidence

```text
python3 tools/repo-checks/check_docs.py
→ documentation harness check passed

test ! -f project_nodes.md && echo no_project_nodes
→ no_project_nodes

git status --short
→ exits 0 and lists untracked repository files
```

## Task 1: Initialize Repository State

**Files:**
- Read: `.git`
- Modify: `project_notes.md`

- [x] **Step 1: Check whether Git is initialized**

Run:

```bash
git status --short
```

Historical output before initialization:

```text
fatal: not a git repository (or any of the parent directories): .git
```

- [x] **Step 2: Initialize Git if absent**

Run:

```bash
git init
```

Expected:

```text
Initialized empty Git repository
```

- [x] **Step 3: Verify Git now responds**

Run:

```bash
git status --short
```

Expected: command exits 0 and lists untracked files.

## Task 2: Add Repository Documentation Check

**Files:**
- Create: `tools/repo-checks/check_docs.py`
- Create: `tools/repo-checks/README.md`

- [x] **Step 1: Create `check_docs.py`**

The script checks:

- required root files exist;
- `project_notes.md` is present;
- `project_nodes.md` is absent;
- each domain has `AGENTS.md` and `domain.md`;
- each active phase plan exists;
- repo-specific skill drafts exist;
- created harness docs do not contain unresolved placeholder markers.

- [x] **Step 2: Create repo-check README**

Document the command:

```bash
python3 tools/repo-checks/check_docs.py
```

- [x] **Step 3: Run the check**

Run:

```bash
python3 tools/repo-checks/check_docs.py
```

Expected:

```text
documentation harness check passed
```

## Task 3: Update Harness Documentation

**Files:**
- Modify: `docs/harness/repository-map.md`
- Modify: `docs/execution-plans/index.md`
- Modify: `project_notes.md`

- [x] **Step 1: Add repo check script to repository map**

Add `tools/repo-checks/check_docs.py` as the Phase 00 verification command.

- [x] **Step 2: Add detailed plan location to plan index**

Add `docs/execution-plans/detailed/` as the place for just-in-time detailed implementation plans.

- [x] **Step 3: Update `project_notes.md`**

Reflect:

- Phase 00 implementation has started.
- The detailed Phase 00 plan exists.
- The next active phase after Phase 00 is Phase 01.

## Task 4: Local Verification

**Files:**
- Read: `AGENTS.md`
- Read: `project_notes.md`
- Read: `docs/execution-plans/index.md`
- Read: `docs/harness/repository-map.md`

- [x] **Step 1: Run docs check**

Run:

```bash
python3 tools/repo-checks/check_docs.py
```

Expected:

```text
documentation harness check passed
```

- [x] **Step 2: Check old operational file name is gone**

Run:

```bash
test ! -f project_nodes.md && echo no_project_nodes
```

Expected:

```text
no_project_nodes
```

- [x] **Step 3: Verify Git status is available**

Run:

```bash
git status --short
```

Expected: command exits 0.

## Task 5: Subagent Review

**Files:**
- Read: `docs/review/subagent-review-protocol.md`
- Read: `docs/execution-plans/phases/00-repository-harness.md`
- Read: `docs/execution-plans/detailed/00-repository-harness-implementation.md`

- [x] **Step 1: Request review**

Ask a subagent to review Phase 00 using:

- plan compliance;
- architecture and harness quality;
- documentation clarity;
- missing entry points.

- [x] **Step 2: Resolve blocking findings**

Apply any required documentation or check-script fixes.

- [x] **Step 3: Re-run local verification**

Run:

```bash
python3 tools/repo-checks/check_docs.py
```

Expected:

```text
documentation harness check passed
```
