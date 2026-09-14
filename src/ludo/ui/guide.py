from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Label, Markdown, RadioButton, RadioSet, Static
from textual.binding import Binding
from textual.screen import Screen

from ludo.content.catalog import Guide, get_guide, load_guide_text
from ludo.progress import save_progress


class GuideScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("c", "complete", "Complete"),
    ]

    def __init__(self, guide_id: str) -> None:
        super().__init__()
        self.guide: Guide = get_guide(guide_id)

    def compose(self) -> ComposeResult:
        from textual.widgets import Footer, Header

        yield Header()
        with Vertical(id="body"):
            yield Label(self.guide.title, classes="gold")
            yield Static(self.guide.windows_hook, classes="muted")
            with VerticalScroll(classes="md-wrap"):
                yield Markdown(load_guide_text(self.guide))
            if self.guide.quiz:
                question = self.guide.quiz[0]
                with Vertical(id="quiz-box"):
                    yield Label("Quick check", classes="gold")
                    yield Static(question.prompt)
                    with RadioSet(id="quiz-choices"):
                        for choice in question.choices:
                            yield RadioButton(choice)
                    yield Button("Check answer", id="check-quiz", classes="ghost")
                    yield Label("", id="quiz-result")
            with Horizontal():
                yield Button("Mark complete", id="complete", classes="primary")
                yield Button("Back", id="back", classes="ghost")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.action_back()
        elif event.button.id == "complete":
            self.action_complete()
        elif event.button.id == "check-quiz":
            self._check_quiz()

    def action_back(self) -> None:
        self.dismiss(False)

    def action_complete(self) -> None:
        self.app.progress.mark_complete(self.guide.id)
        save_progress(self.app.progress)
        self.app.notify(f"Marked complete: {self.guide.title}")
        self.dismiss(True)

    def _check_quiz(self) -> None:
        if not self.guide.quiz:
            return
        question = self.guide.quiz[0]
        radios = self.query_one("#quiz-choices", RadioSet)
        index = radios.pressed_index
        result = self.query_one("#quiz-result", Label)
        if index is None:
            result.update("Pick an answer first.")
            result.set_classes("next")
            return
        if index == question.answer:
            result.update(f"Correct. {question.explain}")
            result.set_classes("good")
            self.app.progress.record_quiz(self.guide.id, 1)
            save_progress(self.app.progress)
        else:
            result.update(f"Not quite. {question.explain}")
            result.set_classes("warn")
