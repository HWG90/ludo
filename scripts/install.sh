#!/usr/bin/env bash
# Install Ludo into ~/.local for the current user. No sudo.
set -euo pipefail

REPO="${LUDO_REPO:-https://github.com/HWG90/ludo.git}"
BIN_DIR="${LUDO_BIN_DIR:-$HOME/.local/bin}"
VENV_DIR="${LUDO_VENV_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/ludo/venv}"

need_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    echo "Ludo needs Python 3.11+. Install python from your distro, then re-run." >&2
    exit 1
  fi
  python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit(f"Python 3.11+ required, found {sys.version.split()[0]}")
PY
}

install_with_pipx() {
  echo "Installing with pipx…"
  pipx install --force "git+${REPO}"
}

install_with_uv() {
  echo "Installing with uv…"
  uv tool install --force "git+${REPO}"
}

install_with_venv() {
  echo "Installing into ${VENV_DIR}…"
  mkdir -p "$BIN_DIR" "$(dirname "$VENV_DIR")"
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install --upgrade pip
  "$VENV_DIR/bin/pip" install "git+${REPO}"
  ln -sf "$VENV_DIR/bin/ludo" "$BIN_DIR/ludo"
}

need_python
mkdir -p "$BIN_DIR"

if command -v pipx >/dev/null 2>&1; then
  install_with_pipx
elif command -v uv >/dev/null 2>&1; then
  install_with_uv
else
  install_with_venv
fi

if ! command -v ludo >/dev/null 2>&1; then
  echo
  echo "ludo is installed, but ${BIN_DIR} is not on PATH."
  echo "Add this to ~/.bashrc or ~/.zshrc:"
  echo "  export PATH=\"${BIN_DIR}:\$PATH\""
fi

echo
echo "Done. Run:  ludo"
echo "First launch will ask before installing a local Qwen model."
