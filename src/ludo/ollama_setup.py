from __future__ import annotations

import atexit
import json
import os
import platform
import shutil
import signal
import stat
import subprocess
import tarfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ludo.llm import (
    DEFAULT_QWEN,
    _ollama_host,
    _post_json,
    ollama_is_running,
    ollama_model,
    ollama_model_names,
)
from ludo.paths import xdg_data_home
from ludo.progress import Progress

ProgressFn = Callable[[str], None]

_owned_pid: int | None = None
_atexit_registered = False


@dataclass(frozen=True)
class OllamaStatus:
    binary: Path | None
    running: bool
    model_present: bool
    model: str

    @property
    def ready(self) -> bool:
        return bool(self.binary) and self.running and self.model_present


def inspect_ollama() -> OllamaStatus:
    model = ollama_model()
    running = ollama_is_running()
    if running:
        present = _has_model(model, ollama_model_names())
    else:
        present = model_on_disk(model)
    return OllamaStatus(
        binary=find_ollama(),
        running=running,
        model_present=present,
        model=model,
    )


def find_ollama() -> Path | None:
    which = shutil.which("ollama")
    candidates = []
    if which:
        candidates.append(Path(which))
    candidates.extend(
        [
            Path.home() / ".local" / "bin" / "ollama",
            xdg_data_home() / "ludo" / "ollama" / "ollama",
        ]
    )
    seen: set[Path] = set()
    for path in candidates:
        resolved = path if not path.exists() else path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if path.is_file() and os.access(path, os.X_OK):
            return path
    return None


def llm_setup_disabled() -> bool:
    choice = (os.environ.get("LUDO_LLM") or "auto").strip().lower()
    return choice in {"off", "none", "notes", "false", "0", "gemini", "google"}


def have_install_and_model(status: OllamaStatus) -> bool:
    return bool(status.binary) and status.model_present


def should_prompt(progress: Progress, status: OllamaStatus) -> bool:
    if llm_setup_disabled():
        return False
    if progress.ollama_choice == "declined":
        return False
    if have_install_and_model(status):
        return False
    return not status.ready


def should_autostart(progress: Progress, status: OllamaStatus) -> bool:
    if llm_setup_disabled():
        return False
    if have_install_and_model(status):
        return not status.ready
    if progress.ollama_choice != "accepted":
        return False
    return True


def prompt_copy(status: OllamaStatus) -> str:
    model = status.model or DEFAULT_QWEN
    lines = [
        "Ludo can answer from Qwen 2.5 7B on this PC — no cloud.",
        "",
    ]
    steps: list[str] = []
    if status.binary is None:
        steps.append("1. Install Ollama for your user (no sudo, about 50 MB)")
    if not status.running:
        steps.append(f"{len(steps) + 1}. Start the Ollama service")
    if not status.model_present:
        steps.append(f"{len(steps) + 1}. Download {model} (about 5 GB, one time)")
    steps.append(f"{len(steps) + 1}. Load the model now so Ask works immediately")
    lines.extend(steps)
    lines.extend(
        [
            "",
            "Y  Yes, set it up",
            "N  Not now — keep using built-in notes",
            "D  Don’t ask again",
        ]
    )
    return "\n".join(lines)


def _has_model(wanted: str, names: list[str]) -> bool:
    needle = wanted.lower()
    return any(needle == name.lower() or name.lower().startswith(needle) for name in names)


def ollama_models_dir() -> Path:
    raw = os.environ.get("OLLAMA_MODELS")
    if raw:
        return Path(raw)
    return Path.home() / ".ollama" / "models"


def model_on_disk(model: str) -> bool:
    name, _, tag = model.partition(":")
    tag = tag or "latest"
    manifests = ollama_models_dir() / "manifests"
    if not manifests.is_dir():
        return False
    wanted_name = name.lower()
    wanted_tag = tag.lower()
    for path in manifests.rglob("*"):
        if not path.is_file():
            continue
        if path.name.lower() == wanted_tag and path.parent.name.lower() == wanted_name:
            return True
    return False


def download_url() -> str:
    machine = platform.machine().lower()
    arch = "arm64" if machine in {"aarch64", "arm64"} else "amd64"
    return f"https://github.com/ollama/ollama/releases/latest/download/ollama-linux-{arch}.tgz"


def ensure_ready(status: OllamaStatus | None = None, on_progress: ProgressFn | None = None) -> OllamaStatus:
    report = on_progress or (lambda _msg: None)
    current = status or inspect_ollama()
    binary = current.binary
    if binary is None:
        report("Installing Ollama for your user…")
        binary = install_ollama(on_progress=report)
    if not ollama_is_running():
        report("Starting Ollama…")
        start_daemon(binary)
        _wait_until_running(timeout=20)
    if not _has_model(current.model, ollama_model_names()):
        report(f"Downloading {current.model}… this is the slow one, once.")
        pull_model(current.model, on_progress=report)
    report(f"Loading {current.model}…")
    warmup(current.model)
    report("Qwen is ready.")
    return inspect_ollama()


def install_ollama(on_progress: ProgressFn | None = None) -> Path:
    report = on_progress or (lambda _msg: None)
    dest_dir = Path.home() / ".local" / "bin"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "ollama"
    archive = xdg_data_home() / "ludo" / "cache" / "ollama.tgz"
    archive.parent.mkdir(parents=True, exist_ok=True)
    url = download_url()
    report("Downloading Ollama…")
    urllib.request.urlretrieve(url, archive)
    report("Unpacking Ollama…")
    _extract_binary(archive, dest)
    dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    archive.unlink(missing_ok=True)
    if not dest.is_file():
        raise RuntimeError("Ollama installed but the binary is missing")
    return dest


def _extract_binary(archive: Path, dest: Path) -> None:
    with tarfile.open(archive, "r:*") as tar:
        member = None
        for item in tar.getmembers():
            if Path(item.name).name == "ollama" and item.isfile():
                member = item
                break
        if member is None:
            raise RuntimeError("The Ollama download did not contain an ollama binary")
        extracted = tar.extractfile(member)
        if extracted is None:
            raise RuntimeError("Could not read the Ollama binary from the archive")
        dest.write_bytes(extracted.read())


def pidfile_path() -> Path:
    return xdg_data_home() / "ludo" / "ollama.pid"


def owned_ollama_pid() -> int | None:
    global _owned_pid
    if _owned_pid is not None and _is_ollama_serve(_owned_pid):
        return _owned_pid
    pid = _read_pidfile()
    if pid is not None and _is_ollama_serve(pid):
        _owned_pid = pid
        return pid
    return None


def start_daemon(binary: Path) -> None:
    if ollama_is_running():
        owned_ollama_pid()
        return
    log_path = xdg_data_home() / "ludo" / "ollama.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("ab") as log:
        proc = subprocess.Popen(
            [str(binary), "serve"],
            stdout=log,
            stderr=log,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            env=os.environ.copy(),
        )
    _remember_owned(proc.pid)


def stop_ludo_ollama() -> None:
    """Stop an Ollama daemon that Ludo started. Leave someone else's serve alone."""
    global _owned_pid
    pid = owned_ollama_pid()
    if pid is None:
        return
    _stop_model_quietly()
    _terminate_pid(pid)
    _owned_pid = None
    _clear_pidfile()


def _remember_owned(pid: int) -> None:
    global _owned_pid
    _owned_pid = pid
    path = pidfile_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(pid), encoding="utf-8")
    _ensure_atexit()


def _ensure_atexit() -> None:
    global _atexit_registered
    if _atexit_registered:
        return
    atexit.register(stop_ludo_ollama)
    _atexit_registered = True


def _read_pidfile() -> int | None:
    try:
        raw = pidfile_path().read_text(encoding="utf-8").strip()
        pid = int(raw)
    except (OSError, ValueError):
        return None
    return pid if pid > 0 else None


def _clear_pidfile() -> None:
    pidfile_path().unlink(missing_ok=True)


def _is_ollama_serve(pid: int) -> bool:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return False
    parts = raw.decode("utf-8", errors="replace").split("\x00")
    names = [Path(part).name for part in parts if part]
    return "ollama" in names and "serve" in parts


def _stop_model_quietly() -> None:
    binary = find_ollama()
    if binary is None:
        return
    try:
        subprocess.run(
            [str(binary), "stop", ollama_model()],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass


def _terminate_pid(pid: int) -> None:
    if not _signal_pid(pid, signal.SIGTERM):
        return
    if _wait_exit(pid, 4.0):
        return
    _signal_pid(pid, signal.SIGKILL)
    _wait_exit(pid, 1.0)


def _signal_pid(pid: int, sig: int) -> bool:
    try:
        os.killpg(pid, sig)
        return True
    except ProcessLookupError:
        return False
    except OSError:
        try:
            os.kill(pid, sig)
            return True
        except ProcessLookupError:
            return False
        except OSError:
            return False


def _wait_exit(pid: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            time.sleep(0.1)
            continue
        time.sleep(0.1)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except OSError:
        return False
    return False


def _wait_until_running(*, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if ollama_is_running(timeout=0.5):
            return
        time.sleep(0.25)
    raise RuntimeError("Ollama started but did not begin listening. Check ~/.local/share/ludo/ollama.log")


def pull_model(model: str, on_progress: ProgressFn | None = None) -> None:
    report = on_progress or (lambda _msg: None)
    payload = json.dumps({"model": model, "stream": True}).encode("utf-8")
    request = urllib.request.Request(
        f"{_ollama_host()}/api/pull",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=None) as response:
            for raw in response:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if data.get("error"):
                    raise RuntimeError(str(data["error"]))
                status = str(data.get("status") or "")
                completed = data.get("completed")
                total = data.get("total")
                if isinstance(completed, int) and isinstance(total, int) and total:
                    pct = min(100, int(completed * 100 / total))
                    report(f"Downloading {model}… {pct}%")
                elif status:
                    report(status)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(detail or f"HTTP {exc.code} while pulling {model}") from exc


def warmup(model: str) -> None:
    payload = {
        "model": model,
        "prompt": "hi",
        "stream": False,
        "options": {"num_predict": 1},
    }
    _post_json(f"{_ollama_host()}/api/generate", payload, timeout=90)
