#!/usr/bin/env bash
# Counts actual windows on the active workspace of the focused monitor,
# including windows inside groups (which hyprland/windowcount now counts as 1).

trap 'pkill -P $$ 2>/dev/null' EXIT TERM INT

get_count() {
    active_ws=$(hyprctl activeworkspace -j | jq -r '.id')
    count=$(hyprctl clients -j | jq "[.[] | select(.workspace.id == $active_ws and .mapped)] | length")
    if [ "$count" -gt 0 ]; then
        echo "$count"
    else
        echo ""
    fi
}

get_count

socat -U - "UNIX-CONNECT:$XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket2.sock" |
    while IFS= read -r event; do
        case "$event" in
            workspace*|focusedmon*|openwindow*|closewindow*|movewindow*|fullscreen*|activewindow*)
                get_count
                ;;
        esac
    done &
wait
