#!/bin/bash
# cap.sh name seconds '<lua shot table>' : set the rig's shot and record it to caps/name.mp4
# With the lockstep shim in the game (run.sh's default), the capture is exactly seconds x 30 frames,
# each a real render 1/30 s of game time apart, however slowly the game draws: no held frames, no judder.
# Filming then takes longer than real time. Without the shim (LOCKSTEP=0 in run.sh, or CAPTURE=x11grab)
# it falls back to grabbing the screen in real time, which holds frames whenever the game drops below 30 fps.
set -e
HALO_DIR=${HALO_DIR:-$HOME/halo-trial}
# one capture at a time: two runners would fight over the rig and splice each other's shots
exec 9>"$HALO_DIR/.cap.lock"; flock -n 9 || { echo "cap.sh: another capture is running" >&2; exit 1; }
"$(dirname "$0")/shot.sh" "$3" 0.6
OUT=$HALO_DIR/caps/$1.mp4
ENC=(-c:v libx264 -crf 12 -preset veryfast -pix_fmt yuv420p "$OUT")
GAME=$(pgrep -f 'halo(ce)?\.exe' | head -1 || true)
if [ "${CAPTURE:-lockstep}" = lockstep ] && [ -n "$GAME" ] && tr '\0' '\n' < /proc/$GAME/environ | grep -q '^LD_PRELOAD=.*liblockstep'; then
  CTL=${LOCKSTEP_CTL:-/dev/shm/lockstep.ctl}
  FIFO=$(mktemp -u /dev/shm/cap.XXXXXX); mkfifo "$FIFO"
  rm -f "$CTL.done"
  FRAMES=$(python3 -c "print(round($2 * 30))")
  ffmpeg -hide_banner -loglevel error -y -f rawvideo -pix_fmt rgb24 -s 640x480 -framerate 30 -i "$FIFO" "${ENC[@]}" &
  FF=$!
  echo "$FRAMES $FIFO" > "$CTL.tmp" && mv "$CTL.tmp" "$CTL"   # the shim picks it up at the next present
  # the game must keep presenting (at >= 1 fps); a paused or hung game would otherwise wait forever
  t=0; while kill -0 $FF 2>/dev/null; do
    sleep 1; t=$((t + 1))
    [ $t -gt $((FRAMES + 60)) ] && { kill $FF; rm -f "$FIFO" "$CTL"; echo "cap.sh: game stopped presenting" >&2; exit 1; }
  done
  wait $FF; rm -f "$FIFO"
else
  DISPLAY=:99 ffmpeg -hide_banner -loglevel error -y -f x11grab -framerate 30 -video_size 640x480 -i :99+80,60 \
    -t "$2" "${ENC[@]}"
fi
echo "captured $1"
