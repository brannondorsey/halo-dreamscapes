# Blood Gulch. Flag rooms: blue (95.7,-159.5), red (40.2,-79.1); roofs ~z 0.6, interiors floor ~z -1.
# Nothing in the map moves on its own, so "static" shots drift very slowly (~0.1 m/s).
from shotlist import static, move, arc

BLUE, RED = (96, -158, 3), (40, -80, 3)


def drift(name, cam, look, d=(0, 0, 0), fov=70, secs=75):
    """Near-static shot creeping by vector d over its length."""
    end = tuple(c + dd for c, dd in zip(cam, d))
    return move(name, secs, [(cam, look), (end, look)], fov, ease=True)


SHOTS = [
    # base roof, looking out over the gulch
    drift("bg_blue_roof", (98, -161, 2.4), (60, -110, 3), d=(0, 2, 0)),
    # gulch, wide and low
    drift("bg_gulch_low", (98, -150, 6), (60, -110, 3), d=(-2, 2, 0)),
    drift("bg_gulch_grass", (75, -135, 1.2), (45, -95, 3), d=(0, 3, 0), fov=55),
    drift("bg_gulch_mid", (68, -119, 2), (96, -158, 6), d=(2, 0, 0)),
    drift("bg_ridge", (55, -150, 8), (80, -100, 5), d=(2, 2, 0)),
    drift("bg_ridge_b", (85, -95, 9), (55, -140, 3), d=(-2, -2, 0)),
    # sky, ring, moon
    drift("bg_ring_up", (70, -118, 1.5), (20, -120, 40), d=(0, 2, 0), fov=75),
    drift("bg_moon", (45, -95, 3), (95, -160, 12), d=(1, -1, 0)),
    static("bg_ring_tele", (70, -118, 2), (25, -122, 60), fov=35),
    # fly-throughs
    move("bg_fly_blue_to_red", 90, [((104, -178, 9), (96, -160, 6)), ((93, -152, 8), (82, -136, 6)),
                                    ((80, -130, 8), (68, -115, 6)), ((66, -112, 9), (54, -98, 7)),
                                    ((52, -96, 10), (40, -82, 8)), ((44, -86, 12), (30, -70, 9))], fov=72),
    move("bg_fly_red_to_blue", 90, [((34, -70, 12), (44, -86, 8)), ((48, -92, 9), (60, -108, 6)),
                                    ((62, -110, 8), (74, -126, 6)), ((78, -132, 8), (90, -148, 6)),
                                    ((94, -150, 10), (100, -168, 6))], fov=72),
    move("bg_crane_gulch", 85, [((70, -122, 2), (50, -95, 3)), ((70, -122, 15), (50, -95, 0))]),
    move("bg_pan_to_ring", 80, [((70, -118, 2), (30, -118, 2)), ((70, -118, 2), (25, -120, 45))], fov=72),
    move("bg_high_drift", 90, [((65, -150, 16), (70, -110, 0)), ((92, -132, 17), (60, -110, 0))]),
    move("bg_skim_grass", 90, [((90, -160, 1.4), (40, -80, 3)), ((76, -139, 3.4), (40, -80, 3)),
                                ((62, -118, 2.6), (40, -80, 3))], fov=60),

    # canyon scenery (replaced most base shots, owner's request 2026-10-13); slow sideways drift
    drift("bg_valley_ring", (79.2, -134.6, 4.0), (24.5, -109.9, 6.0), d=(-0.8, -1.8, 0), fov=58),
    drift("bg_rock_ring", (79.2, -134.6, 4.0), (73.3, -74.9, 6.0), d=(-2.0, -0.2, 0), fov=58),
    drift("bg_cliffs_clouds", (68.0, -119.0, 4.0), (13.3, -94.3, 6.0), d=(-0.8, -1.8, 0), fov=58),
    drift("bg_moon_cliffs", (68.0, -119.0, 4.0), (73.9, -178.7, 6.0), d=(2.0, 0.2, 0), fov=58),
    drift("bg_moon_rock", (56.8, -103.4, 4.0), (62.7, -163.1, 6.0), d=(2.0, 0.2, 0), fov=58),
    drift("bg_rolling_hills", (53.7, -147.0, 7.0), (108.9, -107.4, 9.0), d=(-1.2, 1.6, 0), fov=60),
    drift("bg_canyon_frame", (82.3, -91.0, 7.0), (27.1, -130.6, 9.0), d=(1.2, -1.6, 0), fov=60),
    drift("bg_rock_pillar", (36.9, -123.6, 7.0), (92.1, -84.0, 9.0), d=(-1.2, 1.6, 0), fov=60),
    drift("bg_palm", (75.0, -135.0, 1.2), (52.0, -103.0, 3.0), d=(0.32, 0.24, 0), fov=18),
    drift("bg_peak_cave", (53.7, -147.0, 7.0), (108.9, -107.4, 9.0), d=(-1.2, 1.6, 0), fov=30),

    # interiors: corridors only (no painted flag-room floors, owner's request)
    drift("bg_blue_corridor", (96, -157, 0.5), (106, -160, 0.5), d=(1.5, -0.4, 0), fov=80),
    drift("bg_red_corridor", (39.9, -81.6, 0.5), (29.9, -78.6, 0.5), d=(-1.5, 0.4, 0), fov=80),
]
