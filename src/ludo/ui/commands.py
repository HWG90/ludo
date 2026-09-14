from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Input, Label, Static

from ludo.content.commands import COMMANDS, CommandMap, translate_command


class CommandsView(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("Command Rosetta stone", classes="gold")
        yield Static("Type a Windows / cmd / PowerShell habit. Ludo answers with the Linux command and a warning if it bites.", classes="muted")
        yield Input(placeholder="dir, ipconfig, taskkill, robocopy, dxdiag…", id="cmd-search")
        yield VerticalScroll(id="cmd-results")

    def on_mount(self) -> None:
        self._fill(COMMANDS)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "cmd-search":
            self._fill(translate_command(event.value))

    def _fill(self, entries: list[CommandMap] | tuple[CommandMap, ...]) -> None:
        results = self.query_one("#cmd-results", VerticalScroll)
        results.remove_children()
        if not entries:
            results.mount(Static("No match. Try dir, cls, ipconfig, or tasklist."))
            return
        for entry in entries:
            results.mount(Static(f"{entry.windows}  →  {entry.linux}", classes="gold"))
            results.mount(Static(entry.note, classes="muted"))
            results.mount(Static(" "))
