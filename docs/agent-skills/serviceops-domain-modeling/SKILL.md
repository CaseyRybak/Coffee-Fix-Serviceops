---
name: serviceops-domain-modeling
description: Use when modeling CoffeeFix Pro repair operations, request lifecycles, dispatcher workflows, technician workflows, customers, machines, parts, statuses, or service-domain vocabulary.
---

# ServiceOps Domain Modeling

## Context To Open

- `ARCHITECTURE.md`
- `docs/domain-maps/index.md`
- Relevant `domains/<domain>/AGENTS.md`
- Relevant `domains/<domain>/domain.md`
- `docs/product/vision.md`

## Pattern

Model repair operations around the request lifecycle. Start with the business event or use case, then identify the owning domain, related domains, status changes, and customer-visible effects.

## Domain Questions

- What customer or operator outcome does this use case support?
- Which domain owns the state change?
- Which related domains provide context?
- Is this a customer-visible fact, internal note, AI suggestion, or confirmed human action?
- Does the request history need a status event?

## Useful Vocabulary

- Repair request.
- Request number.
- Clarification question.
- Technician assignment.
- Visit window.
- Machine brand and model.
- Likely cause.
- Parts suggestion.
- Warranty case.
