from ludo.ask import answer_question
from ludo.llm import GeminiBrain, OllamaBrain, detect_backend, describe_backend

from tests.helpers import make_profile


class FakeBrain:
    name = "fake"
    label = "fake"

    def complete(self, question: str, context: str, history: list[tuple[str, str]]) -> str:
        assert "ipconfig" in question.lower() or "ip addr" in context.lower()
        return "On Linux that is `ip addr`."


class BoomBrain:
    name = "boom"
    label = "boom"

    def complete(self, question: str, context: str, history: list[tuple[str, str]]) -> str:
        raise RuntimeError("offline")


def test_injected_brain_wins() -> None:
    answer = answer_question("ipconfig", make_profile(), backend=FakeBrain())
    assert answer.source == "fake"
    assert "ip addr" in answer.text


def test_brain_failure_falls_back_to_notes() -> None:
    answer = answer_question("ipconfig", make_profile(), backend=BoomBrain())
    assert answer.source == "command"


def test_use_llm_false_skips_brain() -> None:
    answer = answer_question("ipconfig", make_profile(), use_llm=False, backend=FakeBrain())
    assert answer.source == "command"


def test_detect_off(monkeypatch) -> None:
    monkeypatch.setenv("LUDO_LLM", "off")
    assert detect_backend() is None
    assert "notes only" in describe_backend(None)


def test_detect_gemini_requires_key(monkeypatch) -> None:
    monkeypatch.setenv("LUDO_LLM", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    try:
        detect_backend("gemini")
    except RuntimeError as exc:
        assert "GEMINI_API_KEY" in str(exc)
    else:
        raise AssertionError("expected missing-key error")


def test_detect_gemini_when_keyed(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    brain = detect_backend("gemini")
    assert isinstance(brain, GeminiBrain)
    assert brain.model.startswith("gemini")


def test_ollama_complete(monkeypatch) -> None:
    def fake_post(url: str, payload: dict, timeout: float) -> dict:
        assert url.endswith("/api/chat")
        assert payload["model"] == "qwen2.5:1.5b"
        options = payload["options"]
        assert options["repeat_penalty"] >= 1.3
        assert options["num_predict"] <= 160
        return {"message": {"content": "Use Proton in Steam compatibility."}}

    monkeypatch.setattr("ludo.llm._post_json", fake_post)
    brain = OllamaBrain(host="http://127.0.0.1:11434", model="qwen2.5:1.5b")
    text = brain.complete("what is proton", "note: Proton is Steam's Wine.", [])
    assert "Proton" in text


def test_ollama_rejects_loop(monkeypatch) -> None:
    from ludo.llm import looks_like_loop, tidy_reply

    ramble = (
        "Commands for Ludo include:\n"
        "- `pacman`: For package management.\n"
        "- `lspci`: To check hardware devices.\n"
        "- `lsusb`: To check USB devices.\n"
        "- `lspci` and `lsusb` can help identify missing drivers or firmware issues.\n"
        "- `lspci` and `lsusb` can also show hidden files and file extensions.\n"
        "- `lspci` and `lsusb` can be used to check for missing drivers or firmware issues.\n"
        "- `lspci` and `lsusb` can show hidden files and file extensions.\n"
        "- `lspci` and `lsusb` can help diagnose hardware issues, especially for GPUs and USB devices.\n"
        "- `lspci` and `lsusb` can show hidden files and file extensions.\n"
        "- `lspci` and `lsusb` can help diagnose hardware issues, especially for GPUs and USB devices.\n"
    )
    assert looks_like_loop(ramble, tidy_reply(ramble))

    def fake_post(url: str, payload: dict, timeout: float) -> dict:
        return {"message": {"content": ramble}}

    monkeypatch.setattr("ludo.llm._post_json", fake_post)
    brain = OllamaBrain(host="http://127.0.0.1:11434", model="qwen2.5:1.5b")
    try:
        brain.complete("commands for ludo", "notes: Ludo has a command map.", [])
    except RuntimeError as exc:
        assert "repetitive" in str(exc)
    else:
        raise AssertionError("looping reply should be rejected")


def test_model_is_tiny() -> None:
    from ludo.llm import model_is_tiny, uses_notes_only

    assert model_is_tiny("qwen2.5:1.5b")
    assert model_is_tiny("qwen2.5:3b")
    assert not model_is_tiny("qwen2.5:7b")
    tiny = OllamaBrain(host="http://127.0.0.1:11434", model="qwen2.5:1.5b")
    big = OllamaBrain(host="http://127.0.0.1:11434", model="qwen2.5:7b")
    assert uses_notes_only(tiny)
    assert not uses_notes_only(big)
    assert "too small for Ask" in describe_backend(tiny)


def test_gemini_complete(monkeypatch) -> None:
    def fake_post(url: str, payload: dict, timeout: float) -> dict:
        assert "generateContent" in url
        assert "test-key" in url
        return {"candidates": [{"content": {"parts": [{"text": "Enable Steam Play."}]}}]}

    monkeypatch.setattr("ludo.llm._post_json", fake_post)
    brain = GeminiBrain(api_key="test-key", model="gemini-3.1-flash-lite")
    text = brain.complete("steam", "Steam is installed.", [])
    assert "Steam Play" in text


def test_http_error_model_missing() -> None:
    from ludo.llm import _short_http_error

    message = _short_http_error(404, "model 'qwen2.5:1.5b' not found")
    assert "ollama pull" in message
