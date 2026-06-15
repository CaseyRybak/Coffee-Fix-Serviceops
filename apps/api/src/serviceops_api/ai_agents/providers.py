from __future__ import annotations

import json
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Any, Protocol

from serviceops_api.ai_agents.models import AiPromptInput, AiRagSource, AiSuggestionCreate


class AiSuggestionProvider(Protocol):
    def suggest(self, prompt: AiPromptInput) -> list[AiSuggestionCreate]:
        """Return human-reviewed suggestions for a service request."""


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


class DeterministicAiSuggestionProvider:
    def suggest(self, prompt: AiPromptInput) -> list[AiSuggestionCreate]:
        source_chunks = prompt.rag_sources[:2]
        if _is_electric_shock_report(prompt):
            return _electric_shock_suggestions(source_chunks)

        if not source_chunks:
            return _generic_gap_suggestions(prompt)

        source_hint = source_chunks[0].content
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


class OpenAiCompatibleAiSuggestionProvider:
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

    def suggest(self, prompt: AiPromptInput) -> list[AiSuggestionCreate]:
        response = self._request_with_retries(self._build_body(prompt))
        try:
            content = response["choices"][0]["message"]["content"]  # type: ignore[index]
            parsed = json.loads(str(content))
            suggestions = parsed.get("suggestions")
            if not isinstance(suggestions, list):
                raise ValueError("suggestions missing")
            return [self._parse_suggestion(item, prompt) for item in suggestions if isinstance(item, dict)]
        except Exception as exc:
            raise RuntimeError("AI provider request failed") from exc

    def _request_with_retries(self, body: dict[str, object]) -> dict[str, object]:
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        url = f"{self._api_base_url}/chat/completions"
        for attempt in range(self._max_retries + 1):
            try:
                return self._post_json(url, body, headers, self._timeout_seconds)
            except json.JSONDecodeError as exc:
                raise RuntimeError("AI provider request failed") from exc
            except HTTPError as exc:
                if attempt >= self._max_retries or exc.code not in {408, 409, 425, 429, 500, 502, 503, 504}:
                    raise RuntimeError("AI provider request failed") from exc
            except (TimeoutError, URLError, OSError) as exc:
                if attempt >= self._max_retries:
                    raise RuntimeError("AI provider request failed") from exc
        raise RuntimeError("AI provider request failed")

    def _build_body(self, prompt: AiPromptInput) -> dict[str, object]:
        source_lines = [
            (
                f"[{index}] {source.document_title} ({source.source_uri or 'no source uri'}), "
                f"score={source.score:.3f}: {source.content}"
            )
            for index, source in enumerate(prompt.rag_sources)
        ]
        user_prompt = "\n".join(
            [
                "Build dispatcher-reviewed Coffee Fix service suggestions.",
                "Write all suggestion titles, content, and rationales in Russian.",
                "Return only JSON with a top-level suggestions array.",
                "Never claim that an action was performed. Suggestions are reviewed by staff.",
                (
                    "Сначала оцени покрытие RAG. Если source chunks отсутствуют, слабо связаны с Problem summary "
                    "или описывают похожий, но другой симптом, не притягивай их к заявке и не используй похожие, "
                    "но другие сценарии как факт. В таком случае работай как RAG gap: гипотезы должны опираться "
                    "на описание клиента, общую ремонтную логику и безопасные уточняющие вопросы; в rationale "
                    "укажи knowledge_gap=true и source_chunk_indexes оставь пустым."
                ),
                (
                    "Если симптом: не включается, перестала включаться, нет питания, не горит дисплей или не реагирует "
                    "на кнопку включения, это no-power/startup triage. Не предлагай проверки помпы, бака воды, пролива, "
                    "дренажного клапана или flow meter, пока клиент не подтвердил, что машина включается и запускает цикл. "
                    "Сначала уточняй розетку, кабель питания, главный выключатель, дисплей/индикаторы, запах гари, "
                    "следы воды и перепад напряжения."
                ),
                (
                    "Если симптом: бьет током, бьёт током, удар током, щиплет током, пробивает на корпус, корпус под "
                    "напряжением или ток при касании - это electrical shock safety triage, не no-power/startup. "
                    "Сначала предложи клиенту не пользоваться кофемашиной, не включать повторно и отключить от сети, "
                    "если это можно сделать безопасно сухими руками. Уточняй заземление розетки, УЗО/автомат, влагу, "
                    "воду под машиной, запах гари, искрение, когда именно бьет током. Не предлагай no-power/startup "
                    "проверки вроде горит ли дисплей, главный выключатель, запуск цикла, проверка помпы или пролива. "
                    "Рекомендуй осмотр мастером по электробезопасности."
                ),
                f"Request number: {prompt.request_number}",
                f"Status: {prompt.status}",
                f"Urgency: {prompt.urgency}",
                f"Customer context: {prompt.customer_context}",
                f"Machine: {prompt.machine_label}",
                f"Location type: {prompt.location_type}",
                f"Problem summary: {prompt.problem_summary}",
                f"Latest timeline title: {prompt.latest_timeline_title or 'none'}",
                f"Clarification state: {prompt.clarification_state}",
                f"Assignment state: {prompt.assignment_state}",
                f"Internal note count: {prompt.internal_note_count}",
                (
                    "RAG coverage: relevant source chunks provided."
                    if source_lines
                    else "RAG coverage: no relevant source chunks."
                ),
                "RAG sources:",
                "\n".join(source_lines) if source_lines else "No source chunks retrieved.",
                "Allowed kinds: intake_classification, diagnostic_question, likely_cause, parts, customer_reply.",
                "Each suggestion must include kind, title, content, rationale, confidence, source_chunk_indexes.",
                "confidence must be a JSON number from 0.0 to 1.0, not a word label.",
            ]
        )
        return {
            "model": self._model,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You help Coffee Fix dispatchers. Produce concise staff-reviewed suggestions only. "
                        "Do not expose secrets or invent completed operational actions."
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }

    def _parse_suggestion(self, item: dict[str, Any], prompt: AiPromptInput) -> AiSuggestionCreate:
        indexes = item.get("source_chunk_indexes")
        source_chunks = []
        if isinstance(indexes, list):
            for index in indexes:
                if isinstance(index, int) and 0 <= index < len(prompt.rag_sources):
                    source_chunks.append(prompt.rag_sources[index])
        return AiSuggestionCreate(
            kind=str(item["kind"]),  # type: ignore[arg-type]
            title=str(item["title"]),
            content=str(item["content"]),
            rationale=str(item["rationale"]),
            confidence=_parse_confidence(item["confidence"]),
            source_chunks=source_chunks,
        )


def _parse_confidence(value: object) -> float:
    if isinstance(value, str):
        normalized = value.strip().lower()
        label_scores = {
            "low": 0.35,
            "medium": 0.6,
            "moderate": 0.6,
            "high": 0.82,
        }
        if normalized in label_scores:
            return label_scores[normalized]
        value = normalized
    parsed = float(value)  # type: ignore[arg-type]
    return max(0.0, min(1.0, parsed))


def _is_electric_shock_report(prompt: AiPromptInput) -> bool:
    text = " ".join(
        [
            prompt.problem_summary,
            prompt.machine_label,
            " ".join(source.content for source in prompt.rag_sources),
        ]
    ).lower()
    markers = (
        "бьет током",
        "бьёт током",
        "удар током",
        "ударило током",
        "щиплет током",
        "пробивает током",
        "пробивает на корпус",
        "корпус под напряжением",
        "ток при касании",
        "при касании ток",
    )
    return any(marker in text for marker in markers)


def _generic_gap_suggestions(prompt: AiPromptInput) -> list[AiSuggestionCreate]:
    problem = prompt.problem_summary.strip() or "симптом не указан"
    return [
        AiSuggestionCreate(
            kind="intake_classification",
            title="Новая тема без покрытия базы знаний",
            content=f"Заявка требует общей диагностики по описанию клиента: {problem}.",
            rationale="Диспетчер видит, что RAG не дал релевантного источника; knowledge_gap=true.",
            confidence=0.62,
        ),
        AiSuggestionCreate(
            kind="diagnostic_question",
            title="Уточнить проявление симптома",
            content=(
                f"По проблеме '{problem}' уточните, когда это происходит, повторяется ли постоянно, "
                "есть ли фото/видео проявления, следы воды, запах гари, шумы или ошибки на дисплее."
            ),
            rationale="Диспетчер собирает базовые признаки без подстановки неподходящего сценария из базы знаний.",
            confidence=0.68,
        ),
        AiSuggestionCreate(
            kind="likely_cause",
            title="Сформировать первичную гипотезу после уточнений",
            content=(
                "Пока база знаний не покрывает эту тему, не фиксируйте конкретную причину. "
                "Сначала отделите условия появления симптома, безопасность, недавнее обслуживание и видимые следы неисправности."
            ),
            rationale="Диспетчер видит предварительную гипотезу без подстановки нерелевантного RAG.",
            confidence=0.55,
        ),
        AiSuggestionCreate(
            kind="parts",
            title="Запчасти не подбирать до уточнений",
            content="Не резервировать детали до ответа клиента или диагностики мастером.",
            rationale="Диспетчер не получает шумную подсказку по деталям без релевантного источника и уточнений.",
            confidence=0.5,
        ),
        AiSuggestionCreate(
            kind="customer_reply",
            title="Черновик ответа клиенту",
            content=(
                "Спасибо, приняли заявку. Уточните, пожалуйста, когда именно проявляется проблема, "
                "и приложите фото или короткое видео, если это возможно."
            ),
            rationale="Диспетчер редактирует и отправляет ответ вручную; AI не отправляет сообщения.",
            confidence=0.66,
        ),
    ]


def _electric_shock_suggestions(source_chunks: list[AiRagSource]) -> list[AiSuggestionCreate]:
    return [
        AiSuggestionCreate(
            kind="customer_reply",
            title="Остановить использование до осмотра",
            content=(
                "Пожалуйста, не пользоваться кофемашиной и не включать ее повторно до осмотра мастером. "
                "Если можно сделать это безопасно сухими руками, отключите вилку от сети."
            ),
            rationale="Диспетчер сначала снижает риск поражения током и не просит клиента продолжать проверки под напряжением.",
            confidence=0.9,
            source_chunks=source_chunks,
        ),
        AiSuggestionCreate(
            kind="diagnostic_question",
            title="Уточнить условия удара током",
            content=(
                "Бьет током при касании корпуса постоянно или только во время нагрева/работы? "
                "Розетка с заземлением, срабатывает ли УЗО или автомат, есть ли вода под машиной, запах гари или искрение?"
            ),
            rationale="Диспетчер собирает признаки утечки на корпус, проблем заземления и влаги без небезопасных действий клиента.",
            confidence=0.86,
            source_chunks=source_chunks,
        ),
        AiSuggestionCreate(
            kind="likely_cause",
            title="Вероятна утечка на корпус или проблема заземления",
            content=(
                "Возможны отсутствие заземления, повреждение сетевого кабеля, влага внутри корпуса, пробой изоляции "
                "ТЭНа или неисправность платы питания. Нужна диагностика мастером по электробезопасности."
            ),
            rationale="Диспетчер использует причину как ориентир для маршрутизации к мастеру, а не как удаленную диагностику.",
            confidence=0.74,
            source_chunks=source_chunks,
        ),
        AiSuggestionCreate(
            kind="parts",
            title="Электроузлы для проверки мастером",
            content="Проверить сетевой кабель, заземление, ТЭН, плату питания, следы влаги и пробой изоляции.",
            rationale="Диспетчер видит концепты узлов; клиенту не предлагается разборка или проверка под напряжением.",
            confidence=0.58,
            source_chunks=source_chunks,
        ),
    ]


def create_ai_suggestion_provider(settings: object) -> AiSuggestionProvider:
    provider_name = str(getattr(settings, "ai_provider", "deterministic")).strip().lower()
    if provider_name == "deterministic":
        return DeterministicAiSuggestionProvider()
    if provider_name == "openai-compatible":
        api_key = str(getattr(settings, "ai_api_key", "")).strip()
        if not api_key:
            raise ValueError("SERVICEOPS_AI_API_KEY is required when SERVICEOPS_AI_PROVIDER=openai-compatible")
        model = str(getattr(settings, "ai_model", "")).strip()
        if not model:
            raise ValueError("SERVICEOPS_AI_MODEL is required when SERVICEOPS_AI_PROVIDER=openai-compatible")
        return OpenAiCompatibleAiSuggestionProvider(
            api_base_url=str(getattr(settings, "ai_api_base_url", "https://api.openai.com/v1")),
            api_key=api_key,
            model=model,
            timeout_seconds=float(getattr(settings, "ai_timeout_seconds", 20.0)),
            max_retries=int(getattr(settings, "ai_max_retries", 2)),
        )
    raise ValueError(f"Unsupported SERVICEOPS_AI_PROVIDER: {provider_name}")
