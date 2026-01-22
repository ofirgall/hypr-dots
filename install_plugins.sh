#!/usr/bin/env sh

hyprpm update
hyprpm -v add https://github.com/levnikmyskin/hyprland-virtual-desktops?tab=readme-ov-file#Layouts
hyprpm enable virtual-desktops

hyprpm reload -n # Reload the plugins
