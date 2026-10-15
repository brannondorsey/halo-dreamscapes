#!/bin/bash
# start a virtual X display and Halo (trial or Custom Edition) under wine
# The lockstep shim (capture/lockstep) is preloaded into the game so cap.sh can film at an even frame
# rate; it runs on real time until a capture is armed. LOCKSTEP=0 starts the game without it.
HALO_DIR=${HALO_DIR:-$HOME/halo-trial}
LS="$(cd "$(dirname "$0")" && pwd)/lockstep"
export DISPLAY=:99 WINEPREFIX=$HALO_DIR/prefix WINEDEBUG=-all WINEARCH=win32
# a container restart leaves a stale display lock that stops a new Xvfb :99 from starting
pgrep -f "Xvfb :99" >/dev/null || { rm -f /tmp/.X99-lock /tmp/.X11-unix/X99; (Xvfb :99 -screen 0 800x600x24 +extension GLX >/dev/null 2>&1 &); }
sleep 2
cd $HALO_DIR/game
EXE=halo.exe; [ -f haloce.exe ] && EXE=haloce.exe
if [ "${LOCKSTEP:-1}" != 0 ]; then
  [ -f "$LS/out/lib/i386-linux-gnu/liblockstep.so" ] || "$LS/build.sh" || exit 1
  # CSMT presents on a separate thread; the shim needs the swap on the game's render thread
  wine reg add 'HKCU\Software\Wine\Direct3D' /v csmt /t REG_DWORD /d 0 /f >/dev/null 2>&1
  export LD_PRELOAD="$LS/out/\$LIB/liblockstep.so" LOCKSTEP_PROC=$EXE LOCKSTEP_FPS=${LOCKSTEP_FPS:-30}
fi
exec wine $EXE -novideo -window -vidmode 800,600,60 "$@"
