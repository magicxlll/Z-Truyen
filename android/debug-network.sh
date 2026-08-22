#!/usr/bin/env bash
# ==============================================================================
# Z-Truyen X3 — Script Chẩn Đoán Mạng & Hotspot Cho Android Termux
# ==============================================================================
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$DIR")"

# Kích hoạt môi trường ảo Python nếu có
if [ -d "$HOME/.ztruyen-venv" ]; then
    source "$HOME/.ztruyen-venv/bin/activate"
fi

python3 "$DIR/debug_network.py"
