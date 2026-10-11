#!/bin/bash
# start a virtual X display and Halo trial under wine
HALO_DIR=${HALO_DIR:-$HOME/halo-trial}
export DISPLAY=:99 WINEPREFIX=$HALO_DIR/prefix WINEDEBUG=-all WINEARCH=win32
pgrep -f "Xvfb :99" >/dev/null || (Xvfb :99 -screen 0 800x600x24 +extension GLX >/dev/null 2>&1 &)
sleep 2
cd $HALO_DIR/game
exec wine halo.exe -novideo -window -vidmode 800,600,60 "$@"
