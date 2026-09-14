from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

DEFAULT_QWEN = "qwen2.5:1.5b"
DEFAULT_GEMINI = "gemini-3.1-flash-lite"
OLLAMA_TIMEOUT = 20
GEMINI_TIMEOUT = 20
PROBE_TIMEOUT = 0.4

SYSTEM = """You are Ludo, a calm Linux guide for people coming from Windows — especially gamers using Steam and Proton.
Answer using ONLY the notes. If the notes are thin, say so and point at a guide topic.
Never pretend you ran a command. Never invent package names. Do not tell anyone to disable security features.
Keep it short: a few sentences, maybe one command. No markdown tables."""


class Brain(Protocol):
    name: str
    label: str

    def complete(self, question: str, context: str, history: list[tuple[str, str]]) -> str: ...


@dataclass(frozen=True)
class OllamaBrain:
    host: str
    model: str
    name: str = "ollama"

    @property
    def label(self) -> str:
        return f"Ollama {self.model}"

    def complete(self, question: str, context: str, history: list[tuple[str, str]]) -> str:
        messages = [{"role": "system", "content": SYSTEM + "\n\nNotes:\n" + context}]
        for role, text in history[-6:]:
            messages.append({"role": "user" if role == "you" else "assistant", "content": text})
        messages.append({"role": "user", "content": question})
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 280},
        }
        data = _post_json(f"{self.host}/api/chat", payload, timeout=OLLAMA_TIMEOUT)
        error = data.get("error")
        if error:
            raise RuntimeError(str(error))
        message = data.get("message") or {}
        text = (message.get("content") or "").strip()
        if not text:
            raise RuntimeError("Ollama returned an empty reply")
        return text


@dataclass(frozen=True)
class GeminiBrain:
    api_key: str
    model: str
    name: str = "gemini"

    @property
    def label(self) -> str:
        return f"Gemini {self.model}"

    def complete(self, question: str, context: str, history: list[tuple[str, str]]) -> str:
        contents: list[dict] = []
        for role, text in history[-6:]:
            contents.append(
                {
                    "role": "user" if role == "you" else "model",
                    "parts": [{"text": text}],
                }
            )
        contents.append({"role": "user", "parts": [{"text": f"Notes:\n{context}\n\nQuestion: {question}"}]})
        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 400},
        }
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        data = _post_json(url, payload, timeout=GEMINI_TIMEOUT)
        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini returned no candidates")
        parts = (((candidates[0] or {}).get("content") or {}).get("parts")) or []
        text = "".join(str(part.get("text") or "") for part in parts).strip()
        if not text:
            raise RuntimeError("Gemini returned an empty reply")
        return text


def detect_backend(choice: str | None = None) -> Brain | None:
    selected = (choice or os.environ.get("LUDO_LLM") or "auto").strip().lower()
    if selected in {"off", "none", "notes", "false", "0"}:
        return None
    if selected in {"gemini", "google"}:
        return _gemini()
    if selected in {"ollama", "qwen", "local"}:
        return _ollama()
    ollama = _ollama_if_up()
    if ollama is not None:
        return ollama
    return _gemini_if_keyed()


def describe_backend(brain: Brain | None) -> str:
    if brain is None:
        return "notes only — ollama pull qwen2.5:1.5b, or set GEMINI_API_KEY"
    return brain.label


def _ollama() -> OllamaBrain:
    return OllamaBrain(host=_ollama_host(), model=_ollama_model())


def _ollama_if_up() -> OllamaBrain | None:
    host = _ollama_host()
    try:
        _get_json(f"{host}/api/tags", timeout=PROBE_TIMEOUT)
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError):
        return None
    return OllamaBrain(host=host, model=_ollama_model())


def _gemini() -> GeminiBrain:
    key = _gemini_key()
    if not key:
        raise RuntimeError("Set GEMINI_API_KEY or GOOGLE_API_KEY to use Gemini.")
    return GeminiBrain(api_key=key, model=_gemini_model())


def _gemini_if_keyed() -> GeminiBrain | None:
    key = _gemini_key()
    if not key:
        return None
    return GeminiBrain(api_key=key, model=_gemini_model())


def _ollama_host() -> str:
    raw = os.environ.get("LUDO_OLLAMA_HOST") or os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434"
    return raw.rstrip("/")


def _ollama_model() -> str:
    return os.environ.get("LUDO_OLLAMA_MODEL") or DEFAULT_QWEN


def _gemini_model() -> str:
    return os.environ.get("LUDO_GEMINI_MODEL") or DEFAULT_GEMINI


def _gemini_key() -> str:
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""


def _get_json(url: str, timeout: float) -> dict:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_json(url: str, payload: dict, timeout: float) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(_short_http_error(exc.code, detail)) from exc


def _short_http_error(code: int, detail: str) -> str:
    lowered = detail.lower()
    if "not found" in lowered or code == 404:
        return f"HTTP {code}: model not found. For Qwen run: ollama pull {DEFAULT_QWEN}"
    if code in {401, 403}:
        return f"HTTP {code}: API key rejected"
    return f"HTTP {code}"
