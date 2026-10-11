#!/bin/bash
# shot.sh '<lua table>' : hand a shot to the in-game camera rig, then screenshot after 2s
HALO_DIR=${HALO_DIR:-$HOME/halo-trial}
G="Halo Trial"; [ -f "$HALO_DIR/game/haloce.exe" ] && G="Halo CE"
D="$HALO_DIR/prefix/drive_c/users/${USER:-root}/Documents/My Games/$G/chimera/lua/data/global/rig"
printf '%s\n' "$1" > "$D/shot.lua"
sleep ${2:-2}
DISPLAY=:99 ffmpeg -hide_banner -loglevel error -y -f x11grab -video_size 640x480 -i :99+80,60 -frames:v 1 $HALO_DIR/now.png
