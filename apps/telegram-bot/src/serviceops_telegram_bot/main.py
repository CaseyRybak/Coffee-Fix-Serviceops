import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from serviceops_telegram_bot.config import BotSettings
from serviceops_telegram_bot.observability import configure_logging
from serviceops_telegram_bot.serviceops_client import ServiceOpsClient


def parse_start_token(text: str | None) -> str | None:
    if not text:
        return None
    parts = text.strip().split(maxsplit=1)
    if len(parts) != 2 or parts[0] != "/start":
        return None
    token = parts[1].strip()
    return token or None


def build_linked_request_message(linked: dict[str, object], public_api_base_url: str) -> str:
    public_status_url = str(linked["public_status_url"])
    if public_status_url.startswith("/"):
        public_status_url = f"{public_api_base_url.rstrip('/')}{public_status_url}"
    return "\n".join(
        [
            "Telegram-уведомления подключены.",
            f"Заявка: {linked['request_number']}",
            f"Статус: {linked['status']}",
            f"Кофемашина: {linked['machine_label']}",
            f"Страница статуса: {public_status_url}",
        ]
    )


def register_handlers(dispatcher: Dispatcher, serviceops: ServiceOpsClient, settings: BotSettings) -> None:
    @dispatcher.message(CommandStart())
    async def start(message: Message) -> None:
        token = parse_start_token(message.text)
        if token is None:
            await message.answer("Откройте ссылку подключения Telegram со страницы статуса заявки.")
            return
        if message.chat is None:
            await message.answer("Не удалось определить Telegram chat id.")
            return
        try:
            linked = await serviceops.link_opt_in(
                token=token,
                chat_id=message.chat.id,
                username=message.from_user.username if message.from_user else None,
            )
        except Exception:
            logging.getLogger(__name__).exception("Telegram opt-in link failed")
            await message.answer("Не удалось подключить уведомления. Проверьте ссылку или попробуйте позже.")
            return
        await message.answer(build_linked_request_message(linked, settings.public_api_base_url))


async def run_bot(settings: BotSettings | None = None) -> None:
    resolved_settings = settings or BotSettings()
    configure_logging(
        service_name="serviceops-telegram-bot",
        environment=resolved_settings.environment,
    )
    if not resolved_settings.is_enabled:
        logging.getLogger(__name__).warning("Telegram bot disabled: token is not configured")
        return

    bot = Bot(token=resolved_settings.telegram_bot_token)
    dispatcher = Dispatcher()
    register_handlers(dispatcher, ServiceOpsClient(resolved_settings), resolved_settings)
    await dispatcher.start_polling(bot)


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
