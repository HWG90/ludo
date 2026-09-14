import pytest


@pytest.fixture(autouse=True)
def _default_offline_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LUDO_LLM", "off")
