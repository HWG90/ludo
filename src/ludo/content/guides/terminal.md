# The terminal without fear

The terminal is PowerShell, not a ritual. You can use Linux for years with the GUI. You learn a few commands because they are fast, honest, and copy-pasteable when a game wiki says "run this."

Open one from the app menu ("Terminal", "Konsole", "Kitty") or with a shortcut — often `Ctrl+Alt+T` or `Super+Enter`.

## The one shortcut that matters

**Ctrl+C copies on Windows. In a Linux terminal it cancels the running command.**

Copy with **Ctrl+Shift+C**. Paste with **Ctrl+Shift+V**.

This is not Linux being difficult. Unix used Ctrl+C for "interrupt" long before Windows used it for copy. Both meanings still exist; Shift is how they share a keyboard.

## A tiny map

You are always *in a folder*. The prompt often shows it.

```bash
pwd          # where am I?
ls           # what is here?
ls -la       # include hidden files (the ones starting with a dot)
cd Downloads # go there
cd ..        # up one folder
cd           # back home
```

Tab completes names. Up-arrow replays the last command. Those two habits cut typing in half.

## Reading a command before you run it

```bash
sudo pacman -S steam
```

Pieces:

- `sudo` — do this as admin, once
- `pacman` — the package program (apt/dnf on other distros)
- `-S` — install
- `steam` — the package name

If a blog says `curl https://example.com/script.sh | bash`, that is "download and run whatever this is." Treat it like an unknown Setup.exe from a pop-up.

## Safe vs loud

Safe to try:

- `ls`, `pwd`, `whoami`, `uname -a`, `ip addr`, `fastfetch` / `neofetch`

Loud (they change the system):

- anything starting with `sudo`
- `rm` (delete, no Recycle Bin)
- `mkfs`, `dd`, `fdisk` (disks)

Ludo will show commands. It will not run the loud ones for you.

## Prompts and shells

`bash` is the default on many distros. `zsh` (and fish) are popular upgrades. They all run the same basic commands. Fancy rainbow prompts are optional cosmetics.

If you see `$` you are a normal user. If you see `#` you are root. You almost never want to *stay* root.

## If you remember one thing

The terminal is a conversation with the machine. You can close the window at any time. Nothing is "in" the terminal except the commands you send.
