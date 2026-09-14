# The rest of the gaming stack

Steam + Proton is enough for a surprising number of people. The rest is optional equipment. Steal what you need.

## Other stores

- **Heroic** — Epic, GOG, Amazon. Uses Proton/Wine under the hood. Flatpak is the easy install.
- **Lutris** — community install scripts for Battle.net, EA, Ubisoft, itch, older Windows clients. Power-user shaped.
- **Bottles** — "this one Windows app in a box" for utilities and launchers you do not want polluting the rest of the system.

You do not need all three. Heroic + Steam covers most libraries.

## Overlays and performance

**MangoHud** is MSI Afterburner / RTSS for Linux: FPS, frametimes, temps, GPU load. Enable it with a launch option (`mangohud %command%`) or a per-game toggle.

**GameMode** asks the CPU governor and a few kernel knobs to take the game seriously. `gamemoderun %command%`. Harmless, sometimes helpful.

**gamescope** is Steam Deck's compositor. On a desktop it gives you:

- Forced resolution and upscaling
- HDR tricks on supported setups
- A nested session when a game fights your desktop compositor

It is a power tool. If a game already runs well, skip it.

## Proton extras

- **ProtonUp-Qt / ProtonPlus** — install Proton-GE without archaeology
- **WineTricks / Protontricks** — install a specific Windows DLL into one prefix when ProtonDB says "needs vcrun2019"
- **Steamtinkerlaunch** — if you enjoy menus more than launch options

A **prefix** is "this game's fake Windows C: drive." It lives under `steamapps/compatdata/<id>/`. Deleting it is the Linux version of "verify integrity, but meaner" — the game will rebuild it.

## Input, HDR, recording

Steam Input works. Many Xbox and DualSense pads just work. For capture, **OBS** has a native Linux build; on Wayland you want a current version.

## If you remember one thing

Install new tools to solve a named problem ("I need Epic", "I want an FPS counter"). Do not install the entire stack because a rice screenshot included it.
