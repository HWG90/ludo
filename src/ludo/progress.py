from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ludo.paths import progress_path


@dataclass
class Progress:
    completed: set[str] = field(default_factory=set)
    quiz: dict[str, int] = field(default_factory=dict)

    def mark_complete(self, guide_id: str) -> None:
        self.completed.add(guide_id)

    def record_quiz(self, guide_id: str, correct: int) -> None:
        self.quiz[guide_id] = correct
        self.mark_complete(guide_id)

    def is_complete(self, guide_id: str) -> bool:
        return guide_id in self.completed

    def dump(self) -> dict:
        return {
            "completed": sorted(self.completed),
            "quiz": dict(self.quiz),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Progress:
        completed = set(data.get("completed") or [])
        quiz = {str(k): int(v) for k, v in (data.get("quiz") or {}).items()}
        return cls(completed=completed, quiz=quiz)


def load_progress(path: Path | None = None) -> Progress:
    target = path or progress_path()
    if not target.is_file():
        return Progress()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return Progress()
    if not isinstance(data, dict):
        return Progress()
    return Progress.from_dict(data)


def save_progress(progress: Progress, path: Path | None = None) -> Path:
    target = path or progress_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(progress.dump(), indent=2) + "\n", encoding="utf-8")
    return target
