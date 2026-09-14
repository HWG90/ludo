from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

DEFAULT_QWEN = "qwen2.5:7b"
DEFAULT_GEMINI = "gemini-3.1-flash-lite"
OLLAMA_TIMEOUT = 120
GEMINI_TIMEOUT = 120
PROBE_TIMEOUT = 0.4
TINY_BILLION_PARAMS = 3.0
_LINE_STOP = frozenset(
    """
    a an and are as at be but by can could do for from help in is it its of on or
    the this to up used with also show check
    """.split()
)

SYSTEM = """You are Ludo, a clear, practical assistant for people moving from Windows to Linux on their own PC.

Talk like a knowledgeable enthusiast helping a friend, not a marketer and not a gamer-bro. Steam and games are fine when asked about; they are not the whole story.

Do:
- Answer the actual question in your own words.
- Use the computer facts when the question is about this machine.
- Be honest when you are unsure. Prefer official docs (Arch Wiki, distro docs, man pages) over guessing.
- Never pretend you ran a command on the user's PC. Never tell anyone to disable security features.

Don't:
- Recite a glossary entry or dump a Windows→Linux Rosetta stone unless they asked for that.
- Pad with repeated bullets or unrelated hostname/user trivia.
- Use slang like “gg”, “skill issue”, “the penguin”, or similar.

Finish the answer. If you start a numbered list or a set of steps, complete it. No markdown tables."""

_OLLAMA_OPTIONS = {
    "temperature": 0.65,
    "top_p": 0.9,
    "repeat_penalty": 1.15,
    "repeat_last_n": 128,
    "num_predict": 4096,
}


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
        system = SYSTEM
        if context.strip():
            system = SYSTEM + "\n\n" + context
        messages = [{"role": "system", "content": system}]
        for role, text in _usable_history(history):
            messages.append({"role": "user" if role == "you" else "assistant", "content": text})
        messages.append({"role": "user", "content": question})
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": dict(_OLLAMA_OPTIONS),
        }
        data = _post_json(f"{self.host}/api/chat", payload, timeout=_ollama_timeout(self.model))
        error = data.get("error")
        if error:
            raise RuntimeError(str(error))
        message = data.get("message") or {}
        return _finalize_reply(message.get("content") or "")


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
        for role, text in _usable_history(history):
            contents.append(
                {
                    "role": "user" if role == "you" else "model",
                    "parts": [{"text": text}],
                }
            )
        contents.append({"role": "user", "parts": [{"text": question}]})
        system = SYSTEM
        if context.strip():
            system = SYSTEM + "\n\n" + context
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.65, "maxOutputTokens": 4096},
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
        return _finalize_reply("".join(str(part.get("text") or "") for part in parts))


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
        return "notes only — ollama pull qwen2.5:7b, or set GEMINI_API_KEY"
    if uses_notes_only(brain):
        return f"{brain.label} — too small for Ask, using notes"
    return brain.label


def uses_notes_only(brain: object | None) -> bool:
    if brain is None:
        return True
    if getattr(brain, "name", "") != "ollama":
        return False
    return model_is_tiny(str(getattr(brain, "model", "")))


def ollama_host() -> str:
    return _ollama_host()


def ollama_model() -> str:
    return _ollama_model()


def ollama_is_running(timeout: float = PROBE_TIMEOUT) -> bool:
    try:
        _get_json(f"{_ollama_host()}/api/tags", timeout=timeout)
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError, ValueError):
        return False
    return True


def ollama_model_names() -> list[str]:
    return [name for name, _size in list_local_model_info()]


def list_local_model_info() -> list[tuple[str, int]]:
    try:
        data = _get_json(f"{_ollama_host()}/api/tags", timeout=1.5)
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError, ValueError):
        data = None
    rows: list[tuple[str, int]] = []
    if isinstance(data, dict):
        for item in data.get("models") or []:
            name = str(item.get("name") or item.get("model") or "")
            if not name:
                continue
            try:
                size = int(item.get("size") or 0)
            except (TypeError, ValueError):
                size = 0
            rows.append((name, size))
    if rows:
        return _unique_model_info(rows)
    from ludo.ollama_setup import list_models_on_disk

    return [(name, 0) for name in list_models_on_disk()]


def resolve_ollama_model(installed: list[str] | None = None) -> str:
    env = (os.environ.get("LUDO_OLLAMA_MODEL") or "").strip()
    if env:
        return env
    from ludo.settings import load_settings

    saved = load_settings().ollama_model.strip()
    names = list(installed) if installed is not None else ollama_model_names()
    if saved:
        return saved
    picked = pick_installed_model(names)
    return picked or DEFAULT_QWEN


def pick_installed_model(names: list[str]) -> str:
    if not names:
        return ""
    for name in names:
        if name.lower() == DEFAULT_QWEN.lower() or name.lower().startswith(DEFAULT_QWEN.lower()):
            return name
    usable = [name for name in names if not model_is_tiny(name)] or list(names)
    return max(usable, key=_model_rank)


def model_param_billions(model: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*b\b", model.lower())
    if match is None:
        return None
    return float(match.group(1))


def model_is_tiny(model: str) -> bool:
    size = model_param_billions(model)
    if size is None:
        return False
    return size <= TINY_BILLION_PARAMS


def _model_rank(name: str) -> tuple[float, str]:
    return (model_param_billions(name) or 0.0, name.lower())


def _unique_model_info(rows: list[tuple[str, int]]) -> list[tuple[str, int]]:
    seen: dict[str, int] = {}
    for name, size in rows:
        key = name.lower()
        if key not in seen or size > seen[key]:
            seen[key] = size
    by_lower = {name.lower(): name for name, _size in rows}
    ordered = sorted(by_lower, key=str)
    return [(by_lower[key], seen[key]) for key in ordered]


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
    return resolve_ollama_model()


def _gemini_model() -> str:
    return os.environ.get("LUDO_GEMINI_MODEL") or DEFAULT_GEMINI


def _gemini_key() -> str:
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""


def tidy_reply(text: str) -> str:
    kept: list[str] = []
    seen: list[str] = []
    nonempty = 0
    for raw_line in text.replace("\r\n", "\n").split("\n"):
        stripped = raw_line.strip()
        if not stripped:
            if kept and kept[-1] != "":
                kept.append("")
            continue
        norm = _normalize_line(stripped)
        if any(_similar_line(norm, previous) for previous in seen):
            continue
        seen.append(norm)
        kept.append(stripped)
        nonempty += 1
        if nonempty >= 200:
            break
    while kept and kept[-1] == "":
        kept.pop()
    return "\n".join(kept).strip()


def looks_like_loop(raw: str, cleaned: str | None = None) -> bool:
    raw_lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if len(raw_lines) < 5:
        return False
    tidied = cleaned if cleaned is not None else tidy_reply(raw)
    kept = [line.strip() for line in tidied.splitlines() if line.strip()]
    dropped = len(raw_lines) - len(kept)
    if dropped >= 3 and len(kept) <= len(raw_lines) * 0.7:
        return True
    norms = [_normalize_line(line) for line in raw_lines]
    token_hits: dict[str, int] = {}
    for norm in norms:
        if len(norm) < 24:
            continue
        copies = sum(1 for other in norms if _similar_line(norm, other))
        if copies >= 4:
            return True
        for token in _content_tokens(norm):
            token_hits[token] = token_hits.get(token, 0) + 1
    return sum(1 for count in token_hits.values() if count >= 4) >= 2


def _usable_history(history: list[tuple[str, str]]) -> list[tuple[str, str]]:
    usable: list[tuple[str, str]] = []
    for role, text in history:
        stripped = (text or "").strip()
        if not stripped or stripped in {"Thinking…", "Thinking..."}:
            continue
        if role != "you" and looks_like_loop(stripped):
            continue
        usable.append((role, stripped))
    return usable[-12:]


def _ollama_timeout(model: str) -> float:
    size = model_param_billions(model) or 7.0
    return min(480.0, max(float(OLLAMA_TIMEOUT), size * 12.0))


def _finalize_reply(text: str) -> str:
    raw = (text or "").strip()
    if not raw:
        raise RuntimeError("empty reply")
    return _collapse_blank_lines(raw)


def _collapse_blank_lines(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    kept: list[str] = []
    blank = 0
    for line in lines:
        if line.strip():
            kept.append(line)
            blank = 0
            continue
        blank += 1
        if blank <= 1:
            kept.append("")
    while kept and kept[-1] == "":
        kept.pop()
    return "\n".join(kept).strip()


def _normalize_line(line: str) -> str:
    text = re.sub(r"^[-*•]+\s+", "", line.strip())
    text = re.sub(r"`+", "", text)
    return re.sub(r"\s+", " ", text).lower()


def _content_tokens(line: str) -> set[str]:
    return {token for token in line.split() if token not in _LINE_STOP and len(token) > 2}


def _similar_line(left: str, right: str) -> bool:
    if left == right:
        return True
    if len(left) > 20 and len(right) > 20 and (left in right or right in left):
        return True
    left_tokens = _content_tokens(left)
    right_tokens = _content_tokens(right)
    if min(len(left_tokens), len(right_tokens)) < 2:
        return False
    overlap = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    return union > 0 and overlap / union >= 0.5


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
