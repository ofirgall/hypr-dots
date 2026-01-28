#!/usr/bin/env sh

CONFIG_LOC="$HOME/.config/hypr/UserConfigs/VirtualDesktopsNames.conf"

cat <<EOF > $CONFIG_LOC
plugin {
    virtual-desktops {
        names = 1:1, 2:2, 3:3, 4:4, 5:5, 9:9 MUSIC
    }
}
EOF
