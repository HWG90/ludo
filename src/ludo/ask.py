from __future__ import annotations

import re
from dataclasses import dataclass

from ludo.content.catalog import GUIDES, Guide, get_guide, load_guide_text
from ludo.content.commands import COMMANDS, CommandMap, translate_command
from ludo.content.glossary import GlossaryEntry, search_glossary
from ludo.content.installs import STEAM, pick
from ludo.format import profile_facts, steam_label
from ludo.llm import Brain, detect_backend, model_is_tiny
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
    if _is_chitchat(query):
        return _chitchat_answer()
    notes = answer_from_notes(query, profile)
    if not use_llm:
        return notes
    brain: Brain | None
    if backend is ...:
        brain = detect_backend(llm_choice)
    else:
        brain = backend  # type: ignore[assignment]
    if brain is None or _skip_tiny_llm(brain, notes):
        return notes
    try:
        text = brain.complete(query, _context_pack(query, profile, notes), history or [])
    except Exception:
        return notes
    cleaned = (text or "").strip()
    if not cleaned:
        return notes
    return Answer(cleaned, source=brain.name, guide_id=notes.guide_id, title=notes.title)


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

    if not ranked:
        return _fallback(cleaned)
    ranked.sort(key=lambda item: item[0], reverse=True)
    winner = ranked[0]
    if winner[0] < 8:
        return _fallback(cleaned)
    return winner[1]


def _context_pack(query: str, profile: SystemProfile | None, notes: Answer) -> str:
    chunks = [f"Question: {query}", f"Best local note ({notes.source}):\n{notes.text}"]
    if profile is not None:
        facts = "\n".join(f"{key}: {value}" for key, value in profile_facts(profile)[:8])
        chunks.append("This PC:\n" + facts)
    if notes.guide_id:
        try:
            body = load_guide_text(get_guide(notes.guide_id)).strip()
            chunks.append("Guide excerpt:\n" + body[:1600])
        except OSError:
            pass
    return "\n\n".join(chunks)[:4000]


def _tokens(query: str) -> tuple[str, ...]:
    words = re.findall(r"[a-z0-9+./-]+", query.lower())
    return tuple(word for word in words if word not in _STOP and len(word) > 1)


def _help() -> Answer:
    return Answer(
        "Ask a Windows habit, a command, or something about this PC. "
        "Try “what is Proton”, “ipconfig”, “Task Manager”, or “is Steam installed”. "
        "I answer from Ludo’s guides — I do not run sudo for you.",
        source="help",
        title="Ask Ludo",
    )


def _fallback(query: str) -> Answer:
    return Answer(
        f"I do not have a sharp answer for “{query}” yet. "
        "Try a Windows name (Task Manager, AppData), a command (dir, ipconfig), "
        "or a topic (Steam, Proton, NVIDIA, dual-boot).",
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
        overlap = sum(1 for token in tokens if token in blob or token.replace("-", "") in blob.replace("-", ""))
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


def _is_chitchat(query: str) -> bool:
    cleaned = query.strip().lower().rstrip("!.?")
    return cleaned in _CHITCHAT


def _chitchat_answer() -> Answer:
    return Answer(
        "Ha. Ask a Windows habit, a command, or something about this PC when you want a real answer.",
        source="chat",
        title="Ask Ludo",
    )


def _skip_tiny_llm(brain: object, notes: Answer) -> bool:
    if getattr(brain, "name", "") != "ollama":
        return False
    if not model_is_tiny(str(getattr(brain, "model", ""))):
        return False
    return notes.source in {"miss", "help", "commands", "ludo", "chat", "command"}


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
        "Ludo is this app — a Linux guide for Windows gamers using Steam and Proton.\n\n"
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
