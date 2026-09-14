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
            placeholder="Ask about Steam, copy-paste, ipconfig, this GPU…  Enter to send",
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
                "Answering from Ludo’s built-in notes. For a local Qwen model: ollama pull qwen2.5:7b. "
                "For Gemini, set GEMINI_API_KEY."
            )
        if getattr(brain, "name", "") == "gemini":
            return f"Using {label}. Replies are grounded in Ludo’s notes, then sent to Google."
        if uses_notes_only(brain):
            return (
                f"{label}. {getattr(brain, 'model', 'This model')} invents too much for chat, "
                "so Ask uses Ludo’s notes. For live answers: LUDO_OLLAMA_MODEL=qwen2.5:7b."
            )
        return f"Using {label} on this machine. Nothing is sent to the cloud."

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
                    "Try “what is Proton”, “Task Manager”, “ipconfig”, or “is Steam installed”.",
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
