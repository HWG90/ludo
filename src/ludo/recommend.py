from __future__ import annotations

from dataclasses import dataclass

from ludo.probe import SystemProfile


@dataclass(frozen=True)
class Recommendation:
    level: str  # good, next, warn
    title: str
    detail: str
    guide_id: str | None = None


def recommend(profile: SystemProfile) -> list[Recommendation]:
    items: list[Recommendation] = []
    gpu = profile.primary_gpu

    if gpu:
        items.append(
            Recommendation(
                "good" if profile.vulkan else "next",
                f"{gpu.vendor} graphics detected",
                _gpu_detail(profile),
                "gpu",
            )
        )
    else:
        items.append(
            Recommendation(
                "warn",
                "No GPU detected",
                "Ludo could not see a graphics card. That is unusual. Open the GPU guide if games or the desktop look wrong.",
                "gpu",
            )
        )

    if profile.vulkan is False:
        items.append(
            Recommendation(
                "warn",
                "Vulkan looks missing",
                "Most Steam games on Linux talk to Vulkan. Install drivers from the GPU guide, then check again.",
                "gpu",
            )
        )
    elif profile.vulkan:
        items.append(
            Recommendation(
                "good",
                "Vulkan is available",
                "Proton and native Linux games can talk to your GPU. This is the green light for gaming.",
                "steam-proton",
            )
        )

    if not profile.steam.installed:
        items.append(
            Recommendation(
                "next",
                "Steam is not installed yet",
                "You can still use Linux as a daily driver without it. When you are ready, the Steam guide covers Proton in a few clicks.",
                "steam-proton",
            )
        )
    else:
        source = "native package" if profile.steam.native else "Flatpak" if profile.steam.flatpak else "existing library"
        proton = (
            "Official Proton is on disk."
            if profile.steam.proton_official
            else "Enable Proton in Steam → Settings → Compatibility when you are ready."
        )
        extra = " Proton-GE is installed too." if profile.steam.proton_ge else ""
        items.append(
            Recommendation(
                "good" if profile.steam.proton_official or profile.steam.proton_ge else "next",
                f"Steam is installed ({source})",
                f"{proton}{extra}",
                "steam-proton",
            )
        )

    if profile.package_manager != "unknown":
        items.append(
            Recommendation(
                "good",
                f"Software installs use {profile.package_manager}",
                "That is your 'download the installer' replacement. The software guide maps Windows habits onto it.",
                "software",
            )
        )

    if profile.flatpak:
        items.append(
            Recommendation(
                "good",
                "Flatpak is available",
                "Sandbox apps (Discord, Heroic, Bottles, many games) can be installed the same way on almost every distro.",
                "software",
            )
        )

    missing_tools = [
        name
        for name, present in (
            ("MangoHud", profile.mangohud),
            ("GameMode", profile.gamemode),
            ("gamescope", profile.gamescope),
        )
        if not present
    ]
    if missing_tools:
        items.append(
            Recommendation(
                "next",
                "Optional gaming tools",
                "Not installed yet: " + ", ".join(missing_tools) + ". Nice later, not required for day one.",
                "gaming-stack",
            )
        )

    if profile.session == "x11" and gpu and gpu.vendor == "AMD":
        items.append(
            Recommendation(
                "next",
                "This session is X11",
                "AMD + Wayland is usually the smoother modern desktop. Switching is a login-screen choice, not a reinstall.",
                "desktop",
            )
        )

    return items


def _gpu_detail(profile: SystemProfile) -> str:
    gpu = profile.primary_gpu
    assert gpu is not None
    if gpu.vendor == "NVIDIA":
        return "NVIDIA on Linux wants the proprietary driver for gaming. The GPU guide covers the distro-specific install."
    if gpu.vendor == "AMD":
        return "AMD is the easy mode on Linux: Mesa is usually already there. Keep the system updated and play."
    if gpu.vendor == "Intel":
        return "Intel iGPUs run Mesa too. Great for desktop use and lighter games; Proton still works."
    return gpu.name
