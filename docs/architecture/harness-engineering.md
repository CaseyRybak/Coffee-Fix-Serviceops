# Harness Engineering Approach

## Principle

The repository is designed so contributors can understand current intent, navigate the codebase, execute bounded slices, validate work, and receive review without relying on chat history.

## Repository Knowledge

The repository stores:

- Product vision.
- User intent.
- Architecture.
- Domain maps.
- Execution plans.
- Review protocol.
- Decisions.
- Reference designs.
- Repo-specific skills.

## Progressive Disclosure

Contributors should not load the entire repository at once. They start with short maps and follow links to the specific domain and phase.

```text
AGENTS.md
→ project_notes.md
→ plan index
→ active phase
→ domain map
→ code and tests
```

## Review Loop

Each implementation slice includes:

- Scope check.
- Implementation.
- Local verification.
- Subagent review for plan compliance.
- Subagent review for code quality and architecture fit.
- Documentation update.
- `project_notes.md` update.

## Entropy Management

The project includes doc-gardening and context artifacts so stale plans, outdated domain maps, and mismatched docs can be found and refreshed in small increments.
