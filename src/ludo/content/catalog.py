from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from ludo.paths import guides_dir


@dataclass(frozen=True)
class QuizQuestion:
    prompt: str
    choices: tuple[str, ...]
    answer: int
    explain: str


@dataclass(frozen=True)
class Guide:
    id: str
    title: str
    section: str
    summary: str
    windows_hook: str
    minutes: int
    filename: str
    quiz: tuple[QuizQuestion, ...] = field(default_factory=tuple)

    def path(self, root: Path | None = None) -> Path:
        return (root or guides_dir()) / self.filename


GUIDES: tuple[Guide, ...] = (
    Guide(
        id="welcome",
        title="You already know this computer",
        section="foundations",
        summary="Linux is not a different universe. It is a different layout of skills you already have.",
        windows_hook="Same PC, different Start menu — and nobody is taking your files hostage.",
        minutes=6,
        filename="welcome.md",
        quiz=(
            QuizQuestion(
                prompt="What is a 'distribution' (distro)?",
                choices=(
                    "A different operating system unrelated to Linux",
                    "A Linux kernel plus a desktop, apps, and a software store, packaged as a product",
                    "A version of Windows that Valve ships with Steam",
                ),
                answer=1,
                explain="Ubuntu, Fedora, CachyOS, and SteamOS are all Linux. They differ in defaults, not in the idea of Linux.",
            ),
        ),
    ),
    Guide(
        id="terminal",
        title="The terminal without fear",
        section="foundations",
        summary="The terminal is PowerShell with less ceremony — and Ctrl+C does something else.",
        windows_hook="Think PowerShell or Command Prompt, not a hacker movie.",
        minutes=8,
        filename="terminal.md",
        quiz=(
            QuizQuestion(
                prompt="In a Linux terminal, what does Ctrl+C do?",
                choices=(
                    "Copy the selected text",
                    "Stop the running command (same idea as cancelling)",
                    "Close the window",
                ),
                answer=1,
                explain="Copy is usually Ctrl+Shift+C. Ctrl+C is the interrupt signal. This one habit prevents a lot of panic.",
            ),
        ),
    ),
    Guide(
        id="software",
        title="Installing software (no Setup.exe)",
        section="foundations",
        summary="Package managers and Flatpak replace downloaded installers — and they also update everything later.",
        windows_hook="The Microsoft Store idea, except it actually has the apps you want.",
        minutes=8,
        filename="software.md",
        quiz=(
            QuizQuestion(
                prompt="Why do Linux users care about a package manager?",
                choices=(
                    "It is the only way to browse the web",
                    "It installs, updates, and removes apps from trusted repos, like a system-wide app store",
                    "It converts .exe files into Linux programs",
                ),
                answer=1,
                explain="pacman, apt, dnf, and Flatpak are how software is supposed to arrive. Random installers from the web are the exception, not the default.",
            ),
        ),
    ),
    Guide(
        id="filesystem",
        title="There is no C: drive",
        section="foundations",
        summary="Everything hangs off /, your files live in /home, and names are case-sensitive.",
        windows_hook="C:\\Users\\You becomes /home/you — Photos and Downloads are still yours.",
        minutes=7,
        filename="filesystem.md",
        quiz=(
            QuizQuestion(
                prompt="Which path is your home folder on Linux?",
                choices=("/home/yourname", "/Users/yourname", "C:\\Linux\\Home"),
                answer=0,
                explain="~ and $HOME also mean your home folder. Root (/) is the whole system, not a recycle bin.",
            ),
        ),
    ),
    Guide(
        id="sudo-updates",
        title="Admin rights, updates, and not breaking things",
        section="foundations",
        summary="sudo is Run as administrator. Updates are normal. Random curl|bash is not.",
        windows_hook="UAC, but you typed it on purpose.",
        minutes=7,
        filename="sudo-updates.md",
        quiz=(
            QuizQuestion(
                prompt="When should you use sudo?",
                choices=(
                    "For every command, to be safe",
                    "Only when changing system-wide settings or installing system packages",
                    "To make games run faster",
                ),
                answer=1,
                explain="sudo is a scalpel. Daily file work in your home folder should not need it.",
            ),
        ),
    ),
    Guide(
        id="desktop",
        title="Taskbar, Start menu, and shortcuts",
        section="desktop",
        summary="KDE, GNOME, and friends are skins on the same OS. Your muscle memory can be remapped.",
        windows_hook="The Super key is the Windows key. It still opens a launcher.",
        minutes=7,
        filename="desktop.md",
        quiz=(
            QuizQuestion(
                prompt="What is a desktop environment?",
                choices=(
                    "The Linux kernel",
                    "The panel, launcher, settings, and window manager bundled as a workspace",
                    "A Steam library category",
                ),
                answer=1,
                explain="KDE Plasma, GNOME, Cosmic, and Cinnamon are desktop environments. You can change them without reinstalling Linux.",
            ),
        ),
    ),
    Guide(
        id="steam-proton",
        title="Steam, Proton, and Windows games",
        section="gaming",
        summary="Most of your Steam library is one compatibility toggle away. Proton is Wine, tuned by Valve.",
        windows_hook="Install Steam, enable Proton, press Play — the surprising part is that it often just works.",
        minutes=10,
        filename="steam-proton.md",
        quiz=(
            QuizQuestion(
                prompt="What does Proton do?",
                choices=(
                    "It virtualizes Windows like a full VM for every game",
                    "It translates Windows game APIs so they run on Linux, including DirectX via Vulkan",
                    "It replaces your GPU driver",
                ),
                answer=1,
                explain="Proton is a compatibility layer, not a virtual machine. That is why performance can match Windows so closely.",
            ),
        ),
    ),
    Guide(
        id="gpu",
        title="Graphics drivers that actually matter",
        section="gaming",
        summary="AMD and Intel usually work out of the box. NVIDIA wants its proprietary driver for gaming.",
        windows_hook="GeForce Experience is gone. The driver is a system package, and that is a good thing.",
        minutes=8,
        filename="gpu.md",
        quiz=(
            QuizQuestion(
                prompt="Which GPU vendor typically needs an extra proprietary driver for Linux gaming?",
                choices=("AMD", "Intel", "NVIDIA"),
                answer=2,
                explain="Mesa covers AMD and Intel well. NVIDIA gaming on Linux still means the NVIDIA driver package.",
            ),
        ),
    ),
    Guide(
        id="gaming-stack",
        title="The rest of the gaming stack",
        section="gaming",
        summary="Lutris, Heroic, MangoHud, GameMode, and gamescope — optional tools with Windows-shaped jobs.",
        windows_hook="Afterburner overlays, Epic/GOG launchers, and 'run this with these flags'.",
        minutes=8,
        filename="gaming-stack.md",
        quiz=(
            QuizQuestion(
                prompt="What is Heroic used for?",
                choices=(
                    "Replacing the Linux kernel with a gaming kernel",
                    "Playing Epic, GOG, and Amazon games with Proton/Wine",
                    "Benchmarking CPUs only",
                ),
                answer=1,
                explain="Steam does Steam. Heroic (and Lutris) cover storefronts Valve does not.",
            ),
        ),
    ),
    Guide(
        id="anticheat",
        title="Anti-cheat: the honest list",
        section="gaming",
        summary="Kernel anti-cheat is the remaining Windows-only wall. Check before you buy, not after.",
        windows_hook="If a game needs to sit inside Windows itself, Proton cannot magic that away.",
        minutes=6,
        filename="anticheat.md",
        quiz=(
            QuizQuestion(
                prompt="Before buying a competitive online game for Linux, what should you check?",
                choices=(
                    "Whether the box art includes a penguin",
                    "ProtonDB plus whether the anti-cheat supports Linux/Proton",
                    "If the game has a .exe, because that guarantees it will run",
                ),
                answer=1,
                explain="Easy Anti-Cheat and BattlEye sometimes work, sometimes do not — it is a per-game publisher choice.",
            ),
        ),
    ),
    Guide(
        id="dualboot",
        title="Keeping Windows around",
        section="daily",
        summary="Dual-boot, separate drives, and why NTFS for Steam libraries is a trap.",
        windows_hook="You do not have to burn the ships. You do have to respect two operating systems sharing a disk.",
        minutes=8,
        filename="dualboot.md",
        quiz=(
            QuizQuestion(
                prompt="Why is a Steam library on an NTFS partition a bad idea?",
                choices=(
                    "Steam cannot see NTFS at all",
                    "Linux permissions, case sensitivity, and file locking on NTFS break Proton games in ugly ways",
                    "NTFS is faster, so games will run too well",
                ),
                answer=1,
                explain="Keep Windows games on NTFS if you must. Put the Linux Steam library on ext4, btrfs, or xfs.",
            ),
        ),
    ),
    Guide(
        id="daily-apps",
        title="The daily driver app swap",
        section="daily",
        summary="Browser, Discord, Office, creative tools, and what still needs a browser tab or a VM.",
        windows_hook="You can keep Chrome. You cannot keep Outlook+Adobe+every bank dongle without a plan.",
        minutes=7,
        filename="daily-apps.md",
        quiz=(
            QuizQuestion(
                prompt="What is the least painful way to install Discord on most distros?",
                choices=(
                    "Download DiscordSetup.msi and run wine",
                    "Flatpak or your distro's package, then log in as usual",
                    "Recompile the kernel with Discord support",
                ),
                answer=1,
                explain="Discord ships a native Linux build. Flatpak is the 'works everywhere' option.",
            ),
        ),
    ),
)

FIRST_WEEK: tuple[str, ...] = (
    "welcome",
    "terminal",
    "software",
    "filesystem",
    "sudo-updates",
    "desktop",
    "steam-proton",
    "gpu",
)

SECTIONS = {
    "foundations": "Foundations",
    "desktop": "Desktop",
    "gaming": "Gaming",
    "daily": "Daily driver",
}


@lru_cache(maxsize=1)
def guides_by_id() -> dict[str, Guide]:
    return {guide.id: guide for guide in GUIDES}


def get_guide(guide_id: str) -> Guide:
    try:
        return guides_by_id()[guide_id]
    except KeyError as exc:
        raise KeyError(f"Unknown guide: {guide_id}") from exc


def load_guide_text(guide: Guide, root: Path | None = None) -> str:
    path = guide.path(root)
    return path.read_text(encoding="utf-8")


def first_week() -> list[Guide]:
    lookup = guides_by_id()
    return [lookup[guide_id] for guide_id in FIRST_WEEK]


def next_incomplete(completed: set[str]) -> Guide | None:
    for guide in first_week():
        if guide.id not in completed:
            return guide
    for guide in GUIDES:
        if guide.id not in completed:
            return guide
    return None
