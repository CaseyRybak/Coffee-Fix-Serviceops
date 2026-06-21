from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_restore_script_requires_confirmation_checksum_and_target_guard() -> None:
    script = (ROOT / "tools/operations/postgres_restore.sh").read_text(encoding="utf-8")

    assert "SERVICEOPS_RESTORE_CONFIRM" in script
    assert "I_UNDERSTAND_THIS_WILL_OVERWRITE_TARGET_DB" in script
    assert "sha256sum -c" in script
    assert "SERVICEOPS_ALLOW_PRODUCTION_RESTORE" in script
    assert "restore|drill|test" in script


if __name__ == "__main__":
    test_restore_script_requires_confirmation_checksum_and_target_guard()
