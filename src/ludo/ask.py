from __future__ import annotations

import re
from dataclasses import dataclass

from ludo.content.catalog import GUIDES, Guide
from ludo.content.commands import COMMANDS, CommandMap, translate_command
from ludo.content.glossary import GlossaryEntry, search_glossary
from ludo.content.installs import APPS, STEAM, AppInstall, pick
from ludo.format import profile_facts, steam_label
from ludo.llm import Brain, detect_backend, uses_notes_only
from ludo.probe import SystemProfile
from ludo.recommend import recommend

_STOP = frozenset(
    """
    a an and are as at be but by can could do does for from how i if in into is
    it its me my of on or please so tell that the this to up what when where
    which who why will with would you your
    """.split()
)

_CHITCHAT = frozenset(
    {
        "lol",
        "lmao",
        "haha",
        "hahaha",
        "heh",
        "ok",
        "okay",
        "k",
        "kk",
        "thanks",
        "thank you",
        "ty",
        "thx",
        "nice",
        "cool",
        "wow",
        "yo",
        "sup",
        "nm",
        "bruh",
    }
)

_COMMAND_OVERVIEW = (
    "dir",
    "cls",
    "ipconfig",
    "tasklist",
    "taskkill",
    "copy",
    "del",
    "dxdiag",
)

_IDENTITY_HINTS = frozenset({"hostname", "username", "whoami"})
_IDENTITY_PHRASES = (
    "system name",
    "computer name",
    "pc name",
    "device name",
    "machine name",
    "host name",
    "my hostname",
    "my username",
    "user name",
    "account name",
    "who am i",
)

_MACHINE_HINTS = frozenset(
    {
        "gpu",
        "graphics",
        "nvidia",
        "amd",
        "intel",
        "vulkan",
        "steam",
        "proton",
        "distro",
        "distribution",
        "kernel",
        "ram",
        "memory",
        "checkup",
        "hardware",
        "pc",
        "machine",
        "computer",
        "installed",
        "driver",
        "drivers",
        "flatpak",
        "mangohud",
        "gamemode",
        "gamescope",
    }
)


@dataclass(frozen=True)
class Answer:
    text: str
    source: str
    guide_id: str | None = None
    title: str | None = None


def answer_question(
    query: str,
    profile: SystemProfile | None = None,
    *,
    use_llm: bool = True,
    backend: Brain | None | object = ...,
    history: list[tuple[str, str]] | None = None,
    llm_choice: str | None = None,
) -> Answer:
    brain: Brain | None
    if backend is ...:
        brain = detect_backend(llm_choice) if use_llm else None
    else:
        brain = backend  # type: ignore[assignment]
        if not use_llm:
            brain = None
    if brain is not None and not uses_notes_only(brain):
        try:
            text = brain.complete(query, _chat_context(profile), history or [])
        except Exception as exc:
            detail = str(exc).strip() or exc.__class__.__name__
            return Answer(
                f"The model did not answer ({detail}). Try again, or pick another model with Ctrl+O.",
                source="error",
            )
        cleaned = (text or "").strip()
        if not cleaned:
            return Answer(
                "The model returned an empty reply. Try again, or pick another model with Ctrl+O.",
                source="error",
            )
        return Answer(cleaned, source=brain.name)
    if _is_chitchat(query):
        return _chitchat_answer()
    return answer_from_notes(query, profile)


def answer_from_notes(query: str, profile: SystemProfile | None = None) -> Answer:
    cleaned = " ".join(query.strip().split())
    if not cleaned:
        return _help()
    lowered = cleaned.lower()
    if lowered in {"help", "?", "hi", "hello", "hey"}:
        return _help()

    tokens = _tokens(cleaned)
    command = _best_command(cleaned, tokens)
    glossary = _best_glossary(cleaned, tokens)
    guide = _best_guide(cleaned, tokens)
    machine_score = _machine_score(tokens, lowered)
    ludo_score = _ludo_score(tokens, lowered)
    commands_score = 0 if command else _commands_overview_score(tokens, lowered)
    app = _best_app(cleaned, tokens, profile)

    ranked: list[tuple[int, Answer]] = []
    if command:
        ranked.append(command)
    if glossary:
        ranked.append(glossary)
    if guide:
        ranked.append(guide)
    if machine_score and profile is not None:
        ranked.append((machine_score, _machine_answer(cleaned, profile)))
    if ludo_score:
        ranked.append((ludo_score, _ludo_answer()))
    if commands_score:
        ranked.append((commands_score, _commands_overview()))
    if app:
        ranked.append(app)

    if not ranked:
        return _fallback(cleaned)
    ranked.sort(key=lambda item: item[0], reverse=True)
    winner = ranked[0]
    if winner[0] < 8:
        return _fallback(cleaned)
    return winner[1]


def _chat_context(profile: SystemProfile | None) -> str:
    if profile is None:
        return ""
    facts = "\n".join(f"{key}: {value}" for key, value in profile_facts(profile)[:10])
    return "Facts about this computer (use when the question is about this PC):\n" + facts


def _tokens(query: str) -> tuple[str, ...]:
    words = re.findall(r"[a-z0-9+./-]+", query.lower())
    return tuple(word for word in words if word not in _STOP and len(word) > 1)


def _help() -> Answer:
    return Answer(
        "Ask about Linux, this PC, or a Windows habit you want to map over. "
        "Try “Task Manager”, “ipconfig”, “how do I update”, or “what is my hostname”. "
        "I will not run sudo for you.",
        source="help",
        title="Ask Ludo",
    )


def _fallback(query: str) -> Answer:
    return Answer(
        f"I do not have a sharp built-in note for “{query}” yet. "
        "Try a Windows name (Task Manager, AppData), a command (dir, ipconfig), "
        "or a topic (updates, NVIDIA, dual-boot, this GPU).",
        source="miss",
    )


def _best_command(query: str, tokens: tuple[str, ...]) -> tuple[int, Answer] | None:
    hits = translate_command(query)
    if not hits and tokens:
        hits = translate_command(tokens[0])
    if not hits:
        return None
    entry = hits[0]
    score = _command_score(query, tokens, entry)
    if score < 10:
        return None
    extra = ""
    if len(hits) > 1:
        extra = "\nAlso: " + "; ".join(f"{item.windows} → {item.linux}" for item in hits[1:3])
    text = f"Windows `{entry.windows}` is `{entry.linux}` on Linux.\n\n{entry.note}{extra}"
    return score, Answer(text, source="command", title=entry.windows)


def _command_score(query: str, tokens: tuple[str, ...], entry: CommandMap) -> int:
    needle = query.strip().lower()
    names = {entry.windows.lower(), entry.linux.lower(), *(alias.lower() for alias in entry.aliases)}
    first = {name.split()[0] for name in names}
    if needle in names:
        return 100
    if tokens and tokens[0] in first:
        return 90
    blob = f"{entry.windows} {entry.linux} {entry.note}".lower()
    overlap = sum(1 for token in tokens if token in blob)
    return overlap * 8


def _best_glossary(query: str, tokens: tuple[str, ...]) -> tuple[int, Answer] | None:
    hits = search_glossary(query)
    if not hits and tokens:
        seen: list[GlossaryEntry] = []
        found: set[str] = set()
        for token in tokens:
            for entry in search_glossary(token):
                if entry.windows not in found:
                    found.add(entry.windows)
                    seen.append(entry)
        hits = seen
    if not hits:
        return None
    entry = hits[0]
    blob = f"{entry.windows} {entry.linux} {entry.why} {' '.join(entry.tags)}".lower()
    overlap = sum(1 for token in tokens if token in blob)
    score = 24 + overlap * 10
    if query.strip().lower() in entry.windows.lower():
        score += 40
    extra = ""
    if len(hits) > 1:
        extra = "\n\nRelated: " + ", ".join(item.windows for item in hits[1:3])
    text = f"{entry.windows}\nLinux: {entry.linux}\n\n{entry.why}{extra}"
    return score, Answer(text, source="glossary", title=entry.windows)


def _best_guide(query: str, tokens: tuple[str, ...]) -> tuple[int, Answer] | None:
    if not tokens:
        return None
    scored: list[tuple[int, Guide]] = []
    for guide in GUIDES:
        blob = " ".join((guide.id, guide.title, guide.summary, guide.windows_hook, guide.section)).lower()
        overlap = sum(1 for token in tokens if _blob_has_token(blob, token))
        bonus = 0
        id_parts = set(guide.id.split("-"))
        if guide.id.replace("-", " ") in query.lower() or guide.id in query.lower():
            bonus += 40
        if id_parts & set(tokens):
            bonus += 36
        if any(token in guide.id for token in tokens):
            bonus += 12
        score = overlap * 12 + bonus
        if score:
            scored.append((score, guide))
    if not scored:
        return None
    scored.sort(key=lambda item: item[0], reverse=True)
    score, guide = scored[0]
    text = (
        f"{guide.title}\n\n{guide.summary}\n\n"
        f"Windows habit: {guide.windows_hook}\n\n"
        f"Open the {guide.minutes}-minute guide for the rest."
    )
    return score, Answer(text, source="guide", guide_id=guide.id, title=guide.title)


def _machine_score(tokens: tuple[str, ...], lowered: str) -> int:
    if _is_identity_query(lowered, tokens):
        return 110
    hits = sum(1 for token in tokens if token in _MACHINE_HINTS)
    phrases = ("this pc", "this machine", "my pc", "my computer", "do i have", "is steam")
    if any(phrase in lowered for phrase in phrases):
        hits += 2
    if not hits:
        return 0
    return 18 + hits * 14


def _machine_answer(query: str, profile: SystemProfile) -> Answer:
    lowered = query.lower()
    facts = dict(profile_facts(profile))
    if _is_identity_query(lowered, _tokens(query)):
        host = profile.hostname or "unknown"
        user = profile.username or "unknown"
        home = f"/home/{user}" if user != "unknown" else "~"
        return Answer(
            f"This PC’s hostname is `{host}`.\n"
            f"Your Linux user is `{user}` (home folder `{home}`).\n"
            "Windows called these the computer name and the account name. "
            "`hostname` and `whoami` print the same thing.",
            source="machine",
            title=host if host != "unknown" else "This PC",
        )
    if any(word in lowered for word in ("steam", "proton")):
        install = pick(STEAM, profile)
        extra = "" if profile.steam.installed else f"\nWhen you are ready: {install}"
        return Answer(
            f"Steam on this PC: {steam_label(profile.steam)}.{extra}\n"
            "Enable Steam Play for all titles in Steam → Settings → Compatibility.",
            source="machine",
            guide_id="steam-proton",
            title="Steam on this PC",
        )
    if any(word in lowered for word in ("gpu", "graphics", "nvidia", "amd", "intel", "vulkan", "driver")):
        return Answer(
            f"GPU: {facts['GPU']}\nVulkan: {facts['Vulkan']}\n"
            "AMD and Intel usually ride Mesa. NVIDIA wants the distro’s proprietary driver.",
            source="machine",
            guide_id="gpu",
            title="Graphics on this PC",
        )
    lines = "\n".join(f"{key}: {value}" for key, value in profile_facts(profile)[:8])
    recs = recommend(profile)
    follow = f"\n\nNext: {recs[0].title}. {recs[0].detail}" if recs else ""
    return Answer(
        f"This machine:\n{lines}{follow}",
        source="machine",
        title=profile.distro_name,
        guide_id=recs[0].guide_id if recs else None,
    )


def _is_identity_query(lowered: str, tokens: tuple[str, ...]) -> bool:
    if any(phrase in lowered for phrase in _IDENTITY_PHRASES):
        return True
    return any(token in _IDENTITY_HINTS for token in tokens)


def _blob_has_token(blob: str, token: str) -> bool:
    if len(token) <= 4:
        return re.search(rf"\b{re.escape(token)}\b", blob) is not None
    return token in blob or token.replace("-", "") in blob.replace("-", "")


def _is_chitchat(query: str) -> bool:
    cleaned = query.strip().lower().rstrip("!.?")
    return cleaned in _CHITCHAT


def _chitchat_answer() -> Answer:
    return Answer(
        "Sure. Ask about Linux, this PC, or a Windows habit when you want a real answer.",
        source="chat",
        title="Ask Ludo",
    )


def _best_app(
    query: str, tokens: tuple[str, ...], profile: SystemProfile | None
) -> tuple[int, Answer] | None:
    lowered = query.lower()
    scored: list[tuple[int, AppInstall]] = []
    for app in APPS:
        names = (app.name.lower(), *app.aliases)
        if not any(name in lowered for name in names):
            continue
        score = 72
        if any(word in lowered for word in ("install", "download", "get", "where")):
            score += 24
        scored.append((score, app))
    if not scored:
        return None
    scored.sort(key=lambda item: (item[0], len(item[1].name)), reverse=True)
    score, app = scored[0]
    command = pick(app.command, profile) if profile is not None else app.command.get("generic", "")
    flatpak = app.command.get("generic", "")
    extra = ""
    if command and flatpak and command != flatpak and "flatpak" in flatpak:
        extra = f"\nEverywhere else: `{flatpak}`"
    text = (
        f"{app.name} on Linux is a Linux app. Do not run the Windows installer.\n\n"
        f"On this PC: `{command}`{extra}\n\n{app.note}"
    )
    return score, Answer(text, source="app", title=app.name, guide_id=app.guide_id)


def _ludo_score(tokens: tuple[str, ...], lowered: str) -> int:
    if "ludo" not in tokens and "ludo" not in lowered:
        return 0
    score = 22
    if any(token in {"command", "commands", "cli", "help", "app"} for token in tokens):
        score += 40
    stripped = lowered.strip().rstrip("?.!")
    if stripped in {"ludo", "what is ludo", "what's ludo", "whats ludo"}:
        score += 50
    return score


def _ludo_answer() -> Answer:
    return Answer(
        "Ludo is this app — a Linux guide for people coming from Windows.\n\n"
        "Commands for Ludo itself:\n"
        "- `ludo` — open this UI\n"
        "- `ludo checkup` — scan this PC\n"
        "- `ludo glossary` — Windows word → Linux\n"
        "- `ludo translate ipconfig` — Windows command → Linux\n"
        "- `ludo ask …` — ask from the terminal\n"
        "- `ludo update` — pull a newer copy\n\n"
        "The Commands tab is a Windows → Linux map. Ask one name like “ipconfig” or “Task Manager”.",
        source="ludo",
        title="Ludo",
    )


def _commands_overview_score(tokens: tuple[str, ...], lowered: str) -> int:
    if "commands" in tokens or "cmds" in tokens:
        return 28
    if "rosetta" in tokens:
        return 22
    if "what can i type" in lowered:
        return 22
    return 0


def _commands_overview() -> Answer:
    by_windows = {entry.windows.lower(): entry for entry in COMMANDS}
    lines: list[str] = []
    for name in _COMMAND_OVERVIEW:
        entry = by_windows.get(name)
        if entry is not None:
            lines.append(f"- `{entry.windows}` → `{entry.linux}`")
    text = (
        "Windows command → Linux, from Ludo’s map — not a random cheat sheet:\n\n"
        + "\n".join(lines)
        + "\n\nAsk one of those names for the note that goes with it, or open the Commands tab."
    )
    return Answer(text, source="commands", title="Commands")
