from __future__ import annotations

from ludo.probe import Gpu, SteamStatus, SystemProfile


def gpu_label(gpus: list[Gpu]) -> str:
    if not gpus:
        return "not detected"
    labels: list[str] = []
    for gpu in gpus:
        if gpu.vendor.lower() in gpu.name.lower():
            labels.append(gpu.name)
        else:
            labels.append(f"{gpu.vendor}: {gpu.name}")
    return ", ".join(labels)


def steam_label(steam: SteamStatus) -> str:
    if not steam.installed:
        return "not installed"
    bits: list[str] = []
    if steam.native:
        bits.append("native")
    if steam.flatpak:
        bits.append("flatpak")
    if not bits:
        bits.append("library found")
    if steam.proton_ge:
        bits.append("Proton-GE")
    elif steam.proton_official:
        bits.append("Proton")
    return ", ".join(bits)


def vulkan_label(value: bool | None) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "unknown"


def profile_facts(profile: SystemProfile) -> list[tuple[str, str]]:
    memory = f"{profile.memory_gb} GB" if profile.memory_gb is not None else "unknown"
    session = profile.session or "unknown"
    desktop = profile.desktop or "unknown"
    return [
        ("Distro", profile.distro_name),
        ("Kernel", profile.kernel or "unknown"),
        ("Desktop", f"{desktop} ({session})"),
        ("CPU", profile.cpu or "unknown"),
        ("Memory", memory),
        ("GPU", gpu_label(profile.gpus)),
        ("Vulkan", vulkan_label(profile.vulkan)),
        ("Packages", profile.package_manager),
        ("Steam", steam_label(profile.steam)),
        ("Flatpak", "yes" if profile.flatpak else "no"),
        ("GameMode", "yes" if profile.gamemode else "no"),
        ("MangoHud", "yes" if profile.mangohud else "no"),
        ("gamescope", "yes" if profile.gamescope else "no"),
    ]


def profile_to_dict(profile: SystemProfile) -> dict:
    return {
        "distro_id": profile.distro_id,
        "distro_name": profile.distro_name,
        "distro_like": list(profile.distro_like),
        "family": profile.family,
        "version": profile.version,
        "kernel": profile.kernel,
        "desktop": profile.desktop,
        "session": profile.session,
        "package_manager": profile.package_manager,
        "gpus": [{"name": gpu.name, "vendor": gpu.vendor, "vendor_id": gpu.vendor_id} for gpu in profile.gpus],
        "vulkan": profile.vulkan,
        "steam": {
            "installed": profile.steam.installed,
            "native": profile.steam.native,
            "flatpak": profile.steam.flatpak,
            "root": str(profile.steam.root) if profile.steam.root else None,
            "proton_official": profile.steam.proton_official,
            "proton_ge": profile.steam.proton_ge,
        },
        "flatpak": profile.flatpak,
        "gamemode": profile.gamemode,
        "mangohud": profile.mangohud,
        "gamescope": profile.gamescope,
        "hostname": profile.hostname,
        "cpu": profile.cpu,
        "memory_gb": profile.memory_gb,
    }
