from __future__ import annotations

import json
from urllib.error import HTTPError

import pytest

from serviceops_api.config import Settings
from serviceops_api.knowledge_base.embeddings import (
    DeterministicEmbeddingProvider,
    OpenAiCompatibleEmbeddingProvider,
    create_embedding_provider,
)


def test_embedding_provider_factory_returns_deterministic_provider_by_default() -> None:
    settings = Settings(embedding_provider="deterministic")

    provider = create_embedding_provider(settings)

    assert isinstance(provider, DeterministicEmbeddingProvider)


def test_embedding_provider_factory_requires_key_for_live_provider() -> None:
    settings = Settings(
        embedding_provider="openai-compatible",
        embedding_model="text-embedding-3-small",
        embedding_api_key="",
    )

    with pytest.raises(ValueError, match="SERVICEOPS_EMBEDDING_API_KEY is required"):
        create_embedding_provider(settings)


def test_embedding_provider_factory_returns_openai_compatible_provider() -> None:
    settings = Settings(
        embedding_provider="openai-compatible",
        embedding_model="text-embedding-3-small",
        embedding_api_key="test-key",
    )

    provider = create_embedding_provider(settings)

    assert isinstance(provider, OpenAiCompatibleEmbeddingProvider)


def test_openai_compatible_embedding_provider_preserves_input_order() -> None:
    captured: dict[str, object] = {}

    def fake_post_json(url: str, body: dict[str, object], headers: dict[str, str], timeout: float) -> dict[str, object]:
        captured["url"] = url
        captured["body"] = body
        captured["headers"] = headers
        captured["timeout"] = timeout
        return {
            "data": [
                {"index": 1, "embedding": [0.0, 1.0, 0.0]},
                {"index": 0, "embedding": [1.0, 0.0, 0.0]},
            ]
        }

    provider = OpenAiCompatibleEmbeddingProvider(
        api_base_url="https://provider.example/v1",
        api_key="test-key",
        model="text-embedding-3-small",
        timeout_seconds=11,
        max_retries=0,
        post_json=fake_post_json,
    )

    embeddings = provider.embed_texts(["first", "second"])

    assert captured["url"] == "https://provider.example/v1/embeddings"
    assert captured["headers"] == {"Authorization": "Bearer test-key", "Content-Type": "application/json"}
    assert captured["timeout"] == 11
    assert captured["body"] == {"model": "text-embedding-3-small", "input": ["first", "second"]}
    assert embeddings == [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]


def test_openai_compatible_embedding_provider_retries_and_masks_errors() -> None:
    attempts = 0

    def fake_post_json(url: str, body: dict[str, object], headers: dict[str, str], timeout: float) -> dict[str, object]:
        nonlocal attempts
        attempts += 1
        raise HTTPError(url, 500, "server error", hdrs=None, fp=None)

    provider = OpenAiCompatibleEmbeddingProvider(
        api_base_url="https://provider.example/v1",
        api_key="secret-key",
        model="text-embedding-3-small",
        timeout_seconds=5,
        max_retries=1,
        post_json=fake_post_json,
    )

    with pytest.raises(RuntimeError, match="Embedding provider request failed") as exc:
        provider.embed_texts(["first"])

    assert attempts == 2
    assert "secret-key" not in str(exc.value)


def test_openai_compatible_embedding_provider_masks_malformed_transport_json() -> None:
    def fake_post_json(url: str, body: dict[str, object], headers: dict[str, str], timeout: float) -> dict[str, object]:
        raise json.JSONDecodeError("provider leaked body with secret-key", doc="secret-key", pos=0)

    provider = OpenAiCompatibleEmbeddingProvider(
        api_base_url="https://provider.example/v1",
        api_key="secret-key",
        model="text-embedding-3-small",
        timeout_seconds=5,
        max_retries=0,
        post_json=fake_post_json,
    )

    with pytest.raises(RuntimeError, match="Embedding provider request failed") as exc:
        provider.embed_texts(["first"])

    assert "secret-key" not in str(exc.value)
