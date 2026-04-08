#!/bin/bash

VAL=$(hyprctl getoption group:groupbar:enabled -j | jq -r ".int")
if [ "$VAL" = "1" ]; then
    hyprctl keyword group:groupbar:enabled false
else
    hyprctl keyword group:groupbar:enabled true
fi

# Force re-render by toggling the active window's group state
sleep 0.05
hyprctl dispatch forcerendererreload
