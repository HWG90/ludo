from pathlib import Path

from ludo.settings import Settings, load_settings, save_settings


def test_settings_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    save_settings(Settings(theme="nord", skip_update="0.2.0"), path)
    loaded = load_settings(path)
    assert loaded.theme == "nord"
    assert loaded.skip_update == "0.2.0"


def test_missing_settings_file(tmp_path: Path) -> None:
    loaded = load_settings(tmp_path / "nope.json")
    assert loaded.theme == "ludo"


def test_corrupt_settings_file(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{not json", encoding="utf-8")
    loaded = load_settings(path)
    assert loaded.theme == "ludo"
