from pathlib import Path

from ludo.progress import Progress, load_progress, save_progress


def test_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "progress.json"
    progress = Progress()
    progress.mark_complete("welcome")
    progress.record_quiz("terminal", 1)
    save_progress(progress, path)
    loaded = load_progress(path)
    assert loaded.is_complete("welcome")
    assert loaded.is_complete("terminal")
    assert loaded.quiz["terminal"] == 1


def test_missing_file(tmp_path: Path) -> None:
    loaded = load_progress(tmp_path / "nope.json")
    assert loaded.completed == set()
