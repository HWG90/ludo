from ludo.content.glossary import search_glossary


def test_empty_query_lists_all() -> None:
    assert len(search_glossary("")) > 20


def test_task_manager() -> None:
    hits = search_glossary("task manager")
    assert hits
    assert "btop" in hits[0].linux or "System Monitor" in hits[0].linux


def test_ctrl_c() -> None:
    hits = search_glossary("Ctrl+C")
    assert any("Shift" in entry.linux or "cancel" in entry.why.lower() for entry in hits)


def test_no_match() -> None:
    assert search_glossary("definitely-not-a-real-windows-thing-xyz") == []
