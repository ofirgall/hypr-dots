#!/usr/bin/env bash

# Toggle monocle mode and maximize state together.
# Monocle groups all workspace windows; maximize triggers waybar's fullscreen CSS class.
# TODO: Replace with built-in monocle layout when upgrading Hyprland past 0.53.

hyprctl dispatch monocle:toggle

GROUPED=$(hyprctl activewindow -j | jq -r '.grouped | length')
FULLSCREEN=$(hyprctl activewindow -j | jq -r '.fullscreen')

if [ "$GROUPED" -gt 1 ] && [ "$FULLSCREEN" = "0" ]; then
    hyprctl dispatch fullscreen 1
elif [ "$GROUPED" -le 1 ] && [ "$FULLSCREEN" != "0" ]; then
    hyprctl dispatch fullscreen 1
fi
