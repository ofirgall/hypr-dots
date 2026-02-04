#!/usr/bin/env sh

 sudo apt -y install hyprland-plugin-deps

## Was required for Duckonaut/split-monitor-workspaces
# sudo apt install g++-14 gcc-14
# sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-14 10
# sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-14 10
# sudo update-alternatives --config gcc
# sudo update-alternatives --config g++


hyprpm update
hyprpm -v add https://github.com/ofirgall/hyprland-virtual-desktops
hyprpm enable virtual-desktops

hyprpm reload -n # Reload the plugins

mkdir ~/.config/waybar/modules
wget -O ~/.config/waybar/modules/libwaybar_vd.so https://github.com/givani30/waybar-vd/releases/latest/download/libwaybar_vd.so
