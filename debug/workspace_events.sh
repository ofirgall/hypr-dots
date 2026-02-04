#!/bin/bash
# WorkspaceEvents.sh - Listen to Hyprland workspace events
# Usage: ./WorkspaceEvents.sh
# Run in background: ./WorkspaceEvents.sh &

SOCKET="$XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket2.sock"

# Check if socket exists
if [[ ! -S "$SOCKET" ]]; then
    echo "Error: Hyprland socket not found at $SOCKET" >&2
    exit 1
fi

echo "Listening to Hyprland workspace events..."
echo "Press Ctrl+C to stop"
echo "---"

socat -u UNIX-CONNECT:"$SOCKET" - | while read -r event; do
    case "$event" in
        workspace\>\>*)
            workspace="${event#workspace>>}"
            echo "[workspace] Switched to: $workspace"
            # Add your custom action here, e.g.:
            # notify-send "Workspace" "Now on: $workspace"
            ;;
        workspacev2\>\>*)
            # Format: workspacev2>>ID,NAME
            data="${event#workspacev2>>}"
            ws_id="${data%%,*}"
            ws_name="${data#*,}"
            echo "[workspacev2] ID: $ws_id, Name: $ws_name"
            ;;
        createworkspace\>\>*)
            workspace="${event#createworkspace>>}"
            echo "[createworkspace] Created: $workspace"
            ;;
        createworkspacev2\>\>*)
            data="${event#createworkspacev2>>}"
            ws_id="${data%%,*}"
            ws_name="${data#*,}"
            echo "[createworkspacev2] Created ID: $ws_id, Name: $ws_name"
            ;;
        destroyworkspace\>\>*)
            workspace="${event#destroyworkspace>>}"
            echo "[destroyworkspace] Destroyed: $workspace"
            ;;
        destroyworkspacev2\>\>*)
            data="${event#destroyworkspacev2>>}"
            ws_id="${data%%,*}"
            ws_name="${data#*,}"
            echo "[destroyworkspacev2] Destroyed ID: $ws_id, Name: $ws_name"
            ;;
        focusedmon\>\>*)
            # Format: focusedmon>>MONNAME,WORKSPACE
            data="${event#focusedmon>>}"
            monitor="${data%%,*}"
            workspace="${data#*,}"
            echo "[focusedmon] Monitor: $monitor, Workspace: $workspace"
            ;;
        moveworkspace\>\>*)
            # Format: moveworkspace>>WORKSPACE,MONNAME
            data="${event#moveworkspace>>}"
            workspace="${data%%,*}"
            monitor="${data#*,}"
            echo "[moveworkspace] Workspace: $workspace moved to Monitor: $monitor"
            ;;
        moveworkspacev2\>\>*)
            # Format: moveworkspacev2>>ID,NAME,MONNAME
            data="${event#moveworkspacev2>>}"
            echo "[moveworkspacev2] $data"
            ;;
        urgent\>\>*)
            address="${event#urgent>>}"
            echo "[urgent] Window requires attention: $address"
            ;;
    esac
done
