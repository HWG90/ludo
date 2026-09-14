from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Static

from ludo.content.catalog import next_incomplete
from ludo.format import profile_facts
from ludo.recommend import recommend
from ludo.ui.widgets import GuideButton


class HomeView(VerticalScroll):
    def compose(self) -> ComposeResult:
        profile = self.app.profile
        progress = self.app.progress
        nxt = next_incomplete(progress.completed)
        done = len(progress.completed)
        yield Label("Ludo", classes="gold hero")
        yield Static(
            "A quiet guide for Windows users who want Linux as a daily driver — "
            "same machine, different layout.",
            classes="muted",
        )
        with Vertical(classes="card"):
            yield Label("This machine", classes="card-title")
            for key, value in profile_facts(profile)[:8]:
                with Horizontal():
                    yield Label(key, classes="fact-key")
                    yield Static(value)
        with Vertical(classes="card"):
            yield Label("First week", classes="card-title")
            if nxt is None:
                yield Static("You have walked the first-week path. Open Gaming or the glossary and keep going.")
            else:
                yield Static(f"{done} guides marked complete. Next up: {nxt.title} ({nxt.minutes} min).")
                yield Static(nxt.windows_hook, classes="muted")
                yield GuideButton(f"Continue — {nxt.title}", nxt.id, classes="primary")
        with Vertical(classes="card"):
            yield Label("Suggestions for this PC", classes="card-title")
            for item in recommend(profile):
                yield Static(f"{item.title}", classes=item.level)
                yield Static(item.detail, classes="muted")
                if item.guide_id:
                    yield GuideButton(f"Read: {item.guide_id}", item.guide_id)

    def on_button_pressed(self, event: GuideButton.Pressed) -> None:
        if isinstance(event.button, GuideButton):
            self.app.open_guide(event.button.guide_id)
