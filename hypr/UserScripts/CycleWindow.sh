#!/usr/bin/env bash

# Cycle to the next window, handling fullscreen state.
# If the active window is fullscreen, exit fullscreen first,
# cycle to the next window, then fullscreen the new window.

FULLSCREEN=$(hyprctl activewindow -j | jq -r '.fullscreen')

if [ "$FULLSCREEN" != "0" ] && [ "$FULLSCREEN" != "false" ]; then
    hyprctl keyword animations:enabled false
    hyprctl --batch "\
        dispatch fullscreen $FULLSCREEN; \
        dispatch cyclenext; \
        dispatch fullscreen $FULLSCREEN; \
        dispatch bringactivetotop"
    hyprctl keyword animations:enabled true
else
    hyprctl dispatch cyclenext
    hyprctl dispatch bringactivetotop
fi
