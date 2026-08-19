#!/usr/bin/env bash
# ==============================================================================
#  Z-Truyen X3 — CrossVi Xteink X3 Desktop Simulator Shell Launcher for macOS
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/run_crossvi_x3.command" "$@"
