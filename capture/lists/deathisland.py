# Death Island (Custom Edition). Island centre ~(-15, 5); bases: blue ~(25, 16, 8.5) at +x,
# red ~(-21, -7, 10) at -x. Beaches at z ~2.5, clifftops z ~15-25, sea arch at ~(-65, 10).
# Strip mode (setup.sh) removes the ~46 vehicles; trees don't sway, so stills face water or sky.
from shotlist import static, move, arc


def drift(name, cam, look, d=(0, 0, 0), fov=70, secs=75):
    """Near-static shot creeping by vector d over its length."""
    end = tuple(c + dd for c, dd in zip(cam, d))
    return move(name, secs, [(cam, look), (end, look)], fov, ease=True)


SHOTS = [
    # wides: sea, coast, ring (static or drifting)
    drift("di_surf_south", (7.8, -47.8, 4.5), (36.1, -76.1, 3.7), d=(0.8, -0.8, 0), fov=65),
    drift("di_surf_open", (8, -44, 5), (8, -90, 1), d=(0, 0, 0.6), fov=65),
    drift("di_arch_beach", (-41.8, -14.6, 6.3), (-70, 13.7, 5.5), d=(-1.5, 1.5, 0), fov=62),
    drift("di_arch_high", (-33.4, -19.8, 11.8), (-61.7, 8.5, 11), d=(0, 0, 0.8), fov=62),
    drift("di_coast_west", (-68, 16.2, 18.1), (-68, -23.8, 13.6), d=(0, -1.5, 0), fov=68),
    drift("di_coast_bay", (-57.4, 25.4, 20.7), (-57.4, 65.4, 16.2), d=(1.5, 0, 0), fov=68),
    drift("di_coast_moon", (-57.4, 25.4, 20.7), (-57.4, -14.6, 16.2), d=(0, 0, 0.6), fov=68),
    drift("di_ring_cliff", (-68, 16.2, 18.1), (-28, 16.2, 13.6), d=(0, 1.5, 0), fov=68),
    drift("di_cliff_base", (46.9, -34.3, 16.8), (46.9, 5.7, 12.3), d=(-1, 0, 0), fov=68),
    drift("di_cliff_ring", (32, -27.8, 18.8), (-8, -27.8, 14.3), d=(0, 1, 0), fov=68),
    drift("di_grove_ring", (-31.9, -6.9, 26.4), (8.1, -6.9, 21.9), d=(1, 0, 0), fov=68),
    drift("di_grove_moon", (-31.9, -6.9, 26.4), (-31.9, 33.1, 21.9), d=(1, 0, 0), fov=68),
    drift("di_beach_rocks", (-57, 54.1, 5.2), (-85.3, 25.8, 4.4), d=(0, -1, 0), fov=65),
    drift("di_beach_north", (-74.8, 24.4, 4.3), (-46.5, 52.7, 3.5), d=(1, 1, 0), fov=65),

    # close-ups: rock, foam, trees, base details
    static("di_foam_close", (9, -47, 3.4), (20, -56, 1.2), fov=45),
    static("di_rock_beach", (-57, 54.1, 5.2), (-45, 66, 4), fov=35),
    static("di_arch_tele", (-41.8, -14.6, 6.3), (-65.3, 17.8, 6.5), fov=30),
    static("di_tree_trunk", (-19.2, -4, 25), (-6, -4, 22), fov=40),
    static("di_tree_rock", (22.7, 18.9, 24), (-17.3, 18.9, 19.5), fov=45),
    static("di_cave_arch", (44, 7.5, 6.6), (15.7, -20.8, 9), fov=65),
    static("di_platform_under", (44, 7.5, 6.6), (15.7, 35.8, 5.8), fov=50),
    static("di_ring_tele", (8, -44, 5), (-41.7, -49.2, 20), fov=45),
    static("di_moon_tele", (-57.4, 25.4, 20.7), (-49, -14.6, 30), fov=25),

    # fly-throughs and orbits
    move("di_skim_beach", 90, [((-2, -50, 3.8), (30, -55, 3)), ((18, -50, 3.8), (50, -55, 3))], fov=62),
    move("di_toward_arch", 90, [((-41.8, -14.6, 6.3), (-66, 12, 6)), ((-48, -8, 6.3), (-66, 12, 6))], fov=62),
    arc("di_orbit_grove", 90, 18, 200, 290, 29, look=(-19, -4, 24), cx=-19, cy=-4, fov=62),
    move("di_crane_coast", 85, [((-57.4, 25.4, 19), (-57.4, 65.4, 4)), ((-57.4, 25.4, 30), (-57.4, 65.4, 4))], fov=66),
    move("di_pan_ring", 80, [((8, -44, 5), (40, -70, 2)), ((8, -44, 5), (-40, -60, 30))], fov=66),
    move("di_cliff_glide", 90, [((46.9, -34.3, 17), (46.9, 5.7, 12)), ((40, -32, 18), (20, 5, 12)),
                                 ((32, -28, 19), (-8, -27.8, 14))], fov=66),

    # interiors: base corridors and teleporter rooms
    drift("di_blue_corridor", (30, 16, 9), (18, 16, 8), d=(-1.5, 0, 0), fov=75),
    drift("di_blue_tele", (25, 14, 9.5), (25, 24, 8), d=(0, 0.8, 0), fov=75),
    drift("di_red_corridor", (-27, -7, 10.5), (-15, -7, 10), d=(1.5, 0, 0), fov=75),
    drift("di_red_tele", (-21, -9, 10.5), (-21, 3, 10), d=(0, 0.8, 0), fov=75),
    drift("di_cave_stairs", (-33.4, -19.8, 11.8), (-5.1, 8.5, 10), d=(0.5, 0.5, 0), fov=60),
]
