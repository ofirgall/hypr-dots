#!/usr/bin/env sh

set -e -x

NO_WAYBAR=false

while [ $# -gt 0 ]; do
	case "$1" in
		--no-waybar) NO_WAYBAR=true ;;
	esac
	shift
done

sudo echo "hey"

if [ "$NO_WAYBAR" = false ]; then
	cd waybar-vd && ./build.sh
fi

# upstream: wget -O ~/.config/waybar/modules/libwaybar_vd.so https://github.com/givani30/waybar-vd/releases/latest/download/libwaybar_vd.so

hyprpm purge-cache
hyprpm update

hyprpm -v add https://github.com/ofirgall/hyprland-virtual-desktops
hyprpm enable virtual-desktops

hyprpm -v add https://github.com/ofirgall/hyprland-monocle
hyprpm enable monocle

hyprpm reload -n # Reload the plugins
