from serviceops_telegram_bot.config import BotSettings


def test_bot_is_disabled_without_token() -> None:
    settings = BotSettings(telegram_bot_token="")

    assert settings.is_enabled is False


def test_bot_is_enabled_with_token() -> None:
    settings = BotSettings(telegram_bot_token="test-token")

    assert settings.is_enabled is True
