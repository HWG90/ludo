from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GlossaryEntry:
    windows: str
    linux: str
    why: str
    tags: tuple[str, ...]


GLOSSARY: tuple[GlossaryEntry, ...] = (
    GlossaryEntry(
        "Windows key / Start menu",
        "Super key — opens the launcher / application menu (Kickoff, GNOME Activities, wofi, etc.)",
        "Same physical key. Distros just give it a different name so it is not trademarked.",
        ("desktop", "keyboard"),
    ),
    GlossaryEntry(
        "File Explorer",
        "Files (GNOME), Dolphin (KDE), Nemo, Thunar, or `ls` / `cd` in a terminal",
        "Still a window with a sidebar. Hidden files are Ctrl+H instead of a folder option buried in View.",
        ("files", "desktop"),
    ),
    GlossaryEntry(
        "Task Manager (Ctrl+Shift+Esc)",
        "System Monitor, KDE System Monitor, `btop`, `htop`, or `plasma-systemmonitor`",
        "Same job: see CPU, RAM, and kill a stuck process. `kill` / `killall` is the command-line version of End Task.",
        ("system", "keyboard"),
    ),
    GlossaryEntry(
        "Ctrl+C / Ctrl+V in a terminal",
        "Ctrl+Shift+C / Ctrl+Shift+V (or Ctrl+Insert / Shift+Insert)",
        "Ctrl+C already meant 'cancel this command' in Unix decades before Windows copy. The Shift is the truce.",
        ("terminal", "keyboard"),
    ),
    GlossaryEntry(
        "Ctrl+C to cancel in cmd",
        "Ctrl+C still cancels. Ctrl+D hangs up (end of input). Ctrl+Z suspends.",
        "Your cancel reflex still works. The extra signals are new power, not new danger.",
        ("terminal", "keyboard"),
    ),
    GlossaryEntry(
        "Run as administrator",
        "`sudo` for one command, or a polkit dialog when a GUI settings app needs elevation",
        "You opt in per command instead of opening an Admin Command Prompt for the rest of the hour.",
        ("system", "terminal"),
    ),
    GlossaryEntry(
        "Control Panel / Settings",
        "GNOME Settings, KDE System Settings, or `settings` from the launcher",
        "Displays, Wi-Fi, Bluetooth, users, and updates all live there. The old 'twelve Control Panel applets' maze is gone.",
        ("desktop", "system"),
    ),
    GlossaryEntry(
        "Device Manager",
        "Most hardware just works. For GPUs see drivers; for details: `lspci`, `lsusb`, and your distro's driver utility.",
        "You rarely hunt yellow-bang devices. When something is missing it is usually firmware or NVIDIA.",
        ("system", "hardware"),
    ),
    GlossaryEntry(
        "Recycle Bin",
        "Trash in the file manager. `rm` skips it.",
        "GUI delete is reversible. Terminal `rm` is not. That is the one rule that saves holidays.",
        ("files",),
    ),
    GlossaryEntry(
        "C:\\ , D:\\ drive letters",
        "One tree starting at `/`. Extra disks appear under `/mnt`, `/run/media/you`, or `/media`.",
        "A partition is a folder, not a letter. Dual-boot Windows often shows up as a folder you can open.",
        ("files",),
    ),
    GlossaryEntry(
        "C:\\Users\\You",
        "`/home/you` (also `~`)",
        "Documents, Downloads, Pictures, and Desktop are still there. Configs hide in `~/.config`.",
        ("files",),
    ),
    GlossaryEntry(
        "Program Files",
        "Distro packages in `/usr`, Flatpaks in `/var/lib/flatpak`, user apps in `~/.local`",
        "You do not pick the install folder. The system does, and uninstallers actually uninstall.",
        ("software", "files"),
    ),
    GlossaryEntry(
        "AppData",
        "`~/.config`, `~/.local/share`, and `~/.cache`",
        "Same idea as roaming/local/temp, just three visible folders instead of a hidden maze behind AppData.",
        ("files",),
    ),
    GlossaryEntry(
        "Registry Editor",
        "Plain config files, dconf/KDE settings, and sometimes `/etc`",
        "There is no single hive to corrupt. Back up a dotfile, not a binary blob.",
        ("system",),
    ),
    GlossaryEntry(
        "Services (services.msc)",
        "systemd units: `systemctl status|start|stop|enable name`",
        "Boot-time stuff is still a list of services. The names are just less Windows-shaped.",
        ("system", "terminal"),
    ),
    GlossaryEntry(
        "Environment Variables / PATH",
        "`echo $PATH`, `export FOO=bar`, and `~/.profile` / `~/.bashrc` / `~/.zshrc`",
        "Same concept. User PATH often lives in your shell config instead of a System Properties dialog.",
        ("terminal", "system"),
    ),
    GlossaryEntry(
        "Windows Update",
        "Your package manager plus GNOME Software / Discover / `pkcon` / `pacman -Syu`",
        "OS, drivers, and many apps update together. Reboots are rarer except for kernel/NVIDIA.",
        ("software", "system"),
    ),
    GlossaryEntry(
        "Microsoft Store / downloaded Setup.exe",
        "Distro repo, Flathub, AppImage, or occasionally a vendor .deb/.rpm",
        "The healthy default is the store. Random installers from the web are how people get malware on Windows too.",
        ("software",),
    ),
    GlossaryEntry(
        ".exe / .msi installers",
        "Native packages, Flatpak, AppImage, or Proton/Wine if it truly is a Windows program",
        "A Windows installer is not a Linux program. Games get Proton. Productivity apps should be native or web.",
        ("software", "gaming"),
    ),
    GlossaryEntry(
        "Defender / antivirus",
        "A narrower attack surface, distro repos, Flatpak sandboxing, and optionally ClamAV",
        "You still should not run random binaries. You usually do not need a red-shield tray icon.",
        ("system",),
    ),
    GlossaryEntry(
        "Display Settings / NVIDIA Control Panel",
        "Settings → Display; NVIDIA Settings; KScreen; Gamescope for per-game compositor tricks",
        "Refresh rate, VRR, and HDR support depend on Wayland + driver. This is the area that improved fastest in recent years.",
        ("desktop", "gaming", "hardware"),
    ),
    GlossaryEntry(
        "Sound / Realtek tray icon",
        "PipeWire (or PulseAudio) via Settings, `pavucontrol`, or EasyEffects",
        "Headphones usually just work. Per-app volume is a first-class feature.",
        ("desktop",),
    ),
    GlossaryEntry(
        "Wi-Fi / Network and Sharing Center",
        "NetworkManager via the panel icon, Settings, or `nmtui` / `nmcli`",
        "Same SSID list, fewer mystery adapter names. VPNs are plugins instead of vendor tray apps.",
        ("system",),
    ),
    GlossaryEntry(
        "Printers",
        "CUPS, often configured in Settings. Many printers just appear.",
        "IPP everywhere helped a lot. The remaining pain is vendor-only scan software — use SANE or the web UI.",
        ("desktop",),
    ),
    GlossaryEntry(
        "Startup apps",
        "GNOME Tweaks / KDE Autostart, `~/.config/autostart`, or a systemd --user service",
        "Same idea as the Startup tab in Task Manager, without the surprise miner you forgot about in 2019.",
        ("desktop", "system"),
    ),
    GlossaryEntry(
        "Alt+Tab",
        "Alt+Tab still cycles windows. Super+Tab or Overview on GNOME is the fancier switcher.",
        "Keep the reflex. Then learn workspaces: they are better than 30 ungrouped taskbar icons.",
        ("desktop", "keyboard"),
    ),
    GlossaryEntry(
        "Win+E, Win+R, Win+L, Win+D",
        "Super+E (often), a runner (krunner/rofi), Super+L, Super+D — bindings vary and are editable",
        "Remap anything. Linux desktops expect you to own the keyboard.",
        ("keyboard", "desktop"),
    ),
    GlossaryEntry(
        "Snipping Tool / Win+Shift+S",
        "Spectacle, GNOME Screenshot, Flameshot, or Print Screen",
        "Flameshot is the crowd favorite if you annotate screenshots for friends who still use Windows.",
        ("desktop",),
    ),
    GlossaryEntry(
        "Notepad",
        "GNOME Text Editor, Kate, Mousepad, `nano`, or `micro`",
        "Kate is Notepad++ energy. VS Code / Cursor / Zed all have Linux builds.",
        ("software",),
    ),
    GlossaryEntry(
        "Notepad++",
        "Kate, VS Code, Cursor, Zed, Neovim",
        "You can keep tabs, syntax highlighting, and a plugin ecosystem. Vim is optional, not a personality test.",
        ("software",),
    ),
    GlossaryEntry(
        "Taskbar + system tray",
        "Panel + tray (KDE is closest). GNOME hides more in the calendar/status menu.",
        "If you want Windows muscle memory, KDE Plasma is the shortest jump.",
        ("desktop",),
    ),
    GlossaryEntry(
        "Show file extensions / hidden files",
        "File manager hamburger menu, or Ctrl+H. In a terminal, `ls -a`.",
        "Dotfiles (`~/.something`) are the hidden files. Extensions are always real — Linux does not infer 'this is a program' from .exe.",
        ("files",),
    ),
    GlossaryEntry(
        "Right-click → Properties",
        "Right-click → Properties / Permissions. `ls -l` and `chmod` / `chown` in a terminal.",
        "The executable bit replaces 'this is a .exe'. AppImages often need `chmod +x` once.",
        ("files",),
    ),
    GlossaryEntry(
        "dxdiag",
        "`ludo checkup`, `vulkaninfo --summary`, `glxinfo -B`, `nvidia-smi`, `fastfetch`",
        "Same 'what hardware is this' question. Ludo's checkup is the friendly version.",
        ("gaming", "hardware"),
    ),
    GlossaryEntry(
        "GeForce Experience / driver updates",
        "System updates, or the NVIDIA driver package from your distro",
        "No extra overlay account. Mesa (AMD/Intel) updates with the OS; NVIDIA still has a driver package of its own.",
        ("gaming", "hardware"),
    ),
    GlossaryEntry(
        "Epic / GOG / Battle.net / EA app",
        "Heroic, Lutris, Bottles, or native Linux builds when they exist",
        "Steam is the easy street. Other stores are playable, just one launcher more.",
        ("gaming",),
    ),
    GlossaryEntry(
        "DirectX",
        "Vulkan, with DXVK/VKD3D inside Proton translating Direct3D",
        "You do not install DirectX. Proton already brings the translation layer.",
        ("gaming",),
    ),
    GlossaryEntry(
        "PowerShell profile / .ps1 scripts",
        "Bash/Zsh/Fish plus `.bashrc` / `.zshrc`. Python is already on the machine.",
        "Pipelines still exist. `Get-ChildItem | Where-Object` becomes `ls | grep` or better tools later.",
        ("terminal",),
    ),
    GlossaryEntry(
        "Disk Management",
        "KDE Partition Manager, GNOME Disks, `lsblk`, `btrfs` tools, GParted",
        "Look, do not touch, until you have a backup. Resizing the Windows partition is the dual-boot boss fight.",
        ("system", "files"),
    ),
    GlossaryEntry(
        "Remote Desktop (mstsc)",
        "GNOME Remote Desktop, KRdp, Sunshine/Moonlight, or `ssh` for terminal work",
        "SSH is the Linux native remote story. For sitting at the desktop from the couch, Moonlight is what gamers actually use.",
        ("system",),
    ),
)


def search_glossary(query: str, entries: tuple[GlossaryEntry, ...] = GLOSSARY) -> list[GlossaryEntry]:
    needle = query.strip().lower()
    if not needle:
        return list(entries)
    hits: list[tuple[int, GlossaryEntry]] = []
    for entry in entries:
        blob = " ".join((entry.windows, entry.linux, entry.why, " ".join(entry.tags))).lower()
        if needle in blob:
            score = 0
            if needle in entry.windows.lower():
                score += 2
            if needle in entry.tags:
                score += 1
            hits.append((score, entry))
    hits.sort(key=lambda item: (-item[0], item[1].windows.lower()))
    return [entry for _, entry in hits]
