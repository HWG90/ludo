from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

VENDOR_NVIDIA = "10de"
VENDOR_AMD = "1002"
VENDOR_INTEL = "8086"

VENDOR_NAMES = {
    VENDOR_NVIDIA: "NVIDIA",
    VENDOR_AMD: "AMD",
    VENDOR_INTEL: "Intel",
}


@dataclass(frozen=True)
class Gpu:
    name: str
    vendor: str
    vendor_id: str = ""


@dataclass(frozen=True)
class SteamStatus:
    installed: bool
    native: bool = False
    flatpak: bool = False
    root: Path | None = None
    proton_official: bool = False
    proton_ge: bool = False


@dataclass
class SystemProfile:
    distro_id: str = "unknown"
    distro_name: str = "Linux"
    distro_like: tuple[str, ...] = ()
    version: str = ""
    kernel: str = ""
    desktop: str = ""
    session: str = ""
    package_manager: str = "unknown"
    gpus: list[Gpu] = field(default_factory=list)
    vulkan: bool | None = None
    steam: SteamStatus = field(default_factory=lambda: SteamStatus(installed=False))
    flatpak: bool = False
    gamemode: bool = False
    mangohud: bool = False
    gamescope: bool = False
    hostname: str = ""
    cpu: str = ""
    memory_gb: float | None = None

    @property
    def primary_gpu(self) -> Gpu | None:
        return self.gpus[0] if self.gpus else None

    @property
    def family(self) -> str:
        ids = {self.distro_id, *self.distro_like}
        if ids & {"arch", "cachyos", "endeavouros", "manjaro", "artix"}:
            return "arch"
        if ids & {"fedora", "rhel", "centos", "nobara", "bazzite"}:
            return "fedora"
        if ids & {"ubuntu", "debian", "linuxmint", "pop", "elementary"}:
            return "debian"
        if ids & {"opensuse", "opensuse-tumbleweed", "opensuse-leap"}:
            return "suse"
        return self.distro_id


def probe(env: dict[str, str] | None = None, os_release_path: Path | None = None) -> SystemProfile:
    environ = env if env is not None else os.environ
    os_release = read_os_release(os_release_path or Path("/etc/os-release"))
    like = tuple(
        part
        for part in os_release.get("ID_LIKE", "").replace(",", " ").split()
        if part
    )
    memory = _memory_gb()
    return SystemProfile(
        distro_id=os_release.get("ID", "unknown"),
        distro_name=os_release.get("PRETTY_NAME") or os_release.get("NAME") or "Linux",
        distro_like=like,
        version=os_release.get("VERSION_ID", ""),
        kernel=_kernel(),
        desktop=_desktop(environ),
        session=environ.get("XDG_SESSION_TYPE", "") or _guess_session(),
        package_manager=detect_package_manager(),
        gpus=detect_gpus(),
        vulkan=detect_vulkan(),
        steam=detect_steam(),
        flatpak=shutil.which("flatpak") is not None,
        gamemode=shutil.which("gamemoderun") is not None or shutil.which("gamemode") is not None,
        mangohud=shutil.which("mangohud") is not None,
        gamescope=shutil.which("gamescope") is not None,
        hostname=os.uname().nodename if hasattr(os, "uname") else "",
        cpu=_cpu_model(),
        memory_gb=memory,
    )


def read_os_release(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return data
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key] = value.strip().strip('"').strip("'")
    return data


def detect_package_manager() -> str:
    for name in ("pacman", "apt", "dnf", "zypper", "apk", "emerge", "xbps-install"):
        if shutil.which(name):
            return name
    return "unknown"


def detect_gpus() -> list[Gpu]:
    from_lspci = _gpus_from_lspci()
    if from_lspci:
        return from_lspci
    return _gpus_from_sysfs()


def detect_vulkan() -> bool | None:
    icd_dir = Path("/usr/share/vulkan/icd.d")
    extra = Path("/etc/vulkan/icd.d")
    icds = []
    if icd_dir.is_dir():
        icds.extend(icd_dir.glob("*.json"))
    if extra.is_dir():
        icds.extend(extra.glob("*.json"))
    if icds:
        return True
    if shutil.which("vulkaninfo"):
        result = _run(["vulkaninfo", "--summary"], timeout=4)
        if result is None:
            return None
        return result.returncode == 0
    return None


def detect_steam() -> SteamStatus:
    native = shutil.which("steam") is not None
    flatpak = _flatpak_app_installed("com.valvesoftware.Steam")
    root = _steam_root()
    installed = native or flatpak or root is not None
    proton_official = False
    proton_ge = False
    if root is not None:
        common = root / "steamapps" / "common"
        if common.is_dir():
            proton_official = any(p.name.startswith("Proton") for p in common.iterdir())
        compat = root / "compatibilitytools.d"
        if compat.is_dir():
            proton_ge = any("GE" in p.name or "proton" in p.name.lower() for p in compat.iterdir())
        user_compat = Path.home() / ".steam" / "root" / "compatibilitytools.d"
        if not proton_ge and user_compat.is_dir():
            proton_ge = any(user_compat.iterdir())
    return SteamStatus(
        installed=installed,
        native=native,
        flatpak=flatpak,
        root=root,
        proton_official=proton_official,
        proton_ge=proton_ge,
    )


def _steam_root() -> Path | None:
    candidates = [
        Path.home() / ".local" / "share" / "Steam",
        Path.home() / ".steam" / "steam",
        Path.home() / ".steam" / "root",
        Path.home() / ".var" / "app" / "com.valvesoftware.Steam" / "data" / "Steam",
    ]
    for path in candidates:
        if (path / "steamapps").is_dir() or (path / "steam.sh").is_file():
            return path
    return None


def _flatpak_app_installed(app_id: str) -> bool:
    if shutil.which("flatpak") is None:
        return False
    result = _run(["flatpak", "info", app_id], timeout=4)
    return bool(result and result.returncode == 0)


def _gpus_from_sysfs() -> list[Gpu]:
    drm = Path("/sys/class/drm")
    if not drm.is_dir():
        return []
    found: list[Gpu] = []
    seen: set[str] = set()
    for card in sorted(drm.glob("card[0-9]")):
        device = card / "device"
        vendor_file = device / "vendor"
        if not vendor_file.is_file():
            continue
        try:
            vendor_id = vendor_file.read_text(encoding="utf-8").strip().removeprefix("0x")
        except OSError:
            continue
        ident = str(device.resolve()) if device.exists() else str(card)
        if ident in seen:
            continue
        seen.add(ident)
        name_file = device / "uevent"
        model = _gpu_name_from_uevent(name_file)
        driver_labels = {
            "nvidia": "NVIDIA GPU",
            "amdgpu": "AMD GPU",
            "radeon": "AMD GPU",
            "i915": "Intel GPU",
            "xe": "Intel GPU",
            "nouveau": "NVIDIA (nouveau)",
        }
        if model.lower() in driver_labels:
            model = driver_labels[model.lower()]
        elif not model:
            model = VENDOR_NAMES.get(vendor_id, "Unknown GPU")
        if vendor_id in VENDOR_NAMES and VENDOR_NAMES[vendor_id] not in model:
            model = f"{VENDOR_NAMES[vendor_id]} {model}"
        found.append(Gpu(name=model, vendor=VENDOR_NAMES.get(vendor_id, "Unknown"), vendor_id=vendor_id))
    return found


def _gpu_name_from_uevent(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    for line in text.splitlines():
        if line.startswith("DRIVER="):
            return line.split("=", 1)[1].strip()
    return ""


def _clean_lspci_name(name: str) -> str:
    name = re.sub(r"\s*\[[0-9a-f]{4}:[0-9a-f]{4}\]", "", name, flags=re.I)
    name = re.sub(r"\s*\(rev [0-9a-f]+\)", "", name, flags=re.I)
    return name.strip()


def _gpus_from_lspci() -> list[Gpu]:
    if shutil.which("lspci") is None:
        return []
    result = _run(["lspci", "-nn"], timeout=3)
    if not result or result.returncode != 0:
        return []
    gpus: list[Gpu] = []
    for line in result.stdout.splitlines():
        lowered = line.lower()
        if "vga compatible controller" not in lowered and "3d controller" not in lowered:
            continue
        vendor = "Unknown"
        vendor_id = ""
        if "nvidia" in lowered:
            vendor = "NVIDIA"
            vendor_id = VENDOR_NVIDIA
        elif "amd" in lowered or "ati" in lowered:
            vendor = "AMD"
            vendor_id = VENDOR_AMD
        elif "intel" in lowered:
            vendor = "Intel"
            vendor_id = VENDOR_INTEL
        name = _clean_lspci_name(line.split(": ", 1)[-1].strip())
        gpus.append(Gpu(name=name, vendor=vendor, vendor_id=vendor_id))
    return gpus


def _desktop(environ: dict[str, str]) -> str:
    current = environ.get("XDG_CURRENT_DESKTOP") or environ.get("DESKTOP_SESSION") or ""
    return current.replace(":", " / ")


def _guess_session() -> str:
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return ""


def _kernel() -> str:
    try:
        return os.uname().release
    except AttributeError:
        return ""


def _cpu_model() -> str:
    cpuinfo = Path("/proc/cpuinfo")
    if not cpuinfo.is_file():
        return ""
    try:
        for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        return ""
    return ""


def _memory_gb() -> float | None:
    meminfo = Path("/proc/meminfo")
    if not meminfo.is_file():
        return None
    try:
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                kb = int(line.split()[1])
                return round(kb / 1024 / 1024, 1)
    except (OSError, ValueError, IndexError):
        return None
    return None


def _run(cmd: list[str], timeout: float) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
