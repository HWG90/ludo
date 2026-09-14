from __future__ import annotations

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
