# Domain Map Index

## Core Flow

```text
Client
→ service-requests
→ customers
→ machines
→ technicians
→ scheduling
→ inventory
→ notifications
→ billing
```

AI and knowledge-base support the flow:

```text
service-requests
→ ai-agents
→ knowledge-base
→ inventory
→ notifications
```

## Domain Entry Points

- Service requests: `domains/service-requests/AGENTS.md`
- Customers: `domains/customers/AGENTS.md`
- Machines: `domains/machines/AGENTS.md`
- Technicians: `domains/technicians/AGENTS.md`
- Scheduling: `domains/scheduling/AGENTS.md`
- Inventory: `domains/inventory/AGENTS.md`
- Knowledge base: `domains/knowledge-base/AGENTS.md`
- AI agents: `domains/ai-agents/AGENTS.md`
- Notifications: `domains/notifications/AGENTS.md`
- Billing: `domains/billing/AGENTS.md`

## Integration Notes

- `service-requests` is the first core domain because every workflow starts with a repair request.
- `knowledge-base` stores repair knowledge and powers RAG.
- `ai-agents` owns workflow orchestration, prompts, and human-confirmed suggestions.
- `notifications` owns Telegram and n8n communication edges.

