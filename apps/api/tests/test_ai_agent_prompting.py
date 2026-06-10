from serviceops_api.ai_agents.prompting import build_prompt_input
from serviceops_api.ai_agents.providers import DeterministicAiSuggestionProvider


def _request_snapshot(problem: str = "E61 group overheats after descaling") -> dict[str, object]:
    return {
        "request_number": "CFX-20260607-000001",
        "status": "new",
        "problem": problem,
        "urgency": "today",
        "customer": {"client_type": "coffee_shop", "phone": "+79990000000", "telegram": "@hidden"},
        "machine": {"brand": "Rocket", "model": "Appartamento", "location_type": "coffee_shop"},
        "timeline": [{"title": "Заявка создана", "description": "Получено обращение", "actor": "system"}],
        "clarification": None,
        "assignment": {
            "technician_name": None,
            "technician_phone": None,
            "technician_region": None,
            "visit_window": None,
        },
        "internal_notes": [],
    }


def test_prompt_input_uses_service_request_and_rag_sources() -> None:
    prompt = build_prompt_input(
        request=_request_snapshot(),
        rag_results=[
            {
                "document_id": 1,
                "document_title": "E61 overheating repair guide",
                "source_uri": "seed://repair/e61-overheating",
                "chunk_id": 5,
                "chunk_index": 0,
                "start_char": 0,
                "end_char": 120,
                "content": "Check thermosiphon scale and boiler pressure.",
                "score": 0.82,
            }
        ],
    )

    assert prompt.request_number == "CFX-20260607-000001"
    assert "E61 group overheats" in prompt.problem_summary
    assert prompt.machine_label == "Rocket Appartamento"
    assert prompt.customer_context == "coffee_shop"
    assert prompt.latest_timeline_title == "Заявка создана"
    assert prompt.internal_note_count == 0
    assert prompt.rag_sources[0].source_uri == "seed://repair/e61-overheating"
    serialized = prompt.model_dump_json()
    assert "+79990000000" not in serialized
    assert "@hidden" not in serialized


def test_prompt_input_excludes_sensitive_operational_details() -> None:
    request = _request_snapshot()
    request["assignment"] = {
        "technician_name": "Sergey Morozov",
        "technician_phone": "+7 999 222-33-44",
        "technician_region": "ЦАО",
        "visit_window": "tomorrow",
    }
    request["internal_notes"] = [
        {"body": "Customer is angry; discount approved by manager.", "author": "dispatcher@coffeefix.local"}
    ]
    request["ai_suggestions"] = [{"content": "Old provider output should not be echoed."}]
    request["notification_deliveries"] = [{"error": "bot token failed with secret-value"}]

    prompt = build_prompt_input(request=request, rag_results=[])

    serialized = prompt.model_dump_json()
    assert "Sergey Morozov" not in serialized
    assert "+7 999 222-33-44" not in serialized
    assert "Customer is angry" not in serialized
    assert "dispatcher@coffeefix.local" not in serialized
    assert "Old provider output" not in serialized
    assert "secret-value" not in serialized
    assert prompt.assignment_state == "assigned"
    assert prompt.internal_note_count == 1


def test_deterministic_provider_returns_bounded_human_review_suggestions() -> None:
    prompt = build_prompt_input(
        request=_request_snapshot("E61 group overheats and pressure rises"),
        rag_results=[],
    )

    suggestions = DeterministicAiSuggestionProvider().suggest(prompt)

    assert {suggestion.kind for suggestion in suggestions} == {
        "intake_classification",
        "diagnostic_question",
        "likely_cause",
        "parts",
        "customer_reply",
    }
    assert all("диспетчер" in suggestion.rationale.lower() for suggestion in suggestions)
    assert all(0 <= suggestion.confidence <= 1 for suggestion in suggestions)
