from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


AiSuggestionKind = Literal[
    "intake_classification",
    "diagnostic_question",
    "likely_cause",
    "parts",
    "customer_reply",
]
AiSuggestionStatus = Literal["pending", "accepted", "ignored"]


def _clean_required(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Field is required")
    return cleaned


class AiRagSource(BaseModel):
    document_id: int
    document_title: str
    source_uri: str | None
    chunk_id: int
    chunk_index: int
    content: str
    score: float

    model_config = ConfigDict(frozen=True)


class AiPromptInput(BaseModel):
    request_number: str
    status: str
    urgency: str
    customer_context: str
    machine_label: str
    location_type: str
    problem_summary: str
    latest_timeline_title: str | None
    clarification_state: str
    assignment_state: str
    internal_note_count: int
    rag_sources: list[AiRagSource] = Field(default_factory=list)

    _clean_request_number = field_validator("request_number")(_clean_required)
    _clean_problem_summary = field_validator("problem_summary")(_clean_required)


class AiSuggestionCreate(BaseModel):
    kind: AiSuggestionKind
    title: str = Field(min_length=1, max_length=180)
    content: str = Field(min_length=1, max_length=2000)
    rationale: str = Field(min_length=1, max_length=1000)
    confidence: float = Field(ge=0, le=1)
    source_chunks: list[AiRagSource] = Field(default_factory=list)

    _clean_title = field_validator("title")(_clean_required)
    _clean_content = field_validator("content")(_clean_required)
    _clean_rationale = field_validator("rationale")(_clean_required)


class AiSuggestion(AiSuggestionCreate):
    suggestion_id: int
    request_number: str
    status: AiSuggestionStatus
    created_at: str
    acted_at: str | None = None


class GenerateAiSuggestionsPayload(BaseModel):
    refresh: bool = False


class AiSuggestionListResponse(BaseModel):
    request_number: str
    suggestions: list[AiSuggestion]


class AiSuggestionActionResponse(BaseModel):
    request_number: str
    suggestion: AiSuggestion
    message: str
