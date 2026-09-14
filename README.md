# Ludo

Interactive terminal guide for people moving from Windows to Linux — especially if the plan is **Steam, Proton, and a daily driver**, not a weekend experiment.

Ludo does not install packages for you and does not run `sudo`. It explains the new nouns, translates the old habits, and looks at *this* machine so the next step is specific.

```
ludo                 # terminal UI
ludo checkup         # dxdiag, but friendly
ludo ask "what is Proton"
ludo translate dir   # Windows command → Linux
ludo glossary "task manager"
```

## Who it is for

You already know how to use a PC. You have a Steam library. You are tired of being told to "just use the terminal" without anyone mapping it onto File Explorer, Task Manager, and Setup.exe.

## What you get

- **Ask bar** — type a question at the bottom (`/` to focus). On first launch Ludo prompts to install Ollama, fetch a small Qwen model, and start it. Gemini is the cloud fallback if you set `GEMINI_API_KEY`.
- **First week path** — eight short guides from "you already know this computer" through Steam and GPU drivers
- **Windows → Linux glossary** — Super key, AppData, Recycle Bin, DirectX, the works
- **Command Rosetta stone** — `ipconfig`, `dir`, `taskkill`, `robocopy`…
- **Checkup** — distro, desktop, GPU, Vulkan, Steam, Proton, MangoHud, GameMode
- **Gaming track** — Proton, ProtonDB, Heroic/Lutris, anti-cheat honesty, dual-boot NTFS traps

Progress is saved in `~/.local/share/ludo/progress.json`. Preferences such as the last theme live in `settings.json` next to it.

## Install

Needs Python 3.11+ on Linux. Pick one:

**One line** (friends, Steam Deck, a fresh CachyOS box):

```bash
curl -fsSL https://raw.githubusercontent.com/HWG90/ludo/master/scripts/install.sh | bash
```

That uses `pipx` or `uv` if you have them, otherwise a venv under `~/.local`. No sudo.

**pipx** (best if you already live in Python tools):

```bash
pipx install git+https://github.com/HWG90/ludo.git
ludo
```

**uv**:

```bash
uv tool install git+https://github.com/HWG90/ludo.git
ludo
```

**From a clone**:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ludo
```

Arch / CachyOS: a starting PKGBUILD is in `packaging/arch/`. PyPI (`pipx install ludo-linux`) is the next publish step once a release is uploaded.

## Keyboard (in the UI)

| Key | Where |
| --- | --- |
| `1` / `h` | Home |
| `2` / `w` | First week |
| `3` / `g` | Windows → Linux glossary |
| `4` / `p` | Gaming |
| `5` / `c` | Checkup |
| `6` / `t` | Command translator |
| `/` | Focus the ask bar |
| `n` | Continue the first-week path |
| `?` | Remind me |
| `q` | Quit |

Inside a guide: `Esc` back, `c` mark complete.

## Chat models

The ask bar always searches Ludo’s guides, glossary, commands, and this PC’s checkup. If a model is available, that material is the prompt — the model does not get a free-roam web.

On first launch Ludo **asks** before touching Ollama: install it for your user (no sudo), download `qwen2.5:1.5b`, and start it so Ask is ready. Choose **Not now** or **Don’t ask again** anytime. After you say yes, later launches start the model in the background.

```bash
# lightweight, ~1 GB. Bigger is LUDO_OLLAMA_MODEL=qwen2.5:7b
ollama pull qwen2.5:1.5b
ludo llm
ludo ask "why is Ctrl+C different in the terminal"
```

**Gemini** (cloud, small/fast Flash-Lite):

```bash
export GEMINI_API_KEY=...
ludo ask --llm gemini "will my Steam games work"
```

Auto order: Ollama if it answers on `localhost:11434`, else Gemini if a key is set, else notes only. Override with `LUDO_LLM=ollama|gemini|off` or `ludo ask --llm`.

## Project layout

```
src/ludo/
  ask.py              question routing (notes + optional model)
  llm.py              Ollama Qwen and Gemini backends
  ollama_setup.py     first-launch install/start/pull prompts
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
