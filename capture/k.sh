#!/bin/bash
# k.sh key [key...] : press keys into the Halo window with real XTest events; "sN" sleeps N seconds
HALO_DIR=${HALO_DIR:-$HOME/halo-trial}
export DISPLAY=:99
for k in "$@"; do
  case $k in s*) sleep "${k#s}";; *) xdotool keydown "$k"; sleep 0.12; xdotool keyup "$k"; sleep 0.5;; esac
done
ffmpeg -hide_banner -loglevel error -y -f x11grab -video_size 640x480 -i :99+80,60 -frames:v 1 $HALO_DIR/now.png
