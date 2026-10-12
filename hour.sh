#!/bin/bash
# hour.sh [map...] : film shot lists and render one-hour bar cuts into cuts/ (default: b30 bloodgulch).
# Needs run.sh up with Chimera + rig.lua (README step 1). Re-running skips shots already in $HALO_DIR/caps/.
# b30/bloodgulch use the trial; Custom Edition maps (deathisland, ...) need HALO_DIR pointing at the CE
# install and the CE game running. Get the shot list's contact sheet approved before filming (SHOT_GUIDE.md).
set -e
cd "$(dirname "$0")"
export HALO_DIR=${HALO_DIR:-$HOME/halo-trial}
mkdir -p cuts
caps() { (cd capture && ./shotlist.py "lists/$1.py" names) | sed "s#.*#$HALO_DIR/caps/&.mp4#"; }
film() { capture/setup.sh "$1" && (cd capture && ./shotlist.py "lists/$1.py" run) && capture/shot.sh ''; }

for map in "${@:-b30 bloodgulch}"; do
  for m in $map; do
    case $m in
      b30)         seed=30 out=silent_cartographer_1h ;;
      bloodgulch)  seed=31 out=blood_gulch_1h ;;
      deathisland) seed=41 out=death_island_1h ;;
      *) echo "no seed/output for $m; add it to hour.sh" >&2; exit 1 ;;
    esac
    film "$m"
    ./glitch.py $(caps "$m") --calm --minutes 60 --seed $seed -o cuts/$out.mp4
  done
done
