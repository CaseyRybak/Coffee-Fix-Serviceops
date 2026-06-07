from __future__ import annotations

from typing import Protocol

from serviceops_api.ai_agents.models import AiPromptInput, AiSuggestionCreate


class AiSuggestionProvider(Protocol):
    def suggest(self, prompt: AiPromptInput) -> list[AiSuggestionCreate]:
        """Return human-reviewed suggestions for a service request."""


class DeterministicAiSuggestionProvider:
    def suggest(self, prompt: AiPromptInput) -> list[AiSuggestionCreate]:
        source_chunks = prompt.rag_sources[:2]
        source_hint = source_chunks[0].content if source_chunks else "Проверьте симптомы и историю заявки перед решением."
        return [
            AiSuggestionCreate(
                kind="intake_classification",
                title="Классификация обращения",
                content=f"{prompt.urgency}: {prompt.customer_context}, {prompt.machine_label}",
                rationale="Диспетчер проверяет классификацию перед изменением очереди или статуса.",
                confidence=0.72,
            ),
            AiSuggestionCreate(
                kind="diagnostic_question",
                title="Уточнить условия перегрева",
                content="Когда именно перегревается группа: сразу после прогрева, после пролива или после простоя?",
                rationale="Диспетчер может отправить вопрос клиенту только после ручного подтверждения.",
                confidence=0.78,
                source_chunks=source_chunks,
            ),
            AiSuggestionCreate(
                kind="likely_cause",
                title="Вероятная причина",
                content=f"Возможны накипь в термосифоне, ограничение протока или завышенное давление. Контекст: {source_hint}",
                rationale="Диспетчер использует причину как подсказку, а не как подтвержденную диагностику.",
                confidence=0.66,
                source_chunks=source_chunks,
            ),
            AiSuggestionCreate(
                kind="parts",
                title="Вероятные запчасти",
                content="Проверить: жиклер/рестриктор группы, трубку прессостата, прессостат. inventory_slice_pending=true",
                rationale="Диспетчер видит концепты запчастей; резервирование будет в inventory slice.",
                confidence=0.52,
                source_chunks=source_chunks,
            ),
            AiSuggestionCreate(
                kind="customer_reply",
                title="Черновик ответа клиенту",
                content="Спасибо, мы уточним режим перегрева и передадим мастеру данные по давлению и циркуляции группы.",
                rationale="Диспетчер редактирует и отправляет ответ вручную; AI не отправляет сообщения.",
                confidence=0.7,
            ),
        ]
