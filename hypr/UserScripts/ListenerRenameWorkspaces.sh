#!/bin/bash
# ListenerRenameWorkspaces.sh - Listen to Hyprland vdesk events and rename workspaces
# Usage: ./ListenerRenameWorkspaces.sh
# Run in background: ./ListenerRenameWorkspaces.sh &

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RENAME_SCRIPT="$SCRIPT_DIR/RenameWorkspaces.py"
SOCKET="$XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket2.sock"

# Check if socket exists
if [[ ! -S "$SOCKET" ]]; then
    echo "Error: Hyprland socket not found at $SOCKET" >&2
    exit 1
fi

# Check if rename script exists
if [[ ! -f "$RENAME_SCRIPT" ]]; then
    echo "Error: RenameWorkspaces.py not found at $RENAME_SCRIPT" >&2
    exit 1
fi

echo "Listening to Hyprland vdesk events..."
echo "Will execute RenameWorkspaces.py on vdesk events"
echo "Press Ctrl+C to stop"
echo "---"

socat -u UNIX-CONNECT:"$SOCKET" - | while read -r event; do
    case "$event" in
        vdesk\>\>*)
            vdesk="${event#vdesk>>}"
            echo "[vdesk] Event received: $vdesk"
            python3 "$RENAME_SCRIPT"
            ;;
    esac
done
