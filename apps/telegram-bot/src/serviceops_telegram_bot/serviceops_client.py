from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from serviceops_telegram_bot.config import BotSettings


PostJson = Callable[[str, dict[str, object], dict[str, str]], dict[str, object]]
AsyncPostJson = Callable[[str, dict[str, object], dict[str, str]], Awaitable[dict[str, object]]]


def post_json(url: str, body: dict[str, object], headers: dict[str, str]) -> dict[str, object]:
    request = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", **headers},
    )
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ServiceOps API request failed with {exc.code}: {detail}") from exc


class ServiceOpsClient:
    def __init__(
        self,
        settings: BotSettings,
        post_json: PostJson = post_json,
        async_post_json: AsyncPostJson | None = None,
    ) -> None:
        self._api_base_url = settings.api_base_url.rstrip("/")
        self._bot_api_secret = settings.bot_api_secret
        self._post_json = post_json
        self._async_post_json = async_post_json

    async def link_opt_in(self, token: str, chat_id: int, username: str | None) -> dict[str, object]:
        url = f"{self._api_base_url}/notifications/telegram/opt-ins/{token}/link"
        body = {"chat_id": chat_id, "username": username}
        headers = {"X-ServiceOps-Telegram-Bot-Secret": self._bot_api_secret}
        if self._async_post_json is not None:
            return await self._async_post_json(url, body, headers)
        return await asyncio.to_thread(
            self._post_json,
            url,
            body,
            headers,
        )
