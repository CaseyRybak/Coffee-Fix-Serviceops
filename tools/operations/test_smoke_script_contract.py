from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_smoke_script_uses_current_public_status_endpoints() -> None:
    script = (ROOT / "tools/operations/smoke_test.sh").read_text(encoding="utf-8")

    assert "$api_base/service-requests/$request_number/status" in script
    assert "$api_base/status/$public_token" in script
    assert "$api_base/service-requests/status/$request_number" not in script
    assert "$api_base/service-requests/status/token/$public_token" not in script


if __name__ == "__main__":
    test_smoke_script_uses_current_public_status_endpoints()
