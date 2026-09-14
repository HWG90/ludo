from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static
from textual.worker import Worker, WorkerState

from ludo.settings import save_settings
from ludo.update import UpdateInfo, apply_update, prompt_copy


class UpdateScreen(ModalScreen[str]):
    BINDINGS = [
        Binding("y", "yes", "Yes", show=False),
        Binding("n", "skip", "Not now", show=False),
        Binding("d", "never", "Don't ask", show=False),
        Binding("escape", "skip", "Not now", show=False),
    ]

    def __init__(self, info: UpdateInfo) -> None:
        super().__init__()
        self.info = info
        self._busy = False

    def compose(self) -> ComposeResult:
        with Vertical(id="setup-card"):
            yield Label("Update Ludo?", classes="gold")
            yield Static(prompt_copy(self.info), id="setup-copy")
            with Horizontal(id="setup-actions"):
                yield Button("Yes, update", id="update-yes", classes="primary")
                yield Button("Not now", id="update-skip", classes="ghost")
                yield Button("Skip this version", id="update-never", classes="ghost")
            yield Static("", id="setup-status", classes="muted")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "update-yes":
            self.action_yes()
        elif event.button.id == "update-skip":
            self.action_skip()
        elif event.button.id == "update-never":
            self.action_never()

    def action_yes(self) -> None:
        if self._busy:
            return
        self._busy = True
        self.query_one("#setup-actions").display = False
        self._set_status("Updating…")
        self.run_worker(self._run_update, thread=True, exclusive=True, name="ludo-update")

    def action_skip(self) -> None:
        if self._busy:
            return
        self.dismiss("skipped")

    def action_never(self) -> None:
        if self._busy:
            return
        settings = self.app.settings
        settings.skip_update = self.info.remote
        save_settings(settings)
        self.dismiss("declined")

    def _run_update(self) -> None:
        apply_update(on_progress=lambda msg: self.app.call_from_thread(self._set_status, msg))

    def _set_status(self, message: str) -> None:
        self.query_one("#setup-status", Static).update(message)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.name != "ludo-update":
            return
        if event.state is WorkerState.SUCCESS:
            self.dismiss("updated")
            return
        if event.state is WorkerState.ERROR:
            self._busy = False
            self.query_one("#setup-actions").display = True
            error = event.worker.error
            detail = str(error) if error else "Update failed"
            self._set_status(f"Could not finish: {detail}")
