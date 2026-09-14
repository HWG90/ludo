from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Static

from ludo.format import profile_facts
from ludo.recommend import recommend
from ludo.ui.widgets import GuideButton


class CheckupView(VerticalScroll):
    def compose(self) -> ComposeResult:
        profile = self.app.profile
        yield Label("System checkup", classes="gold")
        yield Static(
            "A friendly dxdiag. Nothing here is sent anywhere — Ludo only looks at this machine.",
            classes="muted",
        )
        with Vertical(classes="card"):
            yield Label(profile.distro_name, classes="card-title")
            for key, value in profile_facts(profile):
                with Horizontal():
                    yield Label(key, classes="fact-key")
                    yield Static(value)
        with Vertical(classes="card"):
            yield Label("What to do next", classes="card-title")
            for item in recommend(profile):
                yield Static(item.title, classes=item.level)
                yield Static(item.detail, classes="muted")
                if item.guide_id:
                    yield GuideButton(f"Open {item.guide_id}", item.guide_id)

    def on_button_pressed(self, event: GuideButton.Pressed) -> None:
        if isinstance(event.button, GuideButton):
            self.app.open_guide(event.button.guide_id)
