#!/usr/bin/env sh

set -e -x

sudo echo "hey"


cd waybar-vd && ./build.sh

# upstream: wget -O ~/.config/waybar/modules/libwaybar_vd.so https://github.com/givani30/waybar-vd/releases/latest/download/libwaybar_vd.so

hyprpm purge-cache
hyprpm update
hyprpm -v add https://github.com/ofirgall/hyprland-virtual-desktops
hyprpm enable virtual-desktops

hyprpm reload -n # Reload the plugins
