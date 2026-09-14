from __future__ import annotations

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Input, Label, Static

from ludo.ui.widgets import GuideButton


@dataclass
class ChatTurn:
    role: str
    text: str
    guide_id: str | None = None


class AskBar(Horizontal):
    def __init__(self) -> None:
        super().__init__(id="ask-bar")

    def compose(self) -> ComposeResult:
        yield Label("Ask", id="ask-label")
        yield Input(
            placeholder="Ask about Linux, this PC, or a Windows habit…  Enter to send",
            id="ask-input",
        )


class ChatView(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("Ask Ludo", classes="gold")
        yield Static(self._blurb(), classes="muted", id="ask-blurb")
        yield VerticalScroll(id="chat-log")

    def _blurb(self) -> str:
        from ludo.llm import describe_backend, uses_notes_only

        brain = getattr(self.app, "brain", None)
        label = describe_backend(brain)
        if brain is None:
            return (
                "Answering from Ludo’s built-in notes. For live chat, install Ollama and pick a model with Ctrl+O. "
                "Or set GEMINI_API_KEY."
            )
        if getattr(brain, "name", "") == "gemini":
            return f"Using {label}. Live chat via Google. Ctrl+O is only for local Ollama models."
        if uses_notes_only(brain):
            return (
                f"{label}. This size of model is too small for chat, so Ask uses Ludo’s notes. "
                "Pick a larger installed model with Ctrl+O."
            )
        return f"Using {label} on this machine. Live chat — nothing is sent to the cloud. Ctrl+O to switch."

    def on_mount(self) -> None:
        log = self.query_one("#chat-log", VerticalScroll)
        log.anchor()
        self.refresh_log()

    def refresh_log(self) -> None:
        log = self.query_one("#chat-log", VerticalScroll)
        log.remove_children()
        history: list[ChatTurn] = self.app.chat
        if not history:
            log.mount(
                Static(
                    "Try “how do I update”, “Task Manager”, “ipconfig”, or “what is my hostname”.",
                    classes="muted",
                )
            )
            return
        for turn in history:
            who = "You" if turn.role == "you" else "Ludo"
            log.mount(Static(who, classes="gold" if turn.role == "ludo" else "muted"))
            log.mount(Static(turn.text))
            if turn.role == "ludo" and turn.guide_id:
                log.mount(GuideButton(f"Open guide: {turn.guide_id}", turn.guide_id))
            log.mount(Static(" "))
        log.scroll_end(animate=False)

    def refresh_blurb(self) -> None:
        self.query_one("#ask-blurb", Static).update(self._blurb())

    def on_button_pressed(self, event: GuideButton.Pressed) -> None:
        if isinstance(event.button, GuideButton):
            self.app.open_guide(event.button.guide_id)
