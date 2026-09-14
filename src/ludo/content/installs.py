from __future__ import annotations

from dataclasses import dataclass

from ludo.probe import SystemProfile

InstallMap = dict[str, str]


def pick(commands: InstallMap, profile: SystemProfile) -> str:
    family = profile.family
    manager = profile.package_manager
    if manager in commands:
        return commands[manager]
    if family in commands:
        return commands[family]
    return commands.get("generic", next(iter(commands.values())))


STEAM: InstallMap = {
    "pacman": "sudo pacman -S steam",
    "arch": "sudo pacman -S steam",
    "dnf": "sudo dnf install steam",
    "fedora": "sudo dnf install steam   # enable RPM Fusion if the package is missing",
    "apt": "sudo apt update && sudo apt install steam",
    "debian": "sudo dpkg --add-architecture i386 && sudo apt update && sudo apt install steam",
    "generic": "Install Steam from your distro's repo, or Flatpak: flatpak install flathub com.valvesoftware.Steam",
}

FLATPAK_STEAM = "flatpak install flathub com.valvesoftware.Steam"

MANGOHUD: InstallMap = {
    "pacman": "sudo pacman -S mangohud",
    "dnf": "sudo dnf install mangohud",
    "apt": "sudo apt install mangohud",
    "generic": "flatpak install flathub org.freedesktop.Platform.VulkanLayer.MangoHud",
}

GAMEMODE: InstallMap = {
    "pacman": "sudo pacman -S gamemode",
    "dnf": "sudo dnf install gamemode",
    "apt": "sudo apt install gamemode",
    "generic": "Install the gamemode package, then launch with gamemoderun %command%",
}

GAMESCOPE: InstallMap = {
    "pacman": "sudo pacman -S gamescope",
    "dnf": "sudo dnf install gamescope",
    "apt": "sudo apt install gamescope",
    "generic": "Install gamescope from your distro (Steam Deck's compositor, useful on desktops too).",
}

HEROIC: InstallMap = {
    "pacman": "flatpak install flathub com.heroicgameslauncher.hgl",
    "generic": "flatpak install flathub com.heroicgameslauncher.hgl",
}

LUTRIS: InstallMap = {
    "pacman": "sudo pacman -S lutris",
    "dnf": "sudo dnf install lutris",
    "apt": "sudo apt install lutris",
    "generic": "flatpak install flathub net.lutris.Lutris",
}

NVIDIA_DRIVER: InstallMap = {
    "pacman": "sudo pacman -S nvidia nvidia-utils nvidia-settings   # nvidia-open on newer cards; check CachyOS/NVIDIA docs",
    "dnf": "sudo dnf install akmod-nvidia   # from RPM Fusion",
    "apt": "sudo apt install nvidia-driver-580   # version number follows the distro; Ubuntu's 'Additional Drivers' is safer",
    "generic": "Use your distro's NVIDIA driver package. Avoid random .run installers from nvidia.com unless you know why.",
}


@dataclass(frozen=True)
class AppInstall:
    name: str
    aliases: tuple[str, ...]
    command: InstallMap
    note: str
    guide_id: str = "software"


APPS: tuple[AppInstall, ...] = (
    AppInstall(
        name="Discord",
        aliases=("discord",),
        command={
            "pacman": "sudo pacman -S discord",
            "arch": "sudo pacman -S discord",
            "apt": "flatpak install flathub com.discordapp.Discord",
            "dnf": "flatpak install flathub com.discordapp.Discord",
            "generic": "flatpak install flathub com.discordapp.Discord",
        },
        note="Skip the Windows .exe. Voice and screenshare work on a current distro.",
        guide_id="daily-apps",
    ),
    AppInstall(
        name="Spotify",
        aliases=("spotify",),
        command={"generic": "flatpak install flathub com.spotify.Client"},
        note="Flatpak is the straightforward Linux install.",
        guide_id="daily-apps",
    ),
    AppInstall(
        name="Google Chrome",
        aliases=("chrome", "google chrome"),
        command={
            "pacman": "Install via your AUR helper, or: flatpak install flathub com.google.Chrome",
            "apt": "Use Google’s .deb, or: flatpak install flathub com.google.Chrome",
            "generic": "flatpak install flathub com.google.Chrome",
        },
        note="Firefox and Chromium are in most distro repos if you do not need Chrome specifically.",
        guide_id="daily-apps",
    ),
    AppInstall(
        name="Firefox",
        aliases=("firefox",),
        command={
            "pacman": "sudo pacman -S firefox",
            "dnf": "sudo dnf install firefox",
            "apt": "sudo apt install firefox",
            "generic": "flatpak install flathub org.mozilla.firefox",
        },
        note="Usually a one-package distro install.",
        guide_id="daily-apps",
    ),
    AppInstall(
        name="VS Code",
        aliases=("vscode", "vs code", "visual studio code"),
        command={"generic": "flatpak install flathub com.visualstudio.code"},
        note="Cursor also has a Linux build. Search your store for “Visual Studio Code” or install the Flatpak.",
        guide_id="daily-apps",
    ),
    AppInstall(
        name="OBS Studio",
        aliases=("obs", "obs studio"),
        command={
            "pacman": "sudo pacman -S obs-studio",
            "dnf": "sudo dnf install obs-studio",
            "apt": "sudo apt install obs-studio",
            "generic": "flatpak install flathub com.obsproject.Studio",
        },
        note="Native package or Flatpak both work. Wayland capture is fine on a current stack.",
        guide_id="daily-apps",
    ),
    AppInstall(
        name="Heroic",
        aliases=("heroic", "epic"),
        command=HEROIC,
        note="Epic / GOG launcher on Linux. Install once, then add Proton inside it.",
        guide_id="gaming-stack",
    ),
    AppInstall(
        name="Lutris",
        aliases=("lutris",),
        command=LUTRIS,
        note="Another game hub, useful for outside-Steam Windows titles.",
        guide_id="gaming-stack",
    ),
)
