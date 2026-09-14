from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Input, Label, Static

from ludo.content.glossary import GLOSSARY, GlossaryEntry, search_glossary


class GlossaryView(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("Windows → Linux", classes="gold")
        yield Static("Type a Windows habit. Ludo will name the Linux equivalent and why it exists.", classes="muted")
        yield Input(placeholder="Task Manager, Explorer, Ctrl+C, AppData, DirectX…", id="glossary-search")
        yield VerticalScroll(id="glossary-results")

    def on_mount(self) -> None:
        self._fill(GLOSSARY)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "glossary-search":
            self._fill(search_glossary(event.value))

    def _fill(self, entries: list[GlossaryEntry] | tuple[GlossaryEntry, ...]) -> None:
        results = self.query_one("#glossary-results", VerticalScroll)
        results.remove_children()
        if not entries:
            results.mount(Static("Nothing matched. Try 'steam', 'copy', or 'task manager'."))
            return
        for entry in entries:
            results.mount(Static(entry.windows, classes="gold"))
            results.mount(Static(entry.linux))
            results.mount(Static(entry.why, classes="muted"))
            results.mount(Static(" "))
