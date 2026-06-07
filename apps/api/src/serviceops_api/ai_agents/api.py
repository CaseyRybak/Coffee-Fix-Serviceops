from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from serviceops_api.ai_agents.models import (
    AiSuggestionActionResponse,
    AiSuggestionListResponse,
    GenerateAiSuggestionsPayload,
)
from serviceops_api.ai_agents.use_cases import (
    AcceptAiClarificationSuggestion,
    GenerateAiSuggestions,
    IgnoreAiSuggestion,
    ListAiSuggestions,
)


def create_dispatcher_ai_router(
    generate_suggestions: GenerateAiSuggestions,
    list_suggestions: ListAiSuggestions,
    accept_clarification: AcceptAiClarificationSuggestion,
    ignore_suggestion: IgnoreAiSuggestion,
    staff_dependency: Depends | None = None,
) -> APIRouter:
    dependencies = [Depends(staff_dependency)] if staff_dependency is not None else []
    router = APIRouter(prefix="/dispatcher/service-requests", tags=["dispatcher ai"], dependencies=dependencies)

    @router.post("/{request_number}/ai-suggestions/generate", response_model=AiSuggestionListResponse)
    async def generate_ai_suggestions(
        request_number: str,
        payload: GenerateAiSuggestionsPayload | None = None,
    ) -> AiSuggestionListResponse:
        try:
            return generate_suggestions.execute(request_number, payload or GenerateAiSuggestionsPayload())
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found") from exc

    @router.get("/{request_number}/ai-suggestions", response_model=AiSuggestionListResponse)
    async def get_ai_suggestions(request_number: str) -> AiSuggestionListResponse:
        return list_suggestions.execute(request_number)

    @router.post(
        "/{request_number}/ai-suggestions/{suggestion_id}/accept-clarification",
        response_model=AiSuggestionActionResponse,
    )
    async def accept_ai_clarification(request_number: str, suggestion_id: int) -> AiSuggestionActionResponse:
        try:
            return accept_clarification.execute(request_number, suggestion_id)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI suggestion not found") from exc

    @router.post("/{request_number}/ai-suggestions/{suggestion_id}/ignore", response_model=AiSuggestionActionResponse)
    async def ignore_ai_suggestion(request_number: str, suggestion_id: int) -> AiSuggestionActionResponse:
        try:
            return ignore_suggestion.execute(request_number, suggestion_id)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI suggestion not found") from exc

    return router
