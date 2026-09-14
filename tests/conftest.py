from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolate_ludo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LUDO_LLM", "off")
    monkeypatch.setenv("LUDO_UPDATE", "off")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg-data"))
