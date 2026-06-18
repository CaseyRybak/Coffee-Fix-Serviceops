from __future__ import annotations

import re
from datetime import datetime

from fastapi import APIRouter, Header, HTTPException, status

from serviceops_api.notifications.models import (
    DeliveryResultPayload,
    DeliveryResultResponse,
    OperationalLowStockAlertResponse,
    OperationalOwnerDailyReportResponse,
    OperationalRequestAlertResponse,
    TelegramOptInLinkPayload,
    TelegramOptInLinkResponse,
)
from serviceops_api.notifications.use_cases import LinkTelegramOptIn, OperationalN8nAutomation, RecordN8nDeliveryResult

WINDOW_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,80}$")


def create_notifications_router(
    record_delivery_result: RecordN8nDeliveryResult,
    callback_secret: str,
    link_telegram_opt_in: LinkTelegramOptIn,
    telegram_bot_api_secret: str,
    operational_automation: OperationalN8nAutomation | None = None,
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

    @router.get("/n8n/operations/sla-reminders", response_model=OperationalRequestAlertResponse)
    async def n8n_sla_reminders(
        now: str | None = None,
        window_key: str | None = None,
        mark_sent: bool = True,
        x_serviceops_callback_secret: str | None = Header(default=None),
    ) -> OperationalRequestAlertResponse:
        _require_operational_access(callback_secret, x_serviceops_callback_secret, operational_automation)
        return operational_automation.sla_reminders(  # type: ignore[union-attr]
            now=_parse_now(now),
            window_key=_parse_window_key(window_key),
            mark_sent=mark_sent,
        )

    @router.get("/n8n/operations/red-alerts", response_model=OperationalRequestAlertResponse)
    async def n8n_red_alerts(
        now: str | None = None,
        window_key: str | None = None,
        mark_sent: bool = True,
        x_serviceops_callback_secret: str | None = Header(default=None),
    ) -> OperationalRequestAlertResponse:
        _require_operational_access(callback_secret, x_serviceops_callback_secret, operational_automation)
        return operational_automation.red_alerts(  # type: ignore[union-attr]
            now=_parse_now(now),
            window_key=_parse_window_key(window_key),
            mark_sent=mark_sent,
        )

    @router.get("/n8n/operations/owner-daily-report", response_model=OperationalOwnerDailyReportResponse)
    async def n8n_owner_daily_report(
        now: str | None = None,
        window_key: str | None = None,
        mark_sent: bool = True,
        x_serviceops_callback_secret: str | None = Header(default=None),
    ) -> OperationalOwnerDailyReportResponse:
        _require_operational_access(callback_secret, x_serviceops_callback_secret, operational_automation)
        return operational_automation.owner_daily_report(  # type: ignore[union-attr]
            now=_parse_now(now),
            window_key=_parse_window_key(window_key),
            mark_sent=mark_sent,
        )

    @router.get("/n8n/operations/low-stock-alerts", response_model=OperationalLowStockAlertResponse)
    async def n8n_low_stock_alerts(
        now: str | None = None,
        window_key: str | None = None,
        mark_sent: bool = True,
        x_serviceops_callback_secret: str | None = Header(default=None),
    ) -> OperationalLowStockAlertResponse:
        _require_operational_access(callback_secret, x_serviceops_callback_secret, operational_automation)
        return operational_automation.low_stock_alerts(  # type: ignore[union-attr]
            now=_parse_now(now),
            window_key=_parse_window_key(window_key),
            mark_sent=mark_sent,
        )

    return router


def _require_operational_access(
    callback_secret: str,
    provided_secret: str | None,
    operational_automation: OperationalN8nAutomation | None,
) -> None:
    if not callback_secret or provided_secret != callback_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid callback secret")
    if operational_automation is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Operational automation is unavailable")


def _parse_now(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.replace("Z", "+00:00")
    if "T" in normalized and " " in normalized:
        head, tail = normalized.rsplit(" ", 1)
        if ":" in tail:
            normalized = f"{head}+{tail}"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid now timestamp") from exc


def _parse_window_key(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not WINDOW_KEY_PATTERN.fullmatch(cleaned):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid window_key")
    return cleaned
