import asyncio
import logging

from aiogram import Bot, Dispatcher

from serviceops_telegram_bot.config import BotSettings


async def run_bot(settings: BotSettings | None = None) -> None:
    resolved_settings = settings or BotSettings()
    if not resolved_settings.is_enabled:
        logging.getLogger(__name__).warning("Telegram bot disabled: token is not configured")
        return

    bot = Bot(token=resolved_settings.telegram_bot_token)
    dispatcher = Dispatcher()
    await dispatcher.start_polling(bot)


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()

