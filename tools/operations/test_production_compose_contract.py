from pathlib import Path
import subprocess


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


def test_production_compose_tracks_dokploy_routing_overlay() -> None:
    compose = (ROOT / "docker-compose.production.yml").read_text(encoding="utf-8")
    api = _service_block(compose, "api")
    web = _service_block(compose, "web")
    n8n = _service_block(compose, "n8n")

    assert "traefik.docker.network=dokploy-network" in api
    assert "Host(`${SERVICEOPS_TRAEFIK_API_HOST:-api.coffeefix-demo.online}`)" in api
    assert "dokploy-network" in api
    assert "ports:" not in api

    assert "traefik.docker.network=dokploy-network" in web
    assert "Host(`${SERVICEOPS_TRAEFIK_WEB_HOST:-coffeefix-demo.online}`)" in web
    assert "dokploy-network" in web
    assert "ports:" not in web

    assert "dokploy-network" in n8n
    assert "dokploy-network:\n    external: true" in compose


def test_production_compose_renders_demo_hosts_with_example_env() -> None:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            str(ROOT / ".env.example"),
            "-f",
            str(ROOT / "docker-compose.production.yml"),
            "config",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Host(`api.coffeefix-demo.online`)" in result.stdout
    assert "Host(`coffeefix-demo.online`)" in result.stdout
    assert "Host(`0.0.0.0`)" not in result.stdout


def test_worker_image_runs_as_non_root_user() -> None:
    dockerfile = (ROOT / "apps/worker/Dockerfile").read_text(encoding="utf-8")

    assert "\nUSER serviceops\n" in f"\n{dockerfile}\n"


if __name__ == "__main__":
    test_production_telegram_bot_runs_with_default_compose_profile()
    test_production_n8n_does_not_publish_direct_port()
    test_production_compose_tracks_dokploy_routing_overlay()
    test_production_compose_renders_demo_hosts_with_example_env()
    test_worker_image_runs_as_non_root_user()
