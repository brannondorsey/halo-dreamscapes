#!/bin/bash
# The shot list used for the bundled examples. Run with the rig loaded (see README):
#   ./shots.sh bloodgulch   after `map_name bloodgulch` + Backspace (free cam)
#   ./shots.sh b30          after `map_name b30`, the intro, `camera_control 1`
# Keyframes: {seconds, cam x,y,z, look-at x,y,z, fov_deg}
cd "$(dirname "$0")"
case $1 in
bloodgulch)
./cap.sh bg_low_static 25 '{ keys = { {0, 98,-150,6, 60,-110,3, 70} } }'
./cap.sh bg_ring_static 25 '{ keys = { {0, 70,-118,1.5, 20,-120,40, 75} } }'
./cap.sh bg_moon_static 25 '{ keys = { {0, 45,-95,3, 95,-160,12, 70} } }'
./cap.sh bg_base_static 25 '{ keys = { {0, 100,-170,3, 96,-150,3, 60} } }'
./cap.sh bg_ridge_static 25 '{ keys = { {0, 55,-150,8, 80,-100,5, 70} } }'
./cap.sh bg_flythrough 30 '{ ease = false, keys = { {0, 104,-178,9, 96,-160,6, 72}, {1, 104,-178,9, 96,-160,6, 72}, {7, 93,-152,8, 82,-136,6, 72}, {13, 80,-130,8, 68,-115,6, 72}, {19, 66,-112,9, 54,-98,7, 72}, {25, 52,-96,10, 40,-82,8, 72}, {30, 44,-86,12, 30,-70,9, 72} } }'
./cap.sh bg_tilt_to_ring 25 '{ ease = true, keys = { {0, 70,-118,2, 30,-118,2, 72}, {2, 70,-118,2, 30,-118,2, 72}, {22, 70,-118,2, 25,-120,45, 72}, {25, 70,-118,2, 25,-120,45, 72} } }'
./cap.sh bg_orbit_base 30 '{ ease = false, keys = (function() local k={} for i=0,30 do local a=-2.2+i*0.045 k[#k+1]={i, 96+28*math.cos(a), -158+28*math.sin(a), 9, 96,-158,3, 66} end return k end)() }'
;;
b30)
./cap.sh sc_sea_static 25 '{ keys = { {0, -120,40,6, -40,40,4, 70} } }'
./cap.sh sc_beach_static 25 '{ keys = { {0, -90,30,4, -40,40,6, 70} } }'
./cap.sh sc_aerial_static 25 '{ keys = { {0, -100,80,15, -40,20,0, 70} } }'
./cap.sh sc_cliff_static 25 '{ keys = { {0, -30,60,3, -90,20,4, 70} } }'
./cap.sh sc_flyin 30 '{ ease = true, keys = { {0, -230,95,14, -50,35,8, 70}, {1, -230,95,14, -50,35,8, 70}, {29, -95,50,5, -40,35,6, 70}, {30, -95,50,5, -40,35,6, 70} } }'
./cap.sh sc_orbit 30 '{ ease = false, keys = (function() local k={} for i=0,30 do local a=1.9+i*0.04 k[#k+1]={i, -50+110*math.cos(a), 30+110*math.sin(a), 22, -50,30,2, 66} end return k end)() }'
./cap.sh sc_waterline_dolly 30 '{ ease = true, keys = { {0, -112,15,3, -50,40,6, 68}, {30, -112,75,3, -50,40,6, 68} } }'
;;
*) echo "usage: $0 bloodgulch|b30"; exit 1;;
esac
