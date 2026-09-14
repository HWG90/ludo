from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static
from textual.worker import Worker, WorkerState

from ludo.ollama_setup import OllamaStatus, ensure_ready, prompt_copy
from ludo.progress import save_progress


class OllamaSetupScreen(ModalScreen[str]):
    BINDINGS = [
        Binding("y", "yes", "Yes", show=False),
        Binding("n", "skip", "Not now", show=False),
        Binding("d", "never", "Don't ask", show=False),
        Binding("escape", "skip", "Not now", show=False),
    ]

    def __init__(self, status: OllamaStatus) -> None:
        super().__init__()
        self.status = status
        self._busy = False

    def compose(self) -> ComposeResult:
        with Vertical(id="setup-card"):
            yield Label("Set up a local model?", classes="gold")
            yield Static(prompt_copy(self.status), id="setup-copy")
            with Horizontal(id="setup-actions"):
                yield Button("Yes, set it up", id="setup-yes", classes="primary")
                yield Button("Not now", id="setup-skip", classes="ghost")
                yield Button("Don’t ask again", id="setup-never", classes="ghost")
            yield Static("", id="setup-status", classes="muted")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "setup-yes":
            self.action_yes()
        elif event.button.id == "setup-skip":
            self.action_skip()
        elif event.button.id == "setup-never":
            self.action_never()

    def action_yes(self) -> None:
        if self._busy:
            return
        self._busy = True
        actions = self.query_one("#setup-actions")
        actions.display = False
        self._set_status("Working… you can leave this up.")
        self.run_worker(self._run_setup, thread=True, exclusive=True, group="ollama", name="ollama-setup")

    def action_skip(self) -> None:
        if self._busy:
            return
        self.dismiss("skipped")

    def action_never(self) -> None:
        if self._busy:
            return
        self.dismiss("declined")

    def _run_setup(self) -> None:
        ensure_ready(self.status, on_progress=lambda msg: self.app.call_from_thread(self._set_status, msg))

    def _set_status(self, message: str) -> None:
        self.query_one("#setup-status", Static).update(message)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.name != "ollama-setup":
            return
        if event.state is WorkerState.SUCCESS:
            progress = self.app.progress
            progress.ollama_choice = "accepted"
            save_progress(progress)
            self.dismiss("accepted")
            return
        if event.state is WorkerState.ERROR:
            self._busy = False
            self.query_one("#setup-actions").display = True
            error = event.worker.error
            detail = str(error) if error else "Setup failed"
            self._set_status(f"Could not finish: {detail}")
