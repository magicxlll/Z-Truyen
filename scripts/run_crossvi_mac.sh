#!/usr/bin/env bash
# ==============================================================================
#  Z-Truyen X3 — CrossVi Xteink X3 Desktop Simulator Launcher for macOS
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

exec bash "$ROOT_DIR/run_crossvi_x3.command" "$@"
