from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _service_block(compose_text: str, service_name: str) -> str:
    marker = f"  {service_name}:\n"
    start = compose_text.index(marker)
    next_service = compose_text.find("\n  ", start + len(marker))
    while next_service != -1 and compose_text[next_service + 3 : next_service + 4] == " ":
        next_service = compose_text.find("\n  ", next_service + 1)
    return compose_text[start:] if next_service == -1 else compose_text[start:next_service]


def test_production_telegram_bot_runs_with_default_compose_profile() -> None:
    compose = (ROOT / "docker-compose.production.yml").read_text(encoding="utf-8")
    telegram_bot = _service_block(compose, "telegram-bot")

    assert "profiles:" not in telegram_bot


def test_production_n8n_does_not_publish_direct_port() -> None:
    compose = (ROOT / "docker-compose.production.yml").read_text(encoding="utf-8")
    n8n = _service_block(compose, "n8n")

    assert "ports:" not in n8n
    assert "5678:5678" not in n8n


if __name__ == "__main__":
    test_production_telegram_bot_runs_with_default_compose_profile()
    test_production_n8n_does_not_publish_direct_port()
