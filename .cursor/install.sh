#!/usr/bin/env bash
# Idempotent dependency installer for the Cursor Cloud Agent VM.
#
# Installed components:
#   - System packages via apt: docker.io, maven, postgresql, postgresql-client,
#     python3.12-venv, plus a few small utilities used by the helper scripts.
#   - Bun (JavaScript runtime / package manager) under ~/.bun.
#   - Backend Python deps via `uv sync` (creates backend/.venv).
#   - Frontend JS deps via `bun install` (workspaces).
#   - Playwright Chromium browser + its system library dependencies, so
#     `bunx playwright test --project=chromium` runs out of the box.
#
# Safe to re-run: every step is a no-op if the required state already exists.

set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

log() { printf '\n[install] %s\n' "$*"; }

# ---------------------------------------------------------------------------
# 1. apt packages
# ---------------------------------------------------------------------------
APT_PACKAGES=(
  ca-certificates
  curl
  unzip
  docker.io
  maven
  postgresql
  postgresql-client
  python3.12-venv
)

missing_apt=()
for pkg in "${APT_PACKAGES[@]}"; do
  if ! dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q '^install ok installed$'; then
    missing_apt+=("$pkg")
  fi
done

if [[ ${#missing_apt[@]} -gt 0 ]]; then
  log "Installing apt packages: ${missing_apt[*]}"
  sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${missing_apt[@]}"
else
  log "All apt packages already installed"
fi

# Make the docker daemon usable without sudo from the agent's shell.
if getent group docker >/dev/null 2>&1; then
  if ! id -nG "$USER" | tr ' ' '\n' | grep -qx docker; then
    log "Adding $USER to docker group"
    sudo usermod -aG docker "$USER"
  fi
fi

# ---------------------------------------------------------------------------
# 2. Bun
# ---------------------------------------------------------------------------
export BUN_INSTALL="${BUN_INSTALL:-$HOME/.bun}"
export PATH="$BUN_INSTALL/bin:$PATH"

if ! command -v bun >/dev/null 2>&1; then
  log "Installing Bun into $BUN_INSTALL"
  curl -fsSL https://bun.sh/install | bash
else
  log "Bun already installed: $(bun --version)"
fi

# Ensure the agent's interactive shells pick Bun up on PATH.
BUN_PROFILE_LINE='export BUN_INSTALL="$HOME/.bun"; export PATH="$BUN_INSTALL/bin:$PATH"'
for rc in "$HOME/.bashrc" "$HOME/.profile"; do
  if [[ -f "$rc" ]] && ! grep -qF "$BUN_PROFILE_LINE" "$rc"; then
    printf '\n# Added by .cursor/install.sh\n%s\n' "$BUN_PROFILE_LINE" >> "$rc"
  fi
done

# ---------------------------------------------------------------------------
# 3. Frontend JS deps (workspaces) + Playwright Chromium with system deps
# ---------------------------------------------------------------------------
log "Installing JS workspace deps with bun"
bun install --frozen-lockfile

log "Installing Playwright Chromium browser + system deps"
# `--with-deps chromium` installs both the Chromium browser binary and the
# required Linux system libraries (libnss3, libatk-bridge, etc.). It uses
# sudo internally for the apt step.
( cd frontend && bunx --bun playwright install --with-deps chromium )

# ---------------------------------------------------------------------------
# 4. uv (Python package manager) + backend Python deps
# ---------------------------------------------------------------------------
export PATH="$HOME/.local/bin:$PATH"

if ! command -v uv >/dev/null 2>&1; then
  log "Installing uv into ~/.local/bin"
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

UV_PROFILE_LINE='export PATH="$HOME/.local/bin:$PATH"'
for rc in "$HOME/.bashrc" "$HOME/.profile"; do
  if [[ -f "$rc" ]] && ! grep -qF "$UV_PROFILE_LINE" "$rc"; then
    printf '\n# Added by .cursor/install.sh\n%s\n' "$UV_PROFILE_LINE" >> "$rc"
  fi
done

log "Syncing backend Python deps via uv"
( cd backend && uv sync )

log "Done."
