#!/usr/bin/env bash
# Check for uv, the wg command, and the Python packages in pyproject.toml.
# Install anything that is missing.
set -euo pipefail

cd "$(dirname "$0")"

have() { command -v "$1" >/dev/null 2>&1; }

if ! have uv; then
  echo "uv is not installed. Installing it."
  if have brew; then
    brew install uv
  else
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="${HOME}/.local/bin:${PATH}"
  fi
fi

if ! have uv; then
  echo "uv is still not on PATH. Open a new shell and run this script again." >&2
  exit 1
fi

if ! have wg; then
  echo "wg is not installed. Installing WireGuard tools."
  case "$(uname -s)" in
    Darwin)
      brew install wireguard-tools
      ;;
    Linux)
      if have apt-get; then
        sudo apt-get update
        sudo apt-get install -y wireguard openresolv
      else
        echo "Install wireguard-tools so the wg command is on PATH, then run this script again." >&2
        exit 1
      fi
      ;;
    *)
      echo "Install WireGuard so the wg command is on PATH, then run this script again." >&2
      exit 1
      ;;
  esac
fi

uv --version
wg --version
uv sync
echo "Python dependencies are installed."
