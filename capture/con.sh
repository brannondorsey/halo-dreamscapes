#!/bin/bash
# con.sh "cmd1" "cmd2" ... : type commands into Halo's console (opened with the ` key)
HALO_DIR=${HALO_DIR:-$HOME/halo-trial}
export DISPLAY=:99
[ "$NOOPEN" ] || { xdotool keydown grave; sleep 0.1; xdotool keyup grave; sleep 0.6; }
for c in "$@"; do
  case $c in sleep:*) sleep "${c#sleep:}"; continue;; esac
  xdotool type --delay 40 "$c"; sleep 0.2
  xdotool keydown Return; sleep 0.1; xdotool keyup Return; sleep 0.8
done
ffmpeg -hide_banner -loglevel error -y -f x11grab -video_size 640x480 -i :99+80,60 -frames:v 1 $HALO_DIR/now.png
xdotool keydown grave; sleep 0.1; xdotool keyup grave
