from __future__ import annotations

import logging

from serviceops_api.ai_agents.models import (
    AssistantRunListResponse,
    AssistantRunPayload,
    AssistantRunResponse,
    AiSuggestion,
    AiSuggestionActionResponse,
    AiSuggestionListResponse,
    GenerateAiSuggestionsPayload,
)
from serviceops_api.ai_agents.assistant_tools import AssistantToolRegistry, safe_assistant_message, safe_assistant_text
from serviceops_api.ai_agents.prompting import build_prompt_input
from serviceops_api.ai_agents.providers import AiSuggestionProvider
from serviceops_api.ai_agents.repository import AiAssistantHistoryStore, AiSuggestionStore
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


class RunStaffAssistant:
    def __init__(self, history_repository: AiAssistantHistoryStore, tool_registry: AssistantToolRegistry) -> None:
        self._history_repository = history_repository
        self._tool_registry = tool_registry

    def execute(self, payload: AssistantRunPayload, staff) -> AssistantRunResponse:
        safe_message = safe_assistant_message(payload.message)
        try:
            answer_method = getattr(self._tool_registry, "answer", None)
            if callable(answer_method):
                answer = answer_method(payload.message, staff)
                tool_calls = list(answer["tool_calls"])  # type: ignore[index]
                primary_tool = str(tool_calls[0]["tool_name"]) if tool_calls else "unknown"  # type: ignore[index]
                safe_message = safe_assistant_message(payload.message, primary_tool)
                status = str(answer["status"])  # type: ignore[index]
                assistant_message = safe_assistant_text(str(answer["assistant_message"]))  # type: ignore[index]
            else:
                plan = self._tool_registry.plan(payload.message)
                safe_message = safe_assistant_message(payload.message, str(plan["tool_name"]))
                tool_call = self._tool_registry.preview(plan, staff)
                tool_calls = [tool_call]
                status = str(tool_call["status"])
                assistant_message = safe_assistant_text(
                    _assistant_message(status, str(tool_call["tool_name"]), str(tool_call.get("result_summary") or ""))
                )
            tool_calls = [_safe_tool_call_for_history(tool_call) for tool_call in tool_calls]
            saved = self._history_repository.save_run(
                actor_username=staff.username,
                safe_message=safe_message,
                status=status,
                assistant_message=assistant_message,
                tool_calls=tool_calls,
            )
            logger.info(
                "Staff assistant run recorded",
                extra={
                    "serviceops_context": {
                        "actor_username": staff.username,
                        "action": "ai_assistant.run_recorded",
                        "target": str(saved["run_id"]),
                        "outcome": "succeeded",
                        "reason": str(tool_calls[0]["tool_name"]) if tool_calls else "unknown",
                    }
                },
            )
            return AssistantRunResponse.model_validate(saved)
        except PermissionError:
            raise
        except Exception as exc:
            saved = self._history_repository.save_run(
                actor_username=staff.username,
                safe_message=safe_message,
                status="failed",
                assistant_message="Assistant tool request failed.",
                tool_calls=[
                    {
                        "tool_name": "unknown",
                        "policy": "read_only",
                        "status": "failed",
                        "arguments": {},
                        "result_summary": "Assistant tool request failed.",
                        "result_refs": [],
                    }
                ],
            )
            logger.info(
                "Staff assistant run failed",
                extra={
                    "serviceops_context": {
                        "actor_username": staff.username,
                        "action": "ai_assistant.run_recorded",
                        "target": str(saved["run_id"]),
                        "outcome": "failed",
                        "reason": exc.__class__.__name__,
                    }
                },
            )
            return AssistantRunResponse.model_validate(saved)


class ListStaffAssistantRuns:
    def __init__(self, history_repository: AiAssistantHistoryStore) -> None:
        self._history_repository = history_repository

    def execute(self, staff) -> AssistantRunListResponse:
        return AssistantRunListResponse.model_validate({"items": self._history_repository.list_runs(staff.username)})


class ConfirmStaffAssistantTool:
    def __init__(self, history_repository: AiAssistantHistoryStore, tool_registry: AssistantToolRegistry) -> None:
        self._history_repository = history_repository
        self._tool_registry = tool_registry

    def execute(self, run_id: int, staff) -> AssistantRunResponse:
        run = self._history_repository.claim_run_for_confirmation(run_id, staff.username)
        tool_calls = list(run.get("tool_calls", []))
        if not tool_calls:
            raise ValueError("Assistant run has no pending tool call")
        pending = dict(tool_calls[0])
        if pending["policy"] != "requires_confirmation":
            raise ValueError("Assistant tool does not require confirmation")
        try:
            tool_call = self._tool_registry.execute(str(pending["tool_name"]), dict(pending.get("arguments", {})), staff)
        except Exception:
            failed = self._history_repository.mark_run_failed(
                run_id,
                staff.username,
                "Confirmed assistant tool failed before completing the requested change.",
            )
            return AssistantRunResponse.model_validate(failed)
        try:
            saved = self._history_repository.update_run_after_confirmation(
                run_id=run_id,
                actor_username=staff.username,
                status="completed",
                assistant_message=_assistant_message("completed", str(tool_call["tool_name"]), str(tool_call.get("result_summary") or "")),
                tool_call=tool_call,
            )
        except Exception:
            failed = self._history_repository.mark_run_failed(
                run_id,
                staff.username,
                "Confirmed assistant tool may have created a draft, but history finalization failed. Check procurement records before retrying.",
            )
            logger.info(
                "Staff assistant confirmation finalization failed",
                extra={
                    "serviceops_context": {
                        "actor_username": staff.username,
                        "action": "ai_assistant.tool_confirmed",
                        "target": str(run_id),
                        "outcome": "failed",
                        "reason": str(tool_call["tool_name"]),
                    }
                },
            )
            return AssistantRunResponse.model_validate(failed)
        logger.info(
            "Staff assistant confirmed tool",
            extra={
                "serviceops_context": {
                    "actor_username": staff.username,
                    "action": "ai_assistant.tool_confirmed",
                    "target": str(run_id),
                    "outcome": "succeeded",
                    "reason": str(tool_call["tool_name"]),
                }
            },
        )
        return AssistantRunResponse.model_validate(saved)


def _assistant_message(status: str, tool_name: str, result_summary: str = "") -> str:
    if status == "confirmation_required":
        return f"{tool_name} requires staff confirmation before changing ServiceOps data."
    if status == "failed":
        return "Assistant tool request failed."
    if status == "completed" and result_summary:
        return result_summary
    return f"{tool_name} completed."


def _safe_tool_call_for_history(tool_call: dict[str, object]) -> dict[str, object]:
    safe_call = dict(tool_call)
    safe_call["result_summary"] = safe_assistant_text(str(safe_call.get("result_summary") or ""))
    refs = []
    for ref in list(safe_call.get("result_refs") or []):
        if not isinstance(ref, dict):
            continue
        refs.append(
            {
                "label": safe_assistant_text(str(ref.get("label") or ""))[:180],
                "target_type": safe_assistant_text(str(ref.get("target_type") or ""))[:80],
                "target_id": safe_assistant_text(str(ref.get("target_id") or ""))[:180],
                "href": None if ref.get("href") is None else safe_assistant_text(str(ref.get("href")))[:300],
            }
        )
    safe_call["result_refs"] = refs
    return safe_call
