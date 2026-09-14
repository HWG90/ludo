from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.theme import Theme
from textual.widgets import Button, Footer, Header, Input, Static
from textual.worker import Worker, WorkerState

from ludo.ask import Answer, answer_question
from ludo.content.catalog import next_incomplete
from ludo.llm import Brain, detect_backend
from ludo.ollama_setup import inspect_ollama, should_autostart, should_prompt, stop_ludo_ollama
from ludo.probe import SystemProfile, probe
from ludo.progress import Progress, load_progress, save_progress
from ludo.settings import DEFAULT_THEME, Settings, load_settings, save_settings
from ludo.ui.chat import AskBar, ChatTurn, ChatView
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
    ("ask", "Ask"),
)

VIEWS = {
    "home": HomeView,
    "week": WeekView,
    "glossary": GlossaryView,
    "gaming": GamingView,
    "checkup": CheckupView,
    "commands": CommandsView,
    "ask": ChatView,
}

LUDO_THEME = Theme(
    name="ludo",
    primary="#c9a227",
    secondary="#e6c36a",
    accent="#c9a227",
    foreground="#f0e6d8",
    background="#12110e",
    surface="#1c1916",
    panel="#191613",
    success="#8fbf88",
    warning="#e6c36a",
    error="#e09080",
    dark=True,
)


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
        Binding("slash", "focus_ask", "Ask"),
        Binding("question_mark", "keys", "Keys"),
        Binding("n", "continue_path", "Continue", show=False),
    ]

    def __init__(
        self,
        profile: SystemProfile | None = None,
        progress: Progress | None = None,
        settings: Settings | None = None,
    ) -> None:
        super().__init__()
        self.register_theme(LUDO_THEME)
        self.profile = profile if profile is not None else probe()
        self.progress = progress if progress is not None else load_progress()
        self.settings = settings if settings is not None else load_settings()
        self._persist_theme = True
        self.current_view = "home"
        self.chat: list[ChatTurn] = []
        self.brain: Brain | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            with Vertical(id="sidebar"):
                yield Static("LUDO", id="brand")
                yield Static("find your way", id="brand-sub")
                for name, label in NAV:
                    yield Button(label, id=f"nav-{name}", classes="nav")
            yield Vertical(id="body")
        yield AskBar()
        yield Footer()

    def on_mount(self) -> None:
        self._apply_saved_theme()
        try:
            self.brain = detect_backend()
        except RuntimeError as exc:
            self.brain = None
            self.notify(str(exc), severity="warning", timeout=8)
        self.switch_view("home")
        self._boot_ollama()

    def on_unmount(self) -> None:
        stop_ludo_ollama()

    def _apply_saved_theme(self) -> None:
        wanted = self.settings.theme or DEFAULT_THEME
        if wanted not in self.available_themes:
            wanted = DEFAULT_THEME
        self.theme = wanted

    def watch_theme(self, theme_name: str) -> None:
        if not getattr(self, "_persist_theme", False):
            return
        if self.settings.theme == theme_name:
            return
        self.settings.theme = theme_name
        save_settings(self.settings)

    def _boot_ollama(self) -> None:
        status = inspect_ollama()
        if should_prompt(self.progress, status):
            from ludo.ui.setup import OllamaSetupScreen

            self.push_screen(OllamaSetupScreen(status), self._after_ollama_setup)
            return
        if should_autostart(self.progress, status):
            self.run_worker(self._autostart_ollama, thread=True, exclusive=True, name="ollama-boot")

    def _autostart_ollama(self) -> None:
        from ludo.ollama_setup import ensure_ready

        ensure_ready()

    def _after_ollama_setup(self, result: str | None) -> None:
        if result == "declined":
            self.progress.ollama_choice = "declined"
            save_progress(self.progress)
            self.notify("Ask will use built-in notes. You can still set GEMINI_API_KEY later.")
            return
        if result == "accepted":
            try:
                self.brain = detect_backend()
            except RuntimeError:
                self.brain = None
            self.notify("Qwen is ready. Press / and ask something.", timeout=6)
            return

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("nav-"):
            self.switch_view(event.button.id.removeprefix("nav-"))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "ask-input":
            return
        query = event.value.strip()
        if not query:
            return
        event.input.value = ""
        self.ask(query)

    def ask(self, query: str) -> None:
        if len(self.screen_stack) > 1:
            return
        self.chat.append(ChatTurn("you", query))
        if self.brain is None:
            answer = answer_question(query, self.profile, use_llm=False)
            self.chat.append(ChatTurn("ludo", answer.text, answer.guide_id))
            self.switch_view("ask")
            self.call_after_refresh(self._focus_ask)
            return
        self.chat.append(ChatTurn("ludo", "Thinking…"))
        self.switch_view("ask")
        self.call_after_refresh(self._focus_ask)
        history = [(turn.role, turn.text) for turn in self.chat[:-2]]
        self.run_worker(
            lambda: answer_question(query, self.profile, backend=self.brain, history=history),
            name="ask",
            group="ask",
            thread=True,
            exclusive=True,
        )

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.name == "ollama-boot":
            if event.state is WorkerState.SUCCESS:
                try:
                    self.brain = detect_backend()
                except RuntimeError:
                    self.brain = None
                self.notify("Qwen is loaded. Press / to ask.", timeout=5)
            elif event.state is WorkerState.ERROR:
                detail = str(event.worker.error) if event.worker.error else "Ollama did not start"
                self.notify(detail, severity="warning", timeout=8)
            return
        if event.worker.name != "ask":
            return
        if event.state is WorkerState.SUCCESS:
            answer = event.worker.result
            if isinstance(answer, Answer):
                self._finish_ask(answer)
            return
        if event.state is WorkerState.ERROR:
            self._finish_ask(
                Answer(
                    "The model did not answer. Ludo notes are still in the guides if you want the offline version.",
                    source="error",
                )
            )

    def _finish_ask(self, answer: Answer) -> None:
        if self.chat and self.chat[-1].role == "ludo":
            self.chat[-1] = ChatTurn("ludo", answer.text, answer.guide_id)
        else:
            self.chat.append(ChatTurn("ludo", answer.text, answer.guide_id))
        if self.current_view == "ask":
            try:
                self.query_one(ChatView).refresh_log()
            except Exception:
                self.switch_view("ask")
        self.call_after_refresh(self._focus_ask)

    def _focus_ask(self) -> None:
        self.query_one("#ask-input", Input).focus()

    def action_focus_ask(self) -> None:
        if len(self.screen_stack) > 1:
            return
        self._focus_ask()

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
            "1 home · 2 week · 3 glossary · 4 gaming · 5 checkup · 6 commands · / ask · n continue · q quit",
            timeout=6,
        )


def run() -> None:
    try:
        LudoApp().run()
    finally:
        stop_ludo_ollama()
