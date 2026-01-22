#!/usr/bin/env sh

CONFIG_LOC="$HOME/.config/hypr/UserConfigs/VirtualDesktopsNames.conf"

cat <<EOF > $CONFIG_LOC
plugin {
    virtual-desktops {
        names = 1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7, 8:8, 9:9, 10:10
    }
}
EOF
