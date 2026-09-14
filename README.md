# Ludo

Interactive terminal guide for people moving from Windows to Linux — especially if the plan is **Steam, Proton, and a daily driver**, not a weekend experiment.

Ludo does not install packages for you and does not run `sudo`. It explains the new nouns, translates the old habits, and looks at *this* machine so the next step is specific.

```
ludo                 # terminal UI
ludo checkup         # dxdiag, but friendly
ludo translate dir   # Windows command → Linux
ludo glossary "task manager"
```

## Who it is for

You already know how to use a PC. You have a Steam library. You are tired of being told to "just use the terminal" without anyone mapping it onto File Explorer, Task Manager, and Setup.exe.

## What you get

- **First week path** — eight short guides from "you already know this computer" through Steam and GPU drivers
- **Windows → Linux glossary** — Super key, AppData, Recycle Bin, DirectX, the works
- **Command Rosetta stone** — `ipconfig`, `dir`, `taskkill`, `robocopy`…
- **Checkup** — distro, desktop, GPU, Vulkan, Steam, Proton, MangoHud, GameMode
- **Gaming track** — Proton, ProtonDB, Heroic/Lutris, anti-cheat honesty, dual-boot NTFS traps

Progress is saved locally in `~/.local/share/ludo/progress.json`.

## Install

Needs Python 3.11+ on Linux.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
ludo
```

With [uv](https://github.com/astral-sh/uv):

```bash
uv sync --extra dev
uv run ludo
```

## Keyboard (in the UI)

| Key | Where |
| --- | --- |
| `1` / `h` | Home |
| `2` / `w` | First week |
| `3` / `g` | Windows → Linux glossary |
| `4` / `p` | Gaming |
| `5` / `c` | Checkup |
| `6` / `t` | Command translator |
| `n` | Continue the first-week path |
| `?` | Remind me |
| `q` | Quit |

Inside a guide: `Esc` back, `c` mark complete.

## Project layout

```
src/ludo/
  probe.py            system detection
  recommend.py        per-machine next steps
  content/guides/     the lessons
  content/glossary.py Windows ↔ Linux dictionary
  content/commands.py cmd.exe / PowerShell translations
  ui/                 Textual screens
```

Guides are Markdown. Catalog metadata (time, quiz, section) lives in `content/catalog.py`.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Name

*Ludo* is Latin for "I play." It is also a board game about getting from one side to the other with a little help from the dice. That is the idea.
