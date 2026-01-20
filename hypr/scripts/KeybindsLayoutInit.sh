#!/usr/bin/env bash
# /* ---- 💫 https://github.com/JaKooLit 💫 ---- */  ##
# Initialize J/K keybinds so they always cycle windows globally (no layout-specific behavior)
# This avoids double-actions when layouts change.

set -euo pipefail

# Always reset and bind SUPER+J/K the same way on startup
hyprctl keyword unbind SUPER,bracketright || true
hyprctl keyword unbind SUPER,bracketleft || true

# Cycle windows globally: J = next, K = previous
hyprctl keyword bind SUPER,bracketright,cyclenext
hyprctl keyword bind SUPER,bracketleft,cyclenext,prev
