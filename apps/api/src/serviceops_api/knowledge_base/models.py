from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


KnowledgeDocumentStatus = Literal["pending_embedding", "embedded", "failed"]


def _clean_required(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Field is required")
    return cleaned


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class IngestKnowledgeDocumentPayload(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    source_uri: str | None = Field(default=None, max_length=500)
    body: str = Field(min_length=1, max_length=100000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    _clean_title = field_validator("title")(_clean_required)
    _clean_source_uri = field_validator("source_uri")(_clean_optional)
    _clean_body = field_validator("body")(_clean_required)


class KnowledgeDocumentResponse(BaseModel):
    document_id: int
    title: str
    source_uri: str | None
    status: KnowledgeDocumentStatus
    chunk_count: int


class KnowledgeChunkSource(BaseModel):
    document_id: int
    document_title: str
    source_uri: str | None
    chunk_id: int
    chunk_index: int
    start_char: int
    end_char: int

    model_config = ConfigDict(frozen=True)


class KnowledgeRetrievalPayload(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=10)

    _clean_query = field_validator("query")(_clean_required)


class KnowledgeRetrievalResult(BaseModel):
    document_id: int
    document_title: str
    source_uri: str | None
    chunk_id: int
    chunk_index: int
    start_char: int
    end_char: int
    content: str
    score: float


class KnowledgeRetrievalResponse(BaseModel):
    query: str
    results: list[KnowledgeRetrievalResult]
