from pathlib import Path

from ludo.ollama_setup import OllamaStatus, llm_setup_disabled, prompt_copy, should_autostart, should_prompt
from ludo.progress import Progress

MISSING = OllamaStatus(binary=None, running=False, model_present=False, model="qwen2.5:1.5b")
READY = OllamaStatus(
    binary=Path("/usr/bin/ollama"),
    running=True,
    model_present=True,
    model="qwen2.5:1.5b",
)


def test_prompt_when_missing(monkeypatch) -> None:
    monkeypatch.setenv("LUDO_LLM", "auto")
    assert should_prompt(Progress(), MISSING)


def test_no_prompt_when_ready(monkeypatch) -> None:
    monkeypatch.setenv("LUDO_LLM", "auto")
    assert READY.ready
    assert not should_prompt(Progress(), READY)


def test_declined_never_prompts(monkeypatch) -> None:
    monkeypatch.setenv("LUDO_LLM", "auto")
    assert not should_prompt(Progress(ollama_choice="declined"), MISSING)


def test_autostart_only_after_yes(monkeypatch) -> None:
    monkeypatch.setenv("LUDO_LLM", "auto")
    assert not should_autostart(Progress(), MISSING)
    assert should_autostart(Progress(ollama_choice="accepted"), MISSING)


def test_prompt_lists_install_pull_and_start() -> None:
    copy = prompt_copy(MISSING)
    assert "Install Ollama" in copy
    assert "qwen2.5:1.5b" in copy
    assert "Start the Ollama service" in copy
    assert "Yes, set it up" in copy


def test_llm_off_skips_setup() -> None:
    assert llm_setup_disabled()
    assert not should_prompt(Progress(), MISSING)
    assert not should_autostart(Progress(ollama_choice="accepted"), MISSING)
