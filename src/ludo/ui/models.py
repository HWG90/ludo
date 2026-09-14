from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, OptionList, Static
from textual.widgets.option_list import Option

from ludo.llm import list_local_model_info, model_is_tiny, ollama_model


class ModelScreen(ModalScreen[str | None]):
    BINDINGS = [
        Binding("escape", "cancel", "Close", show=False),
    ]

    def __init__(self, models: list[tuple[str, int]] | None = None) -> None:
        super().__init__()
        self.models = models if models is not None else list_local_model_info()
        self.current = ollama_model()

    def compose(self) -> ComposeResult:
        with Vertical(id="setup-card"):
            yield Label("Ollama models", classes="gold")
            yield Static(
                "Installed on this PC. Enter to switch. Esc to close. Tiny models stay on Ludo’s notes.",
                classes="muted",
            )
            yield OptionList(*self._options(), id="model-list")

    def on_mount(self) -> None:
        listing = self.query_one("#model-list", OptionList)
        listing.focus()
        current = self.current.lower()
        for index, (name, _size) in enumerate(self.models):
            if name.lower() == current:
                listing.highlighted = index
                break

    def _options(self) -> list[Option]:
        options: list[Option] = []
        for index, (name, size) in enumerate(self.models):
            mark = "●" if name.lower() == self.current.lower() else " "
            extra = _size_label(size)
            note = "  — notes only" if model_is_tiny(name) else ""
            prompt = f"{mark} {name}{extra}{note}"
            options.append(Option(prompt, id=f"m{index}"))
        return options

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        index = event.option_index
        if 0 <= index < len(self.models):
            self.dismiss(self.models[index][0])

    def action_cancel(self) -> None:
        self.dismiss(None)


def _size_label(size: int) -> str:
    if size <= 0:
        return ""
    if size >= 1_000_000_000:
        return f"  ·  {size / 1_000_000_000:.1f} GB"
    return f"  ·  {size / 1_000_000:.0f} MB"
