#!/bin/bash
# SHEVA AI Factory G10 macOS ARM64 bootstrap, self-contained after archive extraction.
# Installs only reviewed public toolchain + 3 pilot Skills; never imports cloud credentials.
set -euo pipefail

HERE=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [[ ! -f "$HERE/SHA256SUMS.txt" ]]; then
  echo "SHEVA_NO_GO: SHA256SUMS.txt introuvable" >&2
  exit 7
fi
if ! (cd "$HERE" && /usr/bin/shasum -a 256 -c SHA256SUMS.txt >/dev/null); then
  echo "SHEVA_NO_GO: une empreinte interne ne correspond pas" >&2
  exit 8
fi
echo "SHEVA_INTEGRITY_SHA256_PASS"
if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "SHEVA_NO_GO: ce bundle est qualifié uniquement pour macOS Apple Silicon (M1/M2/M3/M4)" >&2
  exit 3
fi

APPLY=0
for arg in "$@"; do [[ "$arg" == "--apply" ]] && APPLY=1; done

echo "SHEVA G10 — préparation machine: $(hostname)"
echo "Archive: $HERE"
echo "Mode: $([[ "$APPLY" == "1" ]] && echo INSTALLATION || echo SIMULATION)"

if [[ "$APPLY" == "1" ]]; then
  if ! command -v xcode-select >/dev/null 2>&1 || ! xcode-select -p >/dev/null 2>&1; then
    echo "SHEVA_HOLD: installer les outils de ligne de commande Apple via 'xcode-select --install', puis relancer." >&2
    exit 4
  fi

  if [[ ! -x /opt/homebrew/bin/brew ]]; then
    echo "Homebrew absent : installation depuis le site officiel (peut demander le mot de passe macOS)."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  fi
  export PATH="/opt/homebrew/bin:$HOME/.local/bin:$PATH"
  if [[ ! -d /Applications/Docker.app ]]; then
    echo "Docker Desktop absent : installation officielle via Homebrew."
    /opt/homebrew/bin/brew install --cask docker-desktop
  fi
else
  export PATH="/opt/homebrew/bin:$HOME/.local/bin:$PATH"
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "SHEVA_HOLD: Python3 indisponible, vérifier les Command Line Tools Apple." >&2
  exit 5
fi

/bin/sh "$HERE/install.sh" "$@"

if [[ "$APPLY" == "1" ]]; then
  echo "SHEVA: installation du socle effectuée. Docker peut demander une validation initiale."
  if [[ -d /Applications/Docker.app ]]; then
    open -a Docker || true
  fi
  echo "ROADMAP: $HERE/sheva-factory roadmap --mission m13"
  echo "FIGO: $HERE/sheva-factory skills install --mission figo"
fi
