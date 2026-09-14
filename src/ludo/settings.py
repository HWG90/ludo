from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ludo.paths import settings_path

DEFAULT_THEME = "ludo"


@dataclass
class Settings:
    theme: str = DEFAULT_THEME
    skip_update: str = ""
    ollama_model: str = ""

    def dump(self) -> dict:
        return {
            "theme": self.theme,
            "skip_update": self.skip_update,
            "ollama_model": self.ollama_model,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Settings:
        theme = str(data.get("theme") or DEFAULT_THEME).strip() or DEFAULT_THEME
        skip_update = str(data.get("skip_update") or "").strip()
        ollama_model = str(data.get("ollama_model") or "").strip()
        return cls(theme=theme, skip_update=skip_update, ollama_model=ollama_model)


def load_settings(path: Path | None = None) -> Settings:
    target = path or settings_path()
    if not target.is_file():
        return Settings()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return Settings()
    if not isinstance(data, dict):
        return Settings()
    return Settings.from_dict(data)


def save_settings(settings: Settings, path: Path | None = None) -> Path:
    target = path or settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(settings.dump(), indent=2) + "\n", encoding="utf-8")
    return target
