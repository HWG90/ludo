from ludo.content.catalog import FIRST_WEEK, GUIDES, get_guide, load_guide_text, next_incomplete


def test_all_guide_files_exist() -> None:
    for guide in GUIDES:
        text = load_guide_text(guide)
        assert len(text) > 200
        assert guide.title.split()[0].lower() in text.lower() or text.startswith("#")


def test_first_week_ids_resolve() -> None:
    for guide_id in FIRST_WEEK:
        assert get_guide(guide_id).id == guide_id


def test_next_incomplete() -> None:
    assert next_incomplete(set()) is get_guide("welcome")
    assert next_incomplete(set(FIRST_WEEK)).id not in FIRST_WEEK
    everything = {guide.id for guide in GUIDES}
    assert next_incomplete(everything) is None
