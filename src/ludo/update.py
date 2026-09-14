from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ludo import __version__
from ludo.paths import package_root, xdg_data_home
from ludo.settings import Settings

DEFAULT_GITHUB_REPO = "HWG90/ludo"
FETCH_TIMEOUT = 4.0


@dataclass(frozen=True)
class UpdateInfo:
    local: str
    remote: str
    repo: str

    @property
    def url(self) -> str:
        return f"https://github.com/{self.repo}"


def github_repo() -> str:
    raw = (os.environ.get("LUDO_GITHUB") or DEFAULT_GITHUB_REPO).strip()
    return raw or DEFAULT_GITHUB_REPO


def git_url() -> str:
    override = (os.environ.get("LUDO_REPO") or "").strip()
    if override:
        return override
    return f"https://github.com/{github_repo()}.git"


def updates_disabled() -> bool:
    choice = (os.environ.get("LUDO_UPDATE") or "auto").strip().lower()
    return choice in {"off", "none", "false", "0", "no"}


def version_parts(value: str) -> tuple[int, int, int]:
    cleaned = value.strip().lstrip("vV")
    numbers: list[int] = []
    for chunk in cleaned.replace("-", ".").split("."):
        digits = "".join(char for char in chunk if char.isdigit())
        if not digits:
            if numbers:
                break
            continue
        numbers.append(int(digits))
        if len(numbers) == 3:
            break
    while len(numbers) < 3:
        numbers.append(0)
    return (numbers[0], numbers[1], numbers[2])


def is_newer(remote: str, local: str) -> bool:
    return version_parts(remote) > version_parts(local)


def parse_pyproject_version(text: str) -> str:
    in_project = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "[project]":
            in_project = True
            continue
        if in_project and stripped.startswith("["):
            break
        if in_project and stripped.startswith("version"):
            _, _, rest = stripped.partition("=")
            value = rest.strip().strip("\"'")
            if value:
                return value
    raise ValueError("Could not read version from pyproject.toml")


def should_offer(settings: Settings, local: str, remote: str) -> bool:
    if not is_newer(remote, local):
        return False
    skipped = (settings.skip_update or "").strip()
    if skipped and not is_newer(remote, skipped):
        return False
    return True


def fetch_remote_version(*, timeout: float = FETCH_TIMEOUT) -> str:
    repo = github_repo()
    try:
        payload = _get_json(
            f"https://api.github.com/repos/{repo}/releases/latest",
            timeout=timeout,
        )
        tag = str(payload.get("tag_name") or "").strip()
        if tag:
            return tag.lstrip("vV")
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError, ValueError):
        pass
    text = _get_text(
        f"https://raw.githubusercontent.com/{repo}/master/pyproject.toml",
        timeout=timeout,
    )
    return parse_pyproject_version(text)


def check_for_update(settings: Settings, *, local: str | None = None) -> UpdateInfo | None:
    if updates_disabled():
        return None
    current = local if local is not None else __version__
    try:
        remote = fetch_remote_version()
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError, ValueError):
        return None
    if not should_offer(settings, current, remote):
        return None
    return UpdateInfo(local=current, remote=remote, repo=github_repo())


def install_kind() -> str:
    for hint in _install_path_hints():
        normalized = hint.replace("\\", "/")
        parts = Path(hint).parts
        if "pipx" in parts:
            return "pipx"
        if "/uv/tools/" in normalized:
            return "uv"
        if "/ludo/venv/" in normalized:
            return "venv"
    if source_repo() is not None:
        return "git"
    return "unknown"


def _install_path_hints() -> list[str]:
    hints: list[str] = []
    seen: set[str] = set()

    def add(raw: str | None) -> None:
        if not raw:
            return
        path = Path(raw)
        candidates = [path]
        try:
            if path.is_symlink():
                target = path.readlink()
                if not target.is_absolute():
                    target = path.parent / target
                candidates.append(target)
        except OSError:
            pass
        for candidate in candidates:
            text = str(candidate)
            if text in seen:
                continue
            seen.add(text)
            hints.append(text)

    add(sys.executable)
    if sys.argv:
        add(sys.argv[0])
    add(shutil.which("ludo"))
    return hints


def source_repo() -> Path | None:
    root = package_root().parents[1]
    if (root / ".git").is_dir() and (root / "pyproject.toml").is_file():
        return root
    return None


def apply_update(on_progress: Callable[[str], None] | None = None) -> None:
    report = on_progress or (lambda _msg: None)
    kind = install_kind()
    url = git_url()
    if kind == "pipx":
        report("Updating with pipx…")
        _run(["pipx", "install", "--force", f"git+{url}"])
        return
    if kind == "uv":
        report("Updating with uv…")
        _run(["uv", "tool", "install", "--force", f"git+{url}"])
        return
    if kind == "venv":
        pip = xdg_data_home() / "ludo" / "venv" / "bin" / "pip"
        if not pip.is_file():
            raise RuntimeError("The Ludo venv is missing. Re-run the install script.")
        report("Updating the Ludo venv…")
        _run([str(pip), "install", "--upgrade", f"git+{url}"])
        return
    if kind == "git":
        repo = source_repo()
        if repo is None:
            raise RuntimeError("This git checkout of Ludo could not be found.")
        git = shutil.which("git")
        if git is None:
            raise RuntimeError("git is not on PATH")
        report("Pulling the latest git…")
        _run([git, "-C", str(repo), "pull", "--ff-only"])
        return
    raise RuntimeError(
        "Ludo does not know how it was installed. Re-run:\n"
        f"curl -fsSL https://raw.githubusercontent.com/{github_repo()}/master/scripts/install.sh | bash"
    )


def prompt_copy(info: UpdateInfo) -> str:
    return "\n".join(
        [
            f"GitHub has Ludo {info.remote}. This copy is {info.local}.",
            "",
            f"Source: {info.url}",
            "",
            "Y  Yes, update now",
            "N  Not now",
            "D  Don’t ask about this version",
        ]
    )


def _get_text(url: str, *, timeout: float) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"ludo/{__version__}",
            "Accept": "application/vnd.github+json, text/plain",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _get_json(url: str, *, timeout: float) -> dict:
    payload = json.loads(_get_text(url, timeout=timeout))
    if not isinstance(payload, dict):
        raise ValueError("GitHub did not return a JSON object")
    return payload


def _run(command: list[str]) -> None:
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode == 0:
        return
    detail = (result.stderr or result.stdout or f"exit {result.returncode}").strip()
    raise RuntimeError(detail or f"{command[0]} failed")
