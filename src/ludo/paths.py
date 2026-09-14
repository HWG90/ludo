from __future__ import annotations

from pathlib import Path


def xdg_data_home() -> Path:
    import os

    raw = os.environ.get("XDG_DATA_HOME")
    if raw:
        return Path(raw)
    return Path.home() / ".local" / "share"


def progress_path() -> Path:
    return xdg_data_home() / "ludo" / "progress.json"


def package_root() -> Path:
    return Path(__file__).resolve().parent


def guides_dir() -> Path:
    return package_root() / "content" / "guides"
