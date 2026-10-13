#!/bin/bash
# con.sh "cmd1" "cmd2" ... : type commands into Halo's console (opened with the ` key)
# The console's state is checked from screenshots (console.py) before typing and after closing: a
# dropped ` press during a heavy load once left it open, which pauses the game.
HALO_DIR=${HALO_DIR:-$HOME/halo-trial}
export DISPLAY=:99
cd "$(dirname "$0")"
snap() { ffmpeg -hide_banner -loglevel error -y -f x11grab -video_size 640x480 -i :99+80,60 -frames:v 1 $HALO_DIR/now.png; }
grave() { xdotool keydown grave; sleep 0.1; xdotool keyup grave; sleep 0.6; }
if [ -z "$NOOPEN" ]; then
  for try in 1 2 3; do snap; python3 console.py $HALO_DIR/now.png && break; grave; done
fi
for c in "$@"; do
  case $c in sleep:*) sleep "${c#sleep:}"; continue;; esac
  xdotool type --delay 40 "$c"; sleep 0.2
  xdotool keydown Return; sleep 0.1; xdotool keyup Return; sleep 0.8
done
for try in 1 2 3 4; do snap; python3 console.py $HALO_DIR/now.png || exit 0; grave; done
echo "con.sh: console still open after 4 tries" >&2; exit 1
