#!/bin/bash
# Opens a URL in a browser window on the active vdesk,
# instead of Chrome's default "last focused window" behavior.

URL="$1"
if [ -z "$URL" ]; then
    URL="https://"
fi

ACTIVE_WS=$(hyprctl activeworkspace -j | jq -r '.id')

# Find all workspace IDs belonging to the same vdesk as the active workspace
VDESK_WS_IDS=$(hyprctl printstate -j | jq -r \
    --argjson ws "$ACTIVE_WS" \
    '[.[] | select(.workspaces[] == $ws) | .workspaces[]] | unique')

# Find a browser window on any workspace in this vdesk
BROWSER_ADDR=$(hyprctl clients -j | jq -r \
    --argjson ws_ids "$VDESK_WS_IDS" \
    '[.[] | select((.tags[] | startswith("browser")) and ([.workspace.id] | inside($ws_ids)))] | first | .address // empty')

if [ -n "$BROWSER_ADDR" ]; then
    hyprctl dispatch focuswindow "address:${BROWSER_ADDR}"
    sleep 0.1
    google-chrome "$URL"
else
    google-chrome --new-window "$URL"
fi
