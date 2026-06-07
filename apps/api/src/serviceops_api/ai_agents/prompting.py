from __future__ import annotations

from typing import Any

from serviceops_api.ai_agents.models import AiPromptInput, AiRagSource


def build_prompt_input(request: dict[str, object], rag_results: list[dict[str, object]]) -> AiPromptInput:
    customer = _mapping(request.get("customer"))
    machine = _mapping(request.get("machine"))
    timeline = request.get("timeline")
    events = timeline if isinstance(timeline, list) else []
    latest_event = _mapping(events[-1]) if events else {}
    clarification = request.get("clarification")
    assignment = _mapping(request.get("assignment"))
    internal_notes = request.get("internal_notes")
    note_count = len(internal_notes) if isinstance(internal_notes, list) else 0
    machine_label = " ".join(
        part
        for part in (
            str(machine.get("brand") or "").strip(),
            str(machine.get("model") or "").strip(),
        )
        if part
    )
    assigned = assignment.get("technician_name")
    return AiPromptInput(
        request_number=str(request.get("request_number") or ""),
        status=str(request.get("status") or ""),
        urgency=str(request.get("urgency") or ""),
        customer_context=str(customer.get("client_type") or "unknown"),
        machine_label=machine_label or "Unknown machine",
        location_type=str(machine.get("location_type") or "unknown"),
        problem_summary=str(request.get("problem") or ""),
        latest_timeline_title=None if not latest_event else str(latest_event.get("title") or ""),
        clarification_state="has_open_clarification" if clarification else "none",
        assignment_state="assigned" if assigned else "unassigned",
        internal_note_count=note_count,
        rag_sources=[
            AiRagSource(
                document_id=int(result["document_id"]),
                document_title=str(result["document_title"]),
                source_uri=None if result.get("source_uri") is None else str(result.get("source_uri")),
                chunk_id=int(result["chunk_id"]),
                chunk_index=int(result["chunk_index"]),
                content=str(result["content"]),
                score=float(result["score"]),
            )
            for result in rag_results
        ],
    )


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
