from __future__ import annotations

import json
from urllib.error import HTTPError

import pytest

from serviceops_api.ai_agents.models import AiPromptInput, AiRagSource
from serviceops_api.ai_agents.providers import (
    DeterministicAiSuggestionProvider,
    OpenAiCompatibleAiSuggestionProvider,
    create_ai_suggestion_provider,
)
from serviceops_api.config import Settings


def _prompt() -> AiPromptInput:
    return AiPromptInput(
        request_number="CFX-20260610-000001",
        status="new",
        urgency="today",
        customer_context="coffee_shop",
        machine_label="Jura E8",
        location_type="coffee_shop",
        problem_summary="No coffee flow after descaling.",
        latest_timeline_title="Заявка создана",
        clarification_state="none",
        assignment_state="unassigned",
        internal_note_count=1,
        rag_sources=[
            AiRagSource(
                document_id=1,
                document_title="Jura no-flow diagnostics",
                source_uri="seed://repair/jura-no-flow",
                chunk_id=10,
                chunk_index=0,
                content="Check brew unit, drainage valve, pump sound, and scale restrictions.",
                score=0.83,
            )
        ],
    )


def test_ai_provider_factory_returns_deterministic_provider_by_default() -> None:
    settings = Settings(ai_provider="deterministic")

    provider = create_ai_suggestion_provider(settings)

    assert isinstance(provider, DeterministicAiSuggestionProvider)


def test_ai_provider_factory_requires_key_for_live_provider() -> None:
    settings = Settings(ai_provider="openai-compatible", ai_model="gpt-4.1-mini", ai_api_key="")

    with pytest.raises(ValueError, match="SERVICEOPS_AI_API_KEY is required"):
        create_ai_suggestion_provider(settings)


def test_ai_provider_factory_returns_openai_compatible_provider() -> None:
    settings = Settings(
        ai_provider="openai-compatible",
        ai_model="gpt-4.1-mini",
        ai_api_key="test-key",
    )

    provider = create_ai_suggestion_provider(settings)

    assert isinstance(provider, OpenAiCompatibleAiSuggestionProvider)


def test_openai_compatible_ai_provider_builds_safe_chat_payload() -> None:
    captured: dict[str, object] = {}

    def fake_post_json(url: str, body: dict[str, object], headers: dict[str, str], timeout: float) -> dict[str, object]:
        captured["url"] = url
        captured["body"] = body
        captured["headers"] = headers
        captured["timeout"] = timeout
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "suggestions": [
                                    {
                                        "kind": "diagnostic_question",
                                        "title": "Уточнить пролив",
                                        "content": "Слышно ли работу помпы при попытке пролива?",
                                        "rationale": "Диспетчер проверяет подсказку перед вопросом клиенту.",
                                        "confidence": 0.74,
                                        "source_chunk_indexes": [0, 99],
                                    }
                                ]
                            }
                        )
                    }
                }
            ]
        }

    provider = OpenAiCompatibleAiSuggestionProvider(
        api_base_url="https://provider.example/v1",
        api_key="test-key",
        model="gpt-4.1-mini",
        timeout_seconds=12,
        max_retries=0,
        post_json=fake_post_json,
    )

    suggestions = provider.suggest(_prompt())

    assert captured["url"] == "https://provider.example/v1/chat/completions"
    assert captured["headers"] == {"Authorization": "Bearer test-key", "Content-Type": "application/json"}
    assert captured["timeout"] == 12
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["model"] == "gpt-4.1-mini"
    prompt_text = json.dumps(body, ensure_ascii=False)
    assert "CFX-20260610-000001" in prompt_text
    assert "No coffee flow" in prompt_text
    assert "Jura E8" in prompt_text
    assert "seed://repair/jura-no-flow" in prompt_text
    assert "test-key" not in prompt_text
    assert "+7" not in prompt_text
    assert "@hidden" not in prompt_text
    assert len(suggestions) == 1
    assert suggestions[0].kind == "diagnostic_question"
    assert suggestions[0].source_chunks == [_prompt().rag_sources[0]]


def test_openai_compatible_ai_provider_accepts_word_confidence_from_provider() -> None:
    def fake_post_json(url: str, body: dict[str, object], headers: dict[str, str], timeout: float) -> dict[str, object]:
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "suggestions": [
                                    {
                                        "kind": "likely_cause",
                                        "title": "Проверить проток",
                                        "content": "Вероятно ограничение протока после декальцинации.",
                                        "rationale": "OpenRouter-compatible models may return confidence as a label.",
                                        "confidence": "high",
                                        "source_chunk_indexes": [0],
                                    }
                                ]
                            }
                        )
                    }
                }
            ]
        }

    provider = OpenAiCompatibleAiSuggestionProvider(
        api_base_url="https://provider.example/v1",
        api_key="test-key",
        model="gpt-4.1-mini",
        timeout_seconds=12,
        max_retries=0,
        post_json=fake_post_json,
    )

    suggestions = provider.suggest(_prompt())

    assert suggestions[0].confidence == 0.82


def test_openai_compatible_ai_provider_retries_and_masks_errors() -> None:
    attempts = 0

    def fake_post_json(url: str, body: dict[str, object], headers: dict[str, str], timeout: float) -> dict[str, object]:
        nonlocal attempts
        attempts += 1
        raise HTTPError(url, 429, "rate limited", hdrs=None, fp=None)

    provider = OpenAiCompatibleAiSuggestionProvider(
        api_base_url="https://provider.example/v1",
        api_key="secret-key",
        model="gpt-4.1-mini",
        timeout_seconds=5,
        max_retries=1,
        post_json=fake_post_json,
    )

    with pytest.raises(RuntimeError, match="AI provider request failed") as exc:
        provider.suggest(_prompt())

    assert attempts == 2
    assert "secret-key" not in str(exc.value)


def test_openai_compatible_ai_provider_masks_malformed_transport_json() -> None:
    def fake_post_json(url: str, body: dict[str, object], headers: dict[str, str], timeout: float) -> dict[str, object]:
        raise json.JSONDecodeError("provider leaked body with secret-key", doc="secret-key", pos=0)

    provider = OpenAiCompatibleAiSuggestionProvider(
        api_base_url="https://provider.example/v1",
        api_key="secret-key",
        model="gpt-4.1-mini",
        timeout_seconds=5,
        max_retries=0,
        post_json=fake_post_json,
    )

    with pytest.raises(RuntimeError, match="AI provider request failed") as exc:
        provider.suggest(_prompt())

    assert "secret-key" not in str(exc.value)
