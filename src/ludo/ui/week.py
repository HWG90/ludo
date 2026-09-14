from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, ListItem, ListView, Static

from ludo.content.catalog import FIRST_WEEK, GUIDES, SECTIONS, get_guide


class WeekView(Vertical):
    def compose(self) -> ComposeResult:
        completed = self.app.progress.completed
        yield Label("First week on Linux", classes="gold")
        yield Static(
            "Eight short stops. Skip around. The order is how most Windows gamers actually get comfortable.",
            classes="muted",
        )
        yield ListView(*self._items(completed), id="week-list")

    def _items(self, completed: set[str]) -> list[ListItem]:
        items: list[ListItem] = []
        for index, guide_id in enumerate(FIRST_WEEK, start=1):
            guide = get_guide(guide_id)
            mark = "✓" if guide.id in completed else f"{index}"
            items.append(
                ListItem(
                    Label(f"{mark}  {guide.title}  ·  {guide.minutes} min"),
                    id=f"guide-{guide.id}",
                )
            )
        extras = [guide for guide in GUIDES if guide.id not in FIRST_WEEK]
        if extras:
            items.append(ListItem(Label("More, when you want it", classes="muted")))
            for guide in extras:
                mark = "✓" if guide.id in completed else "·"
                section = SECTIONS.get(guide.section, guide.section)
                items.append(
                    ListItem(
                        Label(f"{mark}  {guide.title}  ·  {section}"),
                        id=f"guide-{guide.id}",
                    )
                )
        return items

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id.startswith("guide-"):
            self.app.open_guide(item_id.removeprefix("guide-"))
