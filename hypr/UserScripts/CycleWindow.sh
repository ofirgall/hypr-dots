#!/usr/bin/env bash

# Cycle to the next window, handling fullscreen state.
# If the active window is fullscreen, exit fullscreen first,
# cycle to the next window, then fullscreen the new window.

FULLSCREEN=$(hyprctl activewindow -j | jq -r '.fullscreen')

if [ "$FULLSCREEN" != "0" ] && [ "$FULLSCREEN" != "false" ]; then
    hyprctl dispatch fullscreen "$FULLSCREEN"
    hyprctl dispatch cyclenext
    hyprctl dispatch bringactivetotop
    hyprctl dispatch fullscreen "$FULLSCREEN"
else
    hyprctl dispatch cyclenext
    hyprctl dispatch bringactivetotop
fi
