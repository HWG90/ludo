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


def test_start_daemon_records_pid_and_stop_signals_it(monkeypatch, tmp_path) -> None:
    import os
    import signal

    import ludo.ollama_setup as setup

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    setup._owned_pid = None
    monkeypatch.setattr(setup, "ollama_is_running", lambda timeout=1: False)

    class FakeProc:
        pid = 4242

    monkeypatch.setattr(setup.subprocess, "Popen", lambda *args, **kwargs: FakeProc())
    monkeypatch.setattr(setup, "_is_ollama_serve", lambda pid: pid == 4242)
    monkeypatch.setattr(setup, "_stop_model_quietly", lambda: None)

    sent: list[tuple[int, int]] = []

    def fake_killpg(pid: int, sig: int) -> None:
        sent.append((pid, sig))

    def fake_kill(pid: int, sig: int) -> None:
        if sig == 0:
            raise ProcessLookupError
        sent.append((pid, sig))

    monkeypatch.setattr(os, "killpg", fake_killpg)
    monkeypatch.setattr(os, "kill", fake_kill)

    setup.start_daemon(Path("/tmp/ollama"))
    assert setup.owned_ollama_pid() == 4242
    assert setup.pidfile_path().read_text() == "4242"

    setup.stop_ludo_ollama()
    assert (4242, signal.SIGTERM) in sent
    assert setup.owned_ollama_pid() is None
    assert not setup.pidfile_path().exists()


def test_stop_leaves_foreign_ollama_alone(monkeypatch, tmp_path) -> None:
    import os

    import ludo.ollama_setup as setup

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    setup._owned_pid = None
    monkeypatch.setattr(setup, "_is_ollama_serve", lambda pid: False)

    called = []
    monkeypatch.setattr(os, "killpg", lambda *args, **kwargs: called.append(args))
    monkeypatch.setattr(os, "kill", lambda *args, **kwargs: called.append(args))

    setup.stop_ludo_ollama()
    assert called == []
