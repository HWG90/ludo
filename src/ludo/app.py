from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Static

from ludo.content.catalog import next_incomplete
from ludo.probe import SystemProfile, probe
from ludo.progress import Progress, load_progress
from ludo.ui.checkup import CheckupView
from ludo.ui.commands import CommandsView
from ludo.ui.gaming import GamingView
from ludo.ui.glossary import GlossaryView
from ludo.ui.guide import GuideScreen
from ludo.ui.home import HomeView
from ludo.ui.week import WeekView

NAV = (
    ("home", "Home"),
    ("week", "First week"),
    ("glossary", "Windows → Linux"),
    ("gaming", "Gaming"),
    ("checkup", "Checkup"),
    ("commands", "Commands"),
)

VIEWS = {
    "home": HomeView,
    "week": WeekView,
    "glossary": GlossaryView,
    "gaming": GamingView,
    "checkup": CheckupView,
    "commands": CommandsView,
}


class LudoApp(App):
    CSS_PATH = "app.tcss"
    TITLE = "Ludo"
    SUB_TITLE = "Linux, from the Windows you already know"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("1", "goto('home')", "Home", show=False),
        Binding("2", "goto('week')", "Week", show=False),
        Binding("3", "goto('glossary')", "Glossary", show=False),
        Binding("4", "goto('gaming')", "Gaming", show=False),
        Binding("5", "goto('checkup')", "Checkup", show=False),
        Binding("6", "goto('commands')", "Translate", show=False),
        Binding("h", "goto('home')", "Home", show=False),
        Binding("w", "goto('week')", "Week", show=False),
        Binding("g", "goto('glossary')", "Glossary", show=False),
        Binding("p", "goto('gaming')", "Gaming", show=False),
        Binding("c", "goto('checkup')", "Checkup", show=False),
        Binding("t", "goto('commands')", "Translate", show=False),
        Binding("question_mark", "keys", "Keys"),
        Binding("n", "continue_path", "Continue", show=False),
    ]

    def __init__(self, profile: SystemProfile | None = None, progress: Progress | None = None) -> None:
        super().__init__()
        self.profile = profile if profile is not None else probe()
        self.progress = progress if progress is not None else load_progress()
        self.current_view = "home"

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static("LUDO", id="brand")
                yield Static("find your way", id="brand-sub")
                for name, label in NAV:
                    yield Button(label, id=f"nav-{name}", classes="nav")
            yield Vertical(id="body")
        yield Footer()

    def on_mount(self) -> None:
        self.switch_view("home")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("nav-"):
            self.switch_view(event.button.id.removeprefix("nav-"))

    def switch_view(self, name: str) -> None:
        if name not in VIEWS:
            return
        self.current_view = name
        for nav_name, _label in NAV:
            button = self.query_one(f"#nav-{nav_name}", Button)
            button.set_class(nav_name == name, "-active")
        body = self.query_one("#body", Vertical)
        body.remove_children()
        body.mount(VIEWS[name]())

    def open_guide(self, guide_id: str) -> None:
        self.push_screen(GuideScreen(guide_id), self._after_guide)

    def _after_guide(self, _result: bool | None) -> None:
        self.switch_view(self.current_view)

    def action_goto(self, name: str) -> None:
        if len(self.screen_stack) > 1:
            return
        self.switch_view(name)

    def action_continue_path(self) -> None:
        if len(self.screen_stack) > 1:
            return
        nxt = next_incomplete(self.progress.completed)
        if nxt is None:
            self.notify("First week is complete. Browse Gaming or the glossary.")
            return
        self.open_guide(nxt.id)

    def action_keys(self) -> None:
        self.notify(
            "1 home · 2 first week · 3 glossary · 4 gaming · 5 checkup · 6 commands · n continue · q quit",
            timeout=6,
        )


def run() -> None:
    LudoApp().run()
