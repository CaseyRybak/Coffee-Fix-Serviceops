from __future__ import annotations

import logging

from serviceops_api.ai_agents.models import (
    AiSuggestion,
    AiSuggestionActionResponse,
    AiSuggestionListResponse,
    GenerateAiSuggestionsPayload,
)
from serviceops_api.ai_agents.prompting import build_prompt_input
from serviceops_api.ai_agents.providers import AiSuggestionProvider
from serviceops_api.ai_agents.repository import AiSuggestionStore
from serviceops_api.knowledge_base.models import KnowledgeRetrievalPayload as RagRetrievalPayload
from serviceops_api.knowledge_base.use_cases import RetrieveKnowledge
from serviceops_api.service_requests.use_cases import ServiceRequestStore

logger = logging.getLogger(__name__)


class GenerateAiSuggestions:
    def __init__(
        self,
        service_request_repository: ServiceRequestStore,
        ai_repository: AiSuggestionStore,
        suggestion_provider: AiSuggestionProvider,
        retrieve_knowledge: RetrieveKnowledge,
        suggestion_limit: int = 5,
    ) -> None:
        self._service_request_repository = service_request_repository
        self._ai_repository = ai_repository
        self._suggestion_provider = suggestion_provider
        self._retrieve_knowledge = retrieve_knowledge
        self._suggestion_limit = suggestion_limit

    def execute(self, request_number: str, payload: GenerateAiSuggestionsPayload) -> AiSuggestionListResponse:
        _ = payload
        request = self._service_request_repository.get_dispatcher_request(request_number)
        machine = request.get("machine") if isinstance(request.get("machine"), dict) else {}
        query = f"{request.get('problem', '')} {machine.get('brand', '')} {machine.get('model', '')}"
        rag = self._retrieve_knowledge.execute(RagRetrievalPayload(query=query, limit=3))
        prompt = build_prompt_input(request, [result.model_dump() for result in rag.results])
        suggestions = self._suggestion_provider.suggest(prompt)[: self._suggestion_limit]
        saved = self._ai_repository.replace_pending_suggestions(request_number, suggestions)
        logger.info(
            "AI suggestions generated",
            extra={
                "serviceops_context": {
                    "request_number": request_number,
                    "action": "ai.suggestions_generated",
                    "target": request_number,
                    "outcome": "succeeded",
                    "reason": f"suggestion_count={len(saved)}",
                    "provider": _provider_name(self._suggestion_provider),
                }
            },
        )
        return AiSuggestionListResponse.model_validate({"request_number": request_number, "suggestions": saved})


class ListAiSuggestions:
    def __init__(self, ai_repository: AiSuggestionStore) -> None:
        self._ai_repository = ai_repository

    def execute(self, request_number: str) -> AiSuggestionListResponse:
        return AiSuggestionListResponse.model_validate(
            {"request_number": request_number, "suggestions": self._ai_repository.list_suggestions(request_number)}
        )


class AcceptAiClarificationSuggestion:
    def __init__(self, service_request_repository: ServiceRequestStore, ai_repository: AiSuggestionStore) -> None:
        self._service_request_repository = service_request_repository
        self._ai_repository = ai_repository

    def execute(self, request_number: str, suggestion_id: int) -> AiSuggestionActionResponse:
        suggestion = self._ai_repository.get_suggestion(suggestion_id)
        if suggestion["request_number"] != request_number or suggestion["kind"] != "diagnostic_question":
            raise KeyError(str(suggestion_id))
        self._service_request_repository.ask_clarification(request_number, str(suggestion["content"]))
        accepted = self._ai_repository.mark_accepted(suggestion_id)
        return AiSuggestionActionResponse.model_validate(
            {
                "request_number": request_number,
                "suggestion": accepted,
                "message": "AI clarification suggestion accepted",
            }
        )


class IgnoreAiSuggestion:
    def __init__(self, ai_repository: AiSuggestionStore) -> None:
        self._ai_repository = ai_repository

    def execute(self, request_number: str, suggestion_id: int) -> AiSuggestionActionResponse:
        suggestion = self._ai_repository.get_suggestion(suggestion_id)
        if suggestion["request_number"] != request_number:
            raise KeyError(str(suggestion_id))
        ignored = self._ai_repository.mark_ignored(suggestion_id)
        return AiSuggestionActionResponse.model_validate(
            {
                "request_number": request_number,
                "suggestion": ignored,
                "message": "AI suggestion ignored",
            }
        )


def _provider_name(provider: AiSuggestionProvider) -> str:
    class_name = provider.__class__.__name__.lower()
    if "openai" in class_name:
        return "openai-compatible"
    if "deterministic" in class_name:
        return "deterministic"
    return provider.__class__.__name__
