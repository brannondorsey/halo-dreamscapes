#!/bin/bash
# setup.sh <map> : load a map and strip it for filming (no HUD, gun, AI, corpses or player body).
# Needs run.sh up and Chimera installed; installs capture/rig.lua as Chimera's global script.
# Strip mode and the load wait come from maps/<map>/map.json. Strip mode deletes vehicles, weapons and any
# other bipeds continuously (buildings, scenery and lights stay); "hide" moves vehicles out of view
# instead, for campaign levels whose scripts crash when they're deleted. STRIP=0/1/hide overrides.
# map.json "remove" adds scenery to delete by tag path (e.g. Timberland's CTF beacons).
cd "$(dirname "$0")"
HALO_DIR=${HALO_DIR:-$HOME/halo-trial}
G="Halo Trial"; [ -f "$HALO_DIR/game/haloce.exe" ] && G="Halo CE"
D="$HALO_DIR/prefix/drive_c/users/${USER:-root}/Documents/My Games/$G/chimera/lua/data/global/rig"
mkdir -p "$D" "$D/../../../scripts/global"
cp rig.lua "$D/../../../scripts/global/rig.lua"   # always the repo's rig: stale copies lack strip mode
STRIP=${STRIP:-$(python3 ../maps.py "$1" get strip)} && WAIT=$(python3 ../maps.py "$1" get load_wait) &&
  REMOVE=$(python3 ../maps.py "$1" get remove) || exit 1
rm -f "$D/strip"   # off until the map has loaded: stripping mid-cutscene breaks b30's intro
# one command per console open: typing several in a row while the game is busy drops keys
con() { for c in "$@"; do ./con.sh "$c"; sleep 1.5; done; }
con "chimera_devmode true" "chimera_show_fps false" "chimera_lua_reload_scripts" "map_name $1"
sleep "$WAIT"   # map load (b30's includes its opening cutscene)
con "show_hud 0" "cheat_deathless_player 1" "camera_control 1" "ai_erase_all" "garbage_collect_now" \
    "object_set_scale (list_get (players) 0) 0.01 0" "chimera_lua_reload_scripts"
case $STRIP in 1) : > "$D/strip";; hide) echo hide > "$D/strip";; esac
# map.json "remove": scenery whose tag path contains a fragment goes too (strip file: "remove <fragment>" lines)
[ -f "$D/strip" ] && [ -n "$REMOVE" ] && { [ -s "$D/strip" ] || echo > "$D/strip"; printf 'remove %s\n' $REMOVE >> "$D/strip"; }
sleep 8   # let the console text fade (and strip mode clear the map) before anything is filmed
