# Danger Canyon (Custom Edition). Daylight, blue sky with cloud banks, the ring and a moon.
# Symmetric about x = 0. A Forerunner facade with a bridge spans the north canyon at y ~30-40;
# its hall is at (0, 10..30, z ~0). The north canyon floor is at z ~-8 (y 35..55); the south
# valley, with a team base, at z ~-4 (y -13..1). Grassy rims at z ~0..6.
# The sky doesn't move, so every still shot drifts. Keep the bases' red/blue emblems and the
# red-floored side corridors out of frame. Void (flat lavender) shows below the horizon to the south.
# map.json "remove" deletes the teleporter pad.
from shotlist import move, arc


def drift(name, cam, look, d=(0, 0, 0), fov=70, secs=75):
    """Near-static shot creeping by vector d over its length."""
    end = tuple(c + dd for c, dd in zip(cam, d))
    return move(name, secs, [(cam, look), (end, look)], fov, ease=True)


FACADE = (0, 25, 0)

SHOTS = [
    # wides: canyon, facade, rims, gullies, sky
    drift("dc_facade_north", (0, 55, 3), (0, 20, 1), d=(1, 0, 0), fov=70),
    drift("dc_rim_east", (30, 40, 6), (-20, 0, 2), d=(0, -0.8, 0), fov=70),
    drift("dc_rim_west", (-30, 40, 6), (20, 0, 2), d=(0, -0.8, 0), fov=70),
    drift("dc_bridge_rim", (8, 53, 2), (25, 30, -5), d=(0.6, 0, 0), fov=70),
    drift("dc_floor_west", (-20, 45, -7), (10, 40, -7), d=(0, -0.8, 0), fov=70),
    drift("dc_floor_east", (20, 45, -7), (-10, 40, -7), d=(0, -0.8, 0), fov=70),
    drift("dc_gully_west", (-28, 36, -6), (-45, 22, -8), d=(0.6, 0, 0.2), fov=70),
    drift("dc_gully_east", (30, 32, -5), (45, 20, -8), d=(-0.6, 0, 0.2), fov=70),
    drift("dc_low_east", (50, 26, -9), (30, 30, -6), d=(0, 0.6, 0), fov=70),
    drift("dc_low_west", (-55, 22, -9), (-30, 30, -6), d=(0, 0.6, 0), fov=70),
    drift("dc_south_pines", (-15, -2, -2), (-30, -9, -3), d=(0, 0.6, 0), fov=70),
    drift("dc_south_west", (-35, 0, 0), (-55, 10, -4), d=(0.6, 0, 0), fov=70),
    drift("dc_south_east", (40, 0, 0), (52, 8, -4), d=(-0.6, 0, 0), fov=70),
    drift("dc_ring_clouds", (30, 40, 6), (-20, 0, 40), d=(0, 0, 0.6), fov=70),

    # close-ups: pines, granite, Forerunner details, moon, planet
    drift("dc_moon_tele", (0, 50, 0), (0, 20, 14), d=(0.3, 0, 0), fov=30),
    drift("dc_ring_tele", (-30, 40, 6), (20, 37, 30), d=(0, 0.3, 0), fov=45),
    drift("dc_pine_trunk", (-22, 31, -4), (-26.2, 29.1, -2), d=(0, 0.3, 0), fov=45),
    drift("dc_boulder", (-20, 33, -4.5), (-24.1, 30.7, -5), d=(0, 0, 0.3), fov=45),
    drift("dc_granite", (10, 41, -6.5), (13.7, 37.5, -7), d=(0.3, 0, 0), fov=45),
    drift("dc_pillar_up", (0, 40, -7), (0, 30, 4), d=(0.3, 0, 0), fov=55),
    drift("dc_cliff_pine", (28, 42, -5), (33.4, 37.4, -2), d=(0, 0, 0.3), fov=50),
    drift("dc_facade_tele", (0, 55, 3), (0, 24, 2), d=(0.3, 0, 0), fov=25),

    # fly-throughs and orbits
    move("dc_fly_facade", 90, [((0, 52, -5), (0, 30, -2)), ((0, 38, -5), (0, 25, -1))], fov=65),
    move("dc_crane_rim", 85, [((-10, 48, -7), FACADE), ((-10, 48, 3), FACADE)], fov=65),
    arc("dc_orbit_facade", 90, 20, 60, 120, 4, look=FACADE, cx=0, cy=30, fov=65),
    move("dc_glide_west", 90, [((-50, 20, -8), (-30, 30, -6)), ((-35, 30, -6), (-15, 40, -7))], fov=65),
    move("dc_rim_walk", 90, [((30, 40, 5), (0, 30, 0)), ((20, 52, 4), (-5, 30, 0))], fov=65),

    # interiors: the Forerunner hall and its tunnel
    drift("dc_hall_controls", (0, 15, 1.5), (0, 22, 1), d=(0, 0.5, 0), fov=80),
    drift("dc_tunnel", (0, 30, 0.5), (0, 20, 0), d=(0, -0.5, 0), fov=80),
    drift("dc_hall_back", (0, 20, 1.5), (0, 12, 1), d=(0, -0.5, 0), fov=55),
    drift("dc_holo", (0, 18, 1), (0, 14.6, -0.2), d=(0.2, 0, 0), fov=50),
    drift("dc_tunnel_out", (0, 22, 0.5), (0, 32, 0.5), d=(0, 0.5, 0), fov=75),
]
