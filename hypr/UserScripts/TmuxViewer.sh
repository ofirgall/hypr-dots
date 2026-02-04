#!/usr/bin/env bash

# Get active window info
TITLE=$(hyprctl activewindow -j | jq -r '.title')
SUFFIX=" - TMUX"

# Check if title ends with "- TMUX"
if [[ "$TITLE" == *"$SUFFIX" ]]; then
    # Remove the suffix to get the session name
    SESSION_NAME="${TITLE%$SUFFIX}"

    # Open new terminal with VIEW_TMUX_SESSION env var
    VIEW_TMUX_SESSION="$SESSION_NAME" x-terminal-emulator -t "TMUX VIEWER - $SESSION_NAME" &
else
    notify-send "TmuxViewer" "Active window is not a TMUX session"
fi
