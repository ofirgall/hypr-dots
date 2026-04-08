#!/usr/bin/env bash

# Cycle to the next window.
# If the active window is in a group (monocle mode), use changegroupactive.
# Otherwise, use cyclenext.
# TODO: When upgrading Hyprland to a version with built-in monocle layout,
# replace the group check with a layout check and use `layoutmsg cyclenext`.

GROUPED=$(hyprctl activewindow -j | jq -r '.grouped | length')

if [ "$GROUPED" -gt 1 ]; then
    hyprctl dispatch changegroupactive f
else
    hyprctl dispatch cyclenext
    hyprctl dispatch bringactivetotop
fi
