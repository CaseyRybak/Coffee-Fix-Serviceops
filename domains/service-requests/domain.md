# Service Requests Domain

## Responsibility

This domain manages repair requests from creation to closure. It records request details, lifecycle status, clarification needs, assignment metadata, and status history.

## Initial Statuses

- `new`
- `needs_clarification`
- `awaiting_assignment`
- `technician_assigned`
- `visit_scheduled`
- `diagnostics`
- `waiting_for_parts`
- `repair_in_progress`
- `completed`
- `closed`
- `warranty_case`
- `cancelled`

## First Use Cases

- Create repair request.
- Generate public request number.
- Add status event.
- Ask clarification question.
- Record customer answer.
- Assign technician manually.
- Show public status page data.

