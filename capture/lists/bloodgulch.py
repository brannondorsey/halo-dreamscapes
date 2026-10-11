# Blood Gulch. Flag rooms: blue (95.7,-159.5), red (40.2,-79.1); roofs ~z 0.6, interiors floor ~z -1.
# Nothing in the map moves on its own, so "static" shots drift very slowly (~0.1 m/s).
from shotlist import static, move, arc

BLUE, RED = (96, -158, 3), (40, -80, 3)


def drift(name, cam, look, d=(0, 0, 0), fov=70, secs=75):
    """Near-static shot creeping by vector d over its length."""
    end = tuple(c + dd for c, dd in zip(cam, d))
    return move(name, secs, [(cam, look), (end, look)], fov, ease=True)


SHOTS = [
    # bases, close and mid
    drift("bg_blue_low", (100, -172, 2.5), (96, -156, 4), d=(3, 0, 0), fov=60),
    drift("bg_blue_roof", (98, -161, 2.4), (60, -110, 3), d=(0, 2, 0)),
    drift("bg_red_low", (30, -66, 2.5), (40, -82, 4), d=(-3, 0, 0), fov=60),
    drift("bg_red_roof", (38.6, -79.6, 2.4), (80, -130, 3), d=(0, -2, 0)),
    static("bg_blue_tele", (60, -110, 3), (96, -158, 4), fov=25),
    static("bg_red_tele", (90, -150, 3), (40, -80, 4), fov=25),
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
    arc("bg_orbit_blue", 90, 30, 100, 160, 9, look=(96, -158, 3), cx=96, cy=-158, fov=66),
    arc("bg_orbit_red", 90, 30, -85, -40, 9, look=(40, -80, 3), cx=40, cy=-80, fov=66),
    move("bg_crane_gulch", 85, [((70, -122, 2), (50, -95, 3)), ((70, -122, 15), (50, -95, 0))]),
    move("bg_pan_to_ring", 80, [((70, -118, 2), (30, -118, 2)), ((70, -118, 2), (25, -120, 45))], fov=72),
    move("bg_high_drift", 90, [((65, -150, 16), (70, -110, 0)), ((92, -132, 17), (60, -110, 0))]),
    move("bg_skim_grass", 90, [((90, -160, 1.4), (40, -80, 3)), ((76, -139, 3.4), (40, -80, 3)),
                                ((62, -118, 2.6), (40, -80, 3))], fov=60),

    # interiors: flag rooms and corridors (red base mirrors blue through the map centre)
    drift("bg_blue_flagroom", (94, -159, 0.5), (104, -162, 0.3), d=(1.5, -0.4, 0), fov=80),
    drift("bg_blue_corridor", (96, -157, 0.5), (106, -160, 0.5), d=(1.5, -0.4, 0), fov=80),
    drift("bg_blue_flag_low", (94, -159, 0.0), (104, -162, 0.6), d=(0.8, -0.2, 0), fov=85),
    drift("bg_red_flagroom", (41.9, -79.6, 0.5), (31.9, -76.6, 0.3), d=(-1.5, 0.4, 0), fov=80),
    drift("bg_red_flag_low", (41.9, -79.6, 0.0), (31.9, -76.6, 0.6), d=(-0.8, 0.2, 0), fov=85),
    drift("bg_red_corridor", (39.9, -81.6, 0.5), (29.9, -78.6, 0.5), d=(-1.5, 0.4, 0), fov=80),
    # roof close-ups
    static("bg_blue_hatch", (97.3, -161, 2.3), (89, -155, 1.0), fov=70),
    static("bg_red_hatch", (38.6, -79.6, 2.3), (46.9, -85.6, 1.0), fov=70),
    drift("bg_blue_banshee", (97.3, -161, 2.6), (107, -161, 2.6), d=(0, 1.5, 0), fov=70),
]
