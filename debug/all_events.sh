#!/bin/bash
# AllEvents.sh - Listen to ALL Hyprland events
# Usage: ./all_events.sh
# Run in background: ./all_events.sh &

SOCKET="$XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket2.sock"

# Check if socket exists
if [[ ! -S "$SOCKET" ]]; then
    echo "Error: Hyprland socket not found at $SOCKET" >&2
    exit 1
fi

echo "Listening to ALL Hyprland events..."
echo "Press Ctrl+C to stop"
echo "---"

socat -u UNIX-CONNECT:"$SOCKET" -
