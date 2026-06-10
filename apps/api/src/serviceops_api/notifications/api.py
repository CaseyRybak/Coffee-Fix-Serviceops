from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, status

from serviceops_api.notifications.models import (
    DeliveryResultPayload,
    DeliveryResultResponse,
    TelegramOptInLinkPayload,
    TelegramOptInLinkResponse,
)
from serviceops_api.notifications.use_cases import LinkTelegramOptIn, RecordN8nDeliveryResult


def create_notifications_router(
    record_delivery_result: RecordN8nDeliveryResult,
    callback_secret: str,
    link_telegram_opt_in: LinkTelegramOptIn,
    telegram_bot_api_secret: str,
) -> APIRouter:
    router = APIRouter(prefix="/notifications", tags=["notifications"])

    @router.post("/n8n/delivery-results", response_model=DeliveryResultResponse)
    async def n8n_delivery_result(
        payload: DeliveryResultPayload,
        x_serviceops_callback_secret: str | None = Header(default=None),
    ) -> DeliveryResultResponse:
        if not callback_secret or x_serviceops_callback_secret != callback_secret:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid callback secret")
        return record_delivery_result.execute(payload)

    @router.post("/telegram/opt-ins/{token}/link", response_model=TelegramOptInLinkResponse)
    async def link_telegram_chat(
        token: str,
        payload: TelegramOptInLinkPayload,
        x_serviceops_telegram_bot_secret: str | None = Header(default=None),
    ) -> TelegramOptInLinkResponse:
        if not telegram_bot_api_secret or x_serviceops_telegram_bot_secret != telegram_bot_api_secret:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram bot secret")
        try:
            return link_telegram_opt_in.execute(token, payload)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telegram opt-in token not found") from exc

    return router
