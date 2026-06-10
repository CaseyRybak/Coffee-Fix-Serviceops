from __future__ import annotations

import json
import math
import re
import hashlib
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Protocol


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector for each input text."""


PostJson = Callable[[str, dict[str, object], dict[str, str], float], dict[str, object]]


def post_json(url: str, body: dict[str, object], headers: dict[str, str], timeout: float) -> dict[str, object]:
    request = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers=headers,
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class DeterministicEmbeddingProvider:
    def __init__(self, dimensions: int = 12) -> None:
        if dimensions < 1:
            raise ValueError("dimensions must be greater than zero")
        self.dimensions = dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in re.findall(r"[a-zа-я0-9]+", text.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=4).digest()
            bucket = int.from_bytes(digest[:2], "big") % self.dimensions
            sign = 1.0 if digest[2] % 2 == 0 else -1.0
            vector[bucket] += sign
        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [round(value / magnitude, 8) for value in vector]


class OpenAiCompatibleEmbeddingProvider:
    def __init__(
        self,
        api_base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 20.0,
        max_retries: int = 2,
        post_json: PostJson = post_json,
    ) -> None:
        self._api_base_url = api_base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._max_retries = max(0, max_retries)
        self._post_json = post_json

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._request_with_retries({"model": self._model, "input": texts})
        try:
            rows = response["data"]
            if not isinstance(rows, list):
                raise ValueError("embedding data missing")
            ordered: dict[int, list[float]] = {}
            for row in rows:
                if not isinstance(row, dict):
                    raise ValueError("invalid embedding row")
                index = int(row["index"])
                embedding = row["embedding"]
                if not isinstance(embedding, list):
                    raise ValueError("invalid embedding vector")
                ordered[index] = [float(value) for value in embedding]
            if sorted(ordered) != list(range(len(texts))):
                raise ValueError("embedding count mismatch")
            return [ordered[index] for index in range(len(texts))]
        except Exception as exc:
            raise RuntimeError("Embedding provider request failed") from exc

    def _request_with_retries(self, body: dict[str, object]) -> dict[str, object]:
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        url = f"{self._api_base_url}/embeddings"
        for attempt in range(self._max_retries + 1):
            try:
                return self._post_json(url, body, headers, self._timeout_seconds)
            except json.JSONDecodeError as exc:
                raise RuntimeError("Embedding provider request failed") from exc
            except HTTPError as exc:
                if attempt >= self._max_retries or exc.code not in {408, 409, 425, 429, 500, 502, 503, 504}:
                    raise RuntimeError("Embedding provider request failed") from exc
            except (TimeoutError, URLError, OSError) as exc:
                if attempt >= self._max_retries:
                    raise RuntimeError("Embedding provider request failed") from exc
        raise RuntimeError("Embedding provider request failed")


def create_embedding_provider(settings: object) -> EmbeddingProvider:
    provider_name = str(getattr(settings, "embedding_provider", "deterministic")).strip().lower()
    if provider_name == "deterministic":
        return DeterministicEmbeddingProvider(int(getattr(settings, "knowledge_embedding_dimensions", 12)))
    if provider_name == "openai-compatible":
        api_key = str(getattr(settings, "embedding_api_key", "")).strip()
        if not api_key:
            raise ValueError(
                "SERVICEOPS_EMBEDDING_API_KEY is required when SERVICEOPS_EMBEDDING_PROVIDER=openai-compatible"
            )
        model = str(getattr(settings, "embedding_model", "")).strip()
        if not model:
            raise ValueError(
                "SERVICEOPS_EMBEDDING_MODEL is required when SERVICEOPS_EMBEDDING_PROVIDER=openai-compatible"
            )
        return OpenAiCompatibleEmbeddingProvider(
            api_base_url=str(getattr(settings, "embedding_api_base_url", "https://api.openai.com/v1")),
            api_key=api_key,
            model=model,
            timeout_seconds=float(getattr(settings, "embedding_timeout_seconds", 20.0)),
            max_retries=int(getattr(settings, "embedding_max_retries", 2)),
        )
    raise ValueError(f"Unsupported SERVICEOPS_EMBEDDING_PROVIDER: {provider_name}")


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors must have the same dimensions")
    left_magnitude = math.sqrt(sum(value * value for value in left))
    right_magnitude = math.sqrt(sum(value * value for value in right))
    if left_magnitude == 0 or right_magnitude == 0:
        return 0.0
    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
    return dot_product / (left_magnitude * right_magnitude)
