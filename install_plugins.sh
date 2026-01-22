#!/usr/bin/env sh

hyprpm update
hyprpm -v add https://github.com/levnikmyskin/hyprland-virtual-desktops?tab=readme-ov-file#Layouts
hyprpm enable virtual-desktops

hyprpm reload -n # Reload the plugins

mkdir ~/.config/waybar/modules
wget -O ~/.config/waybar/modules/libwaybar_vd.so https://github.com/givani30/waybar-vd/releases/latest/download/libwaybar_vd.so
