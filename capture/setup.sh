#!/bin/bash
# setup.sh bloodgulch|b30 : load a map and strip it for filming (no HUD, gun, AI, corpses or player body).
# Needs run.sh up, Chimera installed and rig.lua in its global scripts folder (see README).
cd "$(dirname "$0")"
./con.sh "chimera_devmode true" "chimera_show_fps false" "chimera_lua_reload_scripts" "map_name $1" sleep:30
# b30 opens on a cutscene; skip past it before taking control
[ "$1" = b30 ] && sleep 120
./con.sh "show_hud 0" "cheat_deathless_player 1" "camera_control 1" "ai_erase_all" "garbage_collect_now" \
         "object_set_scale (list_get (players) 0) 0.01 0"
