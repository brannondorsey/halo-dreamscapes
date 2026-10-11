#!/bin/bash
# hour.sh : film both shot lists and render the two one-hour bar cuts into cuts/.
# Needs run.sh up with Chimera + rig.lua (README step 1). Re-running skips shots already in $HALO_DIR/caps/.
set -e
cd "$(dirname "$0")"
export HALO_DIR=${HALO_DIR:-$HOME/halo-trial}
mkdir -p cuts
caps() { (cd capture && ./shotlist.py "lists/$1.py" names) | sed "s#.*#$HALO_DIR/caps/&.mp4#"; }
film() { capture/setup.sh "$1" && (cd capture && ./shotlist.py "lists/$1.py" run) && capture/shot.sh ''; }

film b30
./glitch.py $(caps b30) --calm --minutes 60 --seed 30 -o cuts/silent_cartographer_1h.mp4
film bloodgulch
./glitch.py $(caps bloodgulch) --calm --minutes 60 --seed 31 -o cuts/blood_gulch_1h.mp4
