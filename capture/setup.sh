#!/bin/bash
# setup.sh <map> : load a map and strip it for filming (no HUD, gun, AI, corpses or player body).
# Needs run.sh up, Chimera installed and rig.lua in its global scripts folder (see README).
# Strip mode and the load wait come from maps/<map>/map.json. Strip mode deletes vehicles, weapons and any
# other bipeds continuously (buildings, scenery and lights stay). STRIP=0/1 overrides.
cd "$(dirname "$0")"
HALO_DIR=${HALO_DIR:-$HOME/halo-trial}
G="Halo Trial"; [ -f "$HALO_DIR/game/haloce.exe" ] && G="Halo CE"
D="$HALO_DIR/prefix/drive_c/users/${USER:-root}/Documents/My Games/$G/chimera/lua/data/global/rig"
mkdir -p "$D"
STRIP=${STRIP:-$(python3 ../maps.py "$1" get strip)} && WAIT=$(python3 ../maps.py "$1" get load_wait) || exit 1
if [ "$STRIP" = 1 ]; then touch "$D/strip"; else rm -f "$D/strip"; fi
# one command per console open: typing several in a row while the game is busy drops keys
con() { for c in "$@"; do ./con.sh "$c"; sleep 1.5; done; }
con "chimera_devmode true" "chimera_show_fps false" "chimera_lua_reload_scripts" "map_name $1"
sleep "$WAIT"   # map load (b30's includes its opening cutscene)
con "show_hud 0" "cheat_deathless_player 1" "camera_control 1" "ai_erase_all" "garbage_collect_now" \
    "object_set_scale (list_get (players) 0) 0.01 0" "chimera_lua_reload_scripts"
sleep 8   # let the console text fade before anything is filmed
