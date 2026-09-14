from __future__ import annotations

from textual.widgets import Button


class GuideButton(Button):
    def __init__(self, label: str, guide_id: str, classes: str = "ghost") -> None:
        super().__init__(label, classes=classes)
        self.guide_id = guide_id
