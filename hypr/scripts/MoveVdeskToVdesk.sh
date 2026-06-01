#!/bin/bash
# Move ALL windows of the current vdesk to the target vdesk silently,
# then switch to the target vdesk. ("Take everything with me to desk N.")

TARGET="$1"
[ -z "$TARGET" ] && exit 1

ACTIVE_WS=$(hyprctl activeworkspace -j | jq -r '.id')

# All workspace IDs belonging to the current vdesk (pattern from OpenUrl.sh)
VDESK_WS_IDS=$(hyprctl printstate -j | jq -r \
    --argjson ws "$ACTIVE_WS" \
    '[.[] | select(.workspaces[] == $ws) | .workspaces[]] | unique')

# Addresses of every client on the current vdesk
ADDRS=$(hyprctl clients -j | jq -r \
    --argjson ws_ids "$VDESK_WS_IDS" \
    '.[] | select([.workspace.id] | inside($ws_ids)) | .address')

for addr in $ADDRS; do
    hyprctl dispatch movetodesksilent "$TARGET,address:$addr"
done

hyprctl dispatch vdesk "$TARGET"
