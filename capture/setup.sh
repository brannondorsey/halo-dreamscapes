#!/bin/bash
# setup.sh <map> : load a map and strip it for filming (no HUD, gun, AI, corpses or player body).
# Needs run.sh up, Chimera installed and rig.lua in its global scripts folder (see README).
# Every map except the two original trial cuts also gets the rig's strip mode: vehicles, weapons
# and any other bipeds are deleted continuously (buildings, scenery and lights stay). STRIP=0/1 overrides.
cd "$(dirname "$0")"
HALO_DIR=${HALO_DIR:-$HOME/halo-trial}
G="Halo Trial"; [ -f "$HALO_DIR/game/haloce.exe" ] && G="Halo CE"
D="$HALO_DIR/prefix/drive_c/users/${USER:-root}/Documents/My Games/$G/chimera/lua/data/global/rig"
mkdir -p "$D"
case $1 in bloodgulch|b30) STRIP=${STRIP:-0};; *) STRIP=${STRIP:-1};; esac
if [ "$STRIP" = 1 ]; then touch "$D/strip"; else rm -f "$D/strip"; fi
./con.sh "chimera_devmode true" "chimera_show_fps false" "chimera_lua_reload_scripts" "map_name $1" sleep:30
# b30 opens on a cutscene; skip past it before taking control
[ "$1" = b30 ] && sleep 120
./con.sh "show_hud 0" "cheat_deathless_player 1" "camera_control 1" "ai_erase_all" "garbage_collect_now" \
         "object_set_scale (list_get (players) 0) 0.01 0"
