# Installing software (no Setup.exe)

On Windows you download an installer, click Next, and hope the Uninstall entry works later. On Linux the default is inverted: software comes from a **repository** (a signed store), updates with the OS, and uninstalls cleanly.

## The three good ways

1. **Distro packages** — `pacman`, `apt`, `dnf`, Discover, GNOME Software. Fast, native, integrated.
2. **Flatpak (Flathub)** — sandboxed apps that look the same on Fedora, Arch, and Mint. Excellent for Discord, Heroic, Bottles, browsers.
3. **AppImage** — a self-contained file you mark executable. No install, slightly messier updates.

There is also **Snap** (Ubuntu) and **Homebrew**. Fine if your distro leans that way. You do not need all of them.

## What about .exe files?

A Windows installer is not a Linux app. Options:

- Prefer a native Linux build (Steam, Discord, Chrome, Firefox, VS Code)
- Use Proton inside Steam for games
- Use Bottles / Lutris / Wine for the stubborn Windows-only utility
- Use a VM or keep a Windows partition for the tax-software-and-bank-dongle tier

## Finding the right name

Package names are short and lowercase: `steam`, `gimp`, `kdenlive`. The GUI store searches by human names. The terminal wants the package name.

Updates are one action:

- Arch family: `sudo pacman -Syu`
- Debian/Ubuntu: `sudo apt update && sudo apt upgrade`
- Fedora: `sudo dnf upgrade`

That command is Windows Update + "update all my installed programs" in one shot.

## Flatpak in one minute

```bash
flatpak install flathub com.discordapp.Discord
flatpak update
```

Flatpaks can look "behind" on GPU features if the runtime is stale — `flatpak update` fixes that. Steam as a Flatpak works; native Steam also works. Pick one and stick with it so you do not grow two libraries by accident.

## Permissions and "this AppImage does nothing when I double-click"

The file is missing the executable bit:

```bash
chmod +x Something.AppImage
```

Then double-click, or run it from a terminal to see the error.

## If you remember one thing

Stop collecting installers on the Desktop. Ask the store first. The store is not a toy — it is how the system is meant to be fed.
