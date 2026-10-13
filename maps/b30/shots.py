# Silent Cartographer island, centred ~(0,0); beach ring r~95, sand z~2.
from shotlist import P, static, move, arc
C = (0, 0, 4)
SHOTS = []
# beach statics looking inland (mid)
for a in (90, 135, 180, 270, 315):
    SHOTS.append(static(f"sc_beach_{a}", P(95, a, 3), C))
# along-shore close-ups: low over the surf, looking down the coastline
for a, d in ((100, 35), (150, 35), (200, -35), (260, 35), (300, -35), (330, 30)):
    SHOTS.append(static(f"sc_surf_{a}", P(104, a, 1.6), P(72, a + d * 0.8, 5), fov=55))
# super close-ups of scenery (replaced the far island statics, owner's request 2026-10-13)
SHOTS.append(static("sc_close_surf_rocks", (50.5, 87.5, 2.2), (40.8, 83.6, 2.4), fov=16))
SHOTS.append(static("sc_close_canopy", (65.1, 65.1, 3.0), (55.2, 55.2, 8.0), fov=19))
SHOTS.append(static("sc_close_structure_moon", (-23.8, 88.9, 3.0), (-20.2, 75.3, 8.0), fov=19))
SHOTS.append(static("sc_close_ring_cliff", (-23.8, -88.9, 3.0), (-20.2, -75.3, 8.0), fov=19))
SHOTS.append(static("sc_close_trees_structure", (65.1, -65.1, 3.0), (55.2, -55.2, 8.0), fov=19))
SHOTS.append(static("sc_close_bridge", (-82.8, -22.2, 5.2), (-75.3, -20.2, 8.0), fov=28))
SHOTS.append(static("sc_close_grove", (87.5, 50.5, 2.2), (77.1, 52.0, 2.4), fov=16))
SHOTS.append(static("sc_close_foam", (93.0, 33.9, 4.0), (89.9, 36.3, 1.6), fov=35))
SHOTS.append(static("sc_close_foam_line", (-63.6, -75.8, 4.0), (-59.7, -76.4, 1.6), fov=35))
SHOTS.append(static("sc_close_ripples", (-75.8, 63.6, 4.0), (-76.4, 59.7, 1.6), fov=35))
# telephoto close-ups from the water
SHOTS.append(static("sc_tele_structure_180", P(130, 180, 4), P(85, 160, 8), fov=28))
SHOTS.append(static("sc_tele_structure_90", P(140, 100, 4), P(90, 80, 10), fov=30))
SHOTS.append(static("sc_tele_cliff_315", P(135, 315, 3), P(80, 330, 12), fov=30))
# pelicans at the landing zone
SHOTS.append(static("sc_pelicans_close", (-80, 60, 3), (-61, 38, 2), fov=50))
SHOTS.append(static("sc_pelicans_water", (-95, 55, 1.5), (-60, 40, 3), fov=40))
SHOTS.append(arc("sc_pelicans_orbit", 90, 28, 110, 170, 4, look=(-61, 38, 2), cx=-61, cy=38, fov=60))
# slow fly-thrus
SHOTS.append(arc("sc_fly_beach_arc_a", 90, 106, 120, 170, 4))
SHOTS.append(arc("sc_fly_beach_arc_b", 90, 106, 250, 300, 4))
SHOTS.append(arc("sc_fly_sea_orbit", 90, 175, 0, 45, 12, look=(0, 0, 6)))
SHOTS.append(arc("sc_fly_sea_orbit_b", 90, 160, 180, 225, 6, look=(0, 0, 6)))
SHOTS.append(move("sc_fly_approach", 90, [((-260, 90, 10), (-50, 30, 5)), ((-120, 50, 5), (-50, 30, 5))]))
SHOTS.append(move("sc_fly_crane_up", 80, [(P(100, 315, 2), C), (P(100, 315, 30), (0, 0, 0))]))
SHOTS.append(move("sc_fly_descend", 90, [(P(220, 60, 60), (0, 0, 0)), (P(125, 60, 6), C)]))
SHOTS.append(move("sc_fly_shore_dolly", 90, [(P(108, 140, 2.5), P(95, 175, 3)), (P(108, 175, 2.5), P(95, 210, 3))]))
SHOTS.append(move("sc_fly_pushin_structure", 90, [(P(170, 180, 6), P(85, 165, 8)), (P(115, 178, 4), P(85, 165, 8))], fov=50))
SHOTS.append(move("sc_fly_seaskim", 90, [(P(220, 250, 2), C), (P(130, 265, 2), C)], fov=60))
