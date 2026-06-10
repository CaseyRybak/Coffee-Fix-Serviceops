from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_smoke_script_uses_current_public_status_endpoints() -> None:
    script = (ROOT / "tools/operations/smoke_test.sh").read_text(encoding="utf-8")

    assert "$api_base/service-requests/$request_number/status" in script
    assert "$api_base/status/$public_token" in script
    assert "$api_base/service-requests/status/$request_number" not in script
    assert "$api_base/service-requests/status/token/$public_token" not in script


def test_smoke_script_supports_staff_login_without_printing_password() -> None:
    script = (ROOT / "tools/operations/smoke_test.sh").read_text(encoding="utf-8")

    assert "SERVICEOPS_SMOKE_STAFF_USERNAME" in script
    assert "SERVICEOPS_SMOKE_STAFF_PASSWORD" in script
    assert "$api_base/staff/login" in script
    assert "$api_base/dispatcher/service-requests" in script
    assert "printf '%s' \"$SERVICEOPS_SMOKE_STAFF_PASSWORD\"" not in script
    assert "printf '%s\\n' \"$SERVICEOPS_SMOKE_STAFF_PASSWORD\"" not in script


def test_smoke_script_uses_current_intake_payload_contract() -> None:
    script = (ROOT / "tools/operations/smoke_test.sh").read_text(encoding="utf-8")

    assert '"client_type": "private"' in script
    assert '"location_type": "office"' in script
    assert '"problem": "Smoke test request"' in script
    assert '"urgency": "planned"' in script
    assert "problem_description" not in script
    assert '"urgency": "standard"' not in script


def test_smoke_script_reads_public_token_from_status_response() -> None:
    script = (ROOT / "tools/operations/smoke_test.sh").read_text(encoding="utf-8")
    create_response_parse = script.split('request_number="$(printf', 1)[0]

    assert 'print(payload["request_number"])' in script
    assert 'print(payload["public_token"])' not in create_response_parse
    assert "status_response" in script
    assert 'public_token="$(' in script
    assert 'RESPONSE_JSON="$status_response"' in script


if __name__ == "__main__":
    test_smoke_script_uses_current_public_status_endpoints()
    test_smoke_script_supports_staff_login_without_printing_password()
    test_smoke_script_uses_current_intake_payload_contract()
    test_smoke_script_reads_public_token_from_status_response()
