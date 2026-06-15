from __future__ import annotations

import re
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
        rag_sources=_relevant_rag_sources(str(request.get("problem") or ""), rag_results),
    )


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _relevant_rag_sources(problem: str, rag_results: list[dict[str, object]]) -> list[AiRagSource]:
    query_terms = _topic_terms(problem)
    return [
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
        if _rag_result_matches_problem(query_terms, problem, result)
    ]


def _rag_result_matches_problem(query_terms: set[str], problem: str, result: dict[str, object]) -> bool:
    source_text = " ".join(
        [
            str(result.get("document_title") or ""),
            str(result.get("source_uri") or ""),
            str(result.get("content") or ""),
        ]
    )
    if _matches_electric_shock_topic(problem, source_text):
        return True
    source_terms = _topic_terms(source_text)
    overlap = query_terms & source_terms
    return len(overlap) >= 2 or any(_is_strong_token(term) for term in overlap)


def _topic_terms(text: str) -> set[str]:
    terms: set[str] = set()
    for token in re.findall(r"[0-9a-zа-яё]+", text.lower()):
        if token in _STOP_WORDS or len(token) < 3:
            continue
        if token.startswith(("кофемаш", "машин")) or token in {"coffee", "machine", "repair", "guide", "seed"}:
            continue
        terms.add(token[:6] if len(token) > 6 else token)
    return terms


def _is_strong_token(term: str) -> bool:
    return any(char.isdigit() for char in term) or len(term) >= 6


def _matches_electric_shock_topic(problem: str, source_text: str) -> bool:
    problem_text = problem.lower()
    source = source_text.lower()
    problem_markers = (
        "бьет током",
        "бьёт током",
        "удар током",
        "ударило током",
        "щиплет током",
        "пробивает током",
        "пробивает на корпус",
        "корпус под напряжением",
        "ток при касании",
    )
    source_markers = (
        "electric shock",
        "electrical shock",
        "утечк",
        "заземл",
        "узо",
        "под напряжением",
        "пробой изоляции",
        "электробезопас",
    )
    return any(marker in problem_text for marker in problem_markers) and any(marker in source for marker in source_markers)


_STOP_WORDS = {
    "and",
    "are",
    "but",
    "for",
    "from",
    "into",
    "not",
    "the",
    "with",
    "или",
    "как",
    "под",
    "при",
    "что",
    "это",
}
