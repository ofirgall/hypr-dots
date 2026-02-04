#!/usr/bin/env sh

set -e -x

sudo echo "hey"

hyprpm purge-cache
hyprpm update
hyprpm -v add https://github.com/ofirgall/hyprland-virtual-desktops
hyprpm enable virtual-desktops

hyprpm reload -n # Reload the plugins
