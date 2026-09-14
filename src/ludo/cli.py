from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from ludo import __version__


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ludo",
        description="Interactive Linux guide for people coming from Windows — especially gamers.",
    )
    parser.add_argument("--version", action="version", version=f"ludo {__version__}")
    sub = parser.add_subparsers(dest="cmd")

    check = sub.add_parser("checkup", help="Probe this machine and print a Windows-friendly report")
    check.add_argument("--json", action="store_true", help="Machine-readable output")

    gloss = sub.add_parser("glossary", help="Look up a Windows term")
    gloss.add_argument("query", nargs="?", default="", help="Search text, or omit to list all")

    trans = sub.add_parser("translate", help="Translate a Windows command to Linux")
    trans.add_argument("command", nargs="+", help="e.g. ipconfig, dir, taskkill")

    ask = sub.add_parser("ask", help="Ask a Windows-to-Linux question")
    ask.add_argument("question", nargs="+", help="e.g. what is Proton, ipconfig, is Steam installed")
    ask.add_argument(
        "--llm",
        choices=["auto", "ollama", "qwen", "gemini", "off"],
        default=None,
        help="Qwen via Ollama, Gemini, or notes only (default: auto)",
    )

    sub.add_parser("llm", help="Show which chat model Ludo would use")

    sub.add_parser("guides", help="List built-in guides")
    sub.add_parser("tui", help="Open the interactive terminal UI (default)")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd in (None, "tui"):
        from ludo.app import run

        run()
        return 0
    if args.cmd == "checkup":
        return _cmd_checkup(json_mode=args.json)
    if args.cmd == "glossary":
        return _cmd_glossary(args.query)
    if args.cmd == "translate":
        return _cmd_translate(" ".join(args.command))
    if args.cmd == "ask":
        return _cmd_ask(" ".join(args.question), llm=args.llm)
    if args.cmd == "llm":
        return _cmd_llm()
    if args.cmd == "guides":
        return _cmd_guides()
    parser.print_help()
    return 1


def _cmd_checkup(*, json_mode: bool) -> int:
    from ludo.format import profile_facts, profile_to_dict
    from ludo.probe import probe
    from ludo.recommend import recommend

    profile = probe()
    if json_mode:
        payload = profile_to_dict(profile)
        payload["recommendations"] = [
            {"level": item.level, "title": item.title, "detail": item.detail, "guide": item.guide_id}
            for item in recommend(profile)
        ]
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
    table.add_column(style="bold #e6c36a")
    table.add_column(style="#f5e6c8")
    for key, value in profile_facts(profile):
        table.add_row(key, value)
    console.print(Panel(table, title="[bold]Ludo checkup[/]", border_style="#c9a227"))
    console.print()
    for item in recommend(profile):
        color = {"good": "green", "next": "yellow", "warn": "red"}.get(item.level, "white")
        console.print(f"[{color}]●[/{color}] [bold]{item.title}[/bold]")
        console.print(f"   {item.detail}")
        if item.guide_id:
            console.print(f"   [dim]guide:[/dim] {item.guide_id}")
        console.print()
    return 0


def _cmd_glossary(query: str) -> int:
    from rich.console import Console
    from rich.panel import Panel

    from ludo.content.glossary import search_glossary

    console = Console()
    hits = search_glossary(query)
    if not hits:
        console.print(f"No glossary entries matched [bold]{query}[/bold].")
        return 1
    for entry in hits:
        body = f"[bold #e6c36a]Linux:[/] {entry.linux}\n\n{entry.why}"
        console.print(Panel(body, title=entry.windows, border_style="#3a3226"))
    return 0


def _cmd_translate(query: str) -> int:
    from rich.console import Console
    from rich.panel import Panel

    from ludo.content.commands import translate_command

    console = Console()
    hits = translate_command(query)
    if not hits:
        console.print(f"No translation for [bold]{query}[/bold]. Try [italic]dir[/], [italic]ipconfig[/], or [italic]taskkill[/].")
        return 1
    for entry in hits:
        body = f"[bold #e6c36a]{entry.linux}[/]\n\n{entry.note}"
        console.print(Panel(body, title=f"Windows: {entry.windows}", border_style="#c9a227"))
    return 0


def _cmd_ask(question: str, llm: str | None = None) -> int:
    from rich.console import Console
    from rich.panel import Panel

    from ludo.ask import answer_question
    from ludo.llm import describe_backend, detect_backend
    from ludo.probe import probe

    console = Console()
    try:
        brain = detect_backend(llm)
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        return 1
    answer = answer_question(question, probe(), llm_choice=llm, backend=brain)
    console = Console()
    subtitle = f"{answer.title or answer.source} · {describe_backend(brain)}"
    console.print(Panel(answer.text, title="Ludo", subtitle=subtitle, border_style="#c9a227"))
    return 0


def _cmd_llm() -> int:
    from rich.console import Console

    from ludo.llm import DEFAULT_QWEN, describe_backend, detect_backend

    console = Console()
    try:
        brain = detect_backend()
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        return 1
    console.print(f"[bold #e6c36a]Brain:[/] {describe_backend(brain)}")
    if brain is None:
        console.print(f"Local Qwen: install Ollama, then [bold]ollama pull {DEFAULT_QWEN}[/bold]")
        console.print("Gemini: export [bold]GEMINI_API_KEY[/bold] and run [bold]ludo ask --llm gemini …[/bold]")
    return 0


def _cmd_guides() -> int:
    from rich.console import Console
    from rich.table import Table

    from ludo.content.catalog import GUIDES, SECTIONS

    console = Console()
    table = Table(title="Ludo guides")
    table.add_column("ID", style="bold #e6c36a")
    table.add_column("Title")
    table.add_column("Section")
    table.add_column("Min", justify="right")
    for guide in GUIDES:
        table.add_row(guide.id, guide.title, SECTIONS.get(guide.section, guide.section), str(guide.minutes))
    console.print(table)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
