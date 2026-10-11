#!/bin/bash
# cap.sh name seconds '<lua shot table>' : set the rig's shot and record it to caps/name.mp4
HALO_DIR=${HALO_DIR:-$HOME/halo-trial}
"$(dirname "$0")/shot.sh" "$3" 0.6
DISPLAY=:99 ffmpeg -hide_banner -loglevel error -y -f x11grab -framerate 30 -video_size 640x480 -i :99+80,60 \
  -t "$2" -c:v libx264 -crf 12 -preset veryfast -pix_fmt yuv420p $HALO_DIR/caps/$1.mp4
echo "captured $1"
