#!/usr/bin/env bash
# Play a loop forever, fullscreen, no OSD. Restarts the player if it ever dies.
#   ./play.sh loop.mp4 [more.mp4 ...]
set -u
[ $# -ge 1 ] || { echo "usage: $0 loop.mp4 [...]"; exit 1; }
while true; do
  if command -v mpv >/dev/null; then
    mpv --fs --no-osc --osd-level=0 --loop-playlist=inf --shuffle --no-terminal \
        --keepaspect=yes --hwdec=auto "$@"
  elif command -v cvlc >/dev/null; then
    cvlc --fullscreen --loop --random --no-video-title-show "$@"
  else
    ffplay -fs -loop 0 -autoexit -hide_banner "$1"
  fi
  sleep 1
done
