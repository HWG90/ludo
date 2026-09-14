from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandMap:
    windows: str
    linux: str
    note: str
    aliases: tuple[str, ...] = ()


COMMANDS: tuple[CommandMap, ...] = (
    CommandMap("dir", "ls -l", "List files. `ls -la` includes hidden files. `eza`/`lsd` are prettier if you install them.", ("ls",)),
    CommandMap("cls", "clear", "Clear the screen. Ctrl+L does the same in most terminals."),
    CommandMap("cd", "cd", "Same command. `cd ~` or `cd` with no args returns home. `cd -` toggles the previous folder."),
    CommandMap("cd /d D:\\Games", "cd /mnt/games", "No drive letters. Mount the disk once, then it is just a folder."),
    CommandMap("copy", "cp", "`cp file dest`. Add `-r` to copy a folder. Destinations are paths, not drive letters."),
    CommandMap("move", "mv", "Also how you rename: `mv oldname newname`."),
    CommandMap("ren", "mv", "Rename is move. Same inode dance, different vintage of command name.", ("rename",)),
    CommandMap("del", "rm", "Deletes immediately. No Recycle Bin. `trash-put` is the safer GUI-like option if installed.", ("erase",)),
    CommandMap("rmdir", "rmdir", "Empty folders only. `rm -r folder` removes a tree. Double-check the path."),
    CommandMap("mkdir", "mkdir -p", "`-p` creates parents and does not complain if it already exists."),
    CommandMap("type", "cat", "`bat` is cat with syntax highlighting if you install it. `less` pages long files."),
    CommandMap("more", "less", "q to quit. `/search` to find. Arrow keys to move. `less` is more."),
    CommandMap("ipconfig", "ip addr", "`ip route` for the default gateway. `nmcli` if you want NetworkManager's view.", ("ipconfig /all",)),
    CommandMap("ipconfig /flushdns", "resolvectl flush-caches", "On systemd-resolved systems. Some distros still use `nscd` or just NetworkManager."),
    CommandMap("ping", "ping", "Same tool. Ctrl+C to stop. Linux pings forever by default, unlike Windows' four packets."),
    CommandMap("tracert", "traceroute", "May need to install the package. `mtr` is the live version."),
    CommandMap("nslookup", "dig", "`host` is the short one. `resolvectl query` talks to systemd-resolved."),
    CommandMap("tasklist", "ps aux", "`btop` / `htop` if you want Task Manager energy."),
    CommandMap("taskkill", "kill", "`kill PID` or `killall name`. `kill -9` is End Task, but try without -9 first.", ("taskkill /f",)),
    CommandMap("shutdown /s", "systemctl poweroff", "`shutdown now` also works. Use the menu if you are not in love with the terminal.", ("shutdown",)),
    CommandMap("shutdown /r", "systemctl reboot", "Reboot. NVIDIA/kernel updates are the usual reason."),
    CommandMap("sfc /scannow", "Your package manager's verify/reinstall", "There is no one system-file checker. Reinstall the broken package instead."),
    CommandMap("chkdsk", "fsck", "Unmount first, or do it from a live USB. Do not fsck a disk that is in use."),
    CommandMap("diskpart", "lsblk / fdisk / parted / GNOME Disks", "Look with `lsblk` first. Partitioning is a GUI job until you are comfortable."),
    CommandMap("netstat -ab", "ss -tulpn", "See listening ports and which process owns them."),
    CommandMap("whoami", "whoami", "Same. `id` adds groups, which is how sudo and plugdev actually work."),
    CommandMap("hostname", "hostname", "`hostnamectl` on systemd distros adds pretty name and chassis."),
    CommandMap("systeminfo", "hostnamectl && lscpu && fastfetch", "Or just `ludo checkup`. `uname -a` is the kernel line."),
    CommandMap("set", "env", "`echo $VAR` reads one. `export VAR=value` sets one for this shell and children."),
    CommandMap("echo %PATH%", "echo $PATH", "Colon-separated, not semicolon-separated."),
    CommandMap("findstr", "grep", "`rg` (ripgrep) is faster and ignores .git. `grep -R` walks a tree."),
    CommandMap("where", "which", "`command -v` is the POSIX version. `whereis` also hunts man pages."),
    CommandMap("start notepad", "xdg-open file", "Opens with the default app. `code .` still works if VS Code/Cursor is installed.", ("start",)),
    CommandMap("explorer .", "xdg-open .", "Opens the current folder in the file manager. `open` on some setups too."),
    CommandMap("clip", "wl-copy / xclip", "Wayland: `wl-copy`. X11: `xclip -selection clipboard`. Pipe into it."),
    CommandMap("tree", "tree", "Install the `tree` package, or `ls -R`."),
    CommandMap("attrib", "ls -l / chmod / chattr", "The executable bit matters more than hidden/system flags."),
    CommandMap("fc", "diff", "`diff -u` is the readable one. `git diff` if it is a repo."),
    CommandMap("xcopy / robocopy", "rsync -a", "The grown-up copy. `--progress` if you want a status bar.", ("robocopy", "xcopy")),
    CommandMap("format", "mkfs", "This will wipe a disk. Use GNOME Disks until that sentence feels appropriately loud."),
    CommandMap("gpupdate", "(no domain Group Policy)", "System settings are files and dconf. Corporate Linux uses other tools; home users ignore this."),
    CommandMap("winver", "lsb_release -a / cat /etc/os-release", "Or `ludo checkup`. There is no Build 22631 to recite at tech support."),
    CommandMap("dxdiag", "ludo checkup", "Add `vulkaninfo --summary` and `nvidia-smi` (NVIDIA) when a game forum asks for proof."),
    CommandMap("msconfig", "systemctl / Cockpit / your startup apps settings", "Disable services carefully. Disabling NetworkManager 'to go faster' is a rite of passage you can skip."),
    CommandMap("control", "Your desktop's Settings app", "Also `gnome-control-center` or `systemsettings` if you like launching them by name."),
    CommandMap("powershell", "bash / zsh / fish / python", "PowerShell exists on Linux too, but you will have more friends in bash or fish."),
    CommandMap("wget (Windows port)", "curl -LO URL", "`wget` is often installed as well. `curl` is the one you will see in docs."),
    CommandMap("Get-Process", "ps aux / btop", "Same question, less object piping until you learn `jq`."),
    CommandMap("Get-Content", "cat / less / tail -f", "`tail -f logfile` is the live view."),
    CommandMap("iisreset", "systemctl restart nginx", "Or apache2/caddy/httpd depending on what you actually installed."),
    CommandMap("netsh wlan show profile", "nmcli device wifi list", "`nmtui` is the friendly full-screen version."),
)


def _needles(entry: CommandMap) -> list[str]:
    values = [entry.windows, *entry.aliases]
    expanded: list[str] = []
    for value in values:
        expanded.append(value.lower())
        expanded.append(value.lower().split()[0])
    return expanded


def translate_command(query: str, entries: tuple[CommandMap, ...] = COMMANDS) -> list[CommandMap]:
    needle = query.strip().lower()
    if not needle:
        return list(entries)
    exact: list[CommandMap] = []
    fuzzy: list[CommandMap] = []
    for entry in entries:
        names = _needles(entry)
        if needle in names or needle == entry.linux.lower():
            exact.append(entry)
        elif needle in entry.windows.lower() or needle in entry.note.lower() or needle in entry.linux.lower():
            fuzzy.append(entry)
    return exact or fuzzy
