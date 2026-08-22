#!/usr/bin/env bash
# ==============================================================================
# Z-Truyen X3 — Realtime Hotspot & Connection Monitor for Android Termux
# ==============================================================================
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$DIR")"

if [ -d "$HOME/.ztruyen-venv" ]; then
    source "$HOME/.ztruyen-venv/bin/activate"
fi

python3 "$DIR/monitor_hotspot.py"
