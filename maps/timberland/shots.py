# Timberland (Custom Edition). Night-blue sky, the ring and a gas giant overhead; a stream runs
# north-south through the pine valley from the waterfall at (13.4, 50.6, -15) to (-6, -35, -21).
# Bases: north ~(-16, 52, -17), south ~(17, -52, -17); stream bed z ~-22, hilltops z ~-15,
# cliff rims z ~-5 (above that, or beyond x = +-40 / y = +-55, the void shows).
# map.json "remove" deletes the CTF beacons (small red/blue ground lights) and flag bases.
# Water, waterfall and stars animate; trees don't sway, so stills face water or sky.
from shotlist import static, move, arc


def drift(name, cam, look, d=(0, 0, 0), fov=70, secs=75):
    """Near-static shot creeping by vector d over its length."""
    end = tuple(c + dd for c, dd in zip(cam, d))
    return move(name, secs, [(cam, look), (end, look)], fov, ease=True)


FALLS = (13.4, 50.6, -15)

SHOTS = [
    # wides: waterfall, stream, valley, ring (static or drifting)
    drift("tl_falls_trail", (5, 30, -19), FALLS, d=(0.6, 0.6, 0), fov=60),
    drift("tl_falls_gorge", (3, 22, -20.5), (13, 50, -16), d=(0, 0, 0.5), fov=50),
    drift("tl_stream_bend", (2, 15, -21), (4, 30, -21.5), d=(0.5, 0.5, 0), fov=60),
    drift("tl_stream_rocks", (-4, 5, -19), (2, 20, -22), d=(0.8, 0, 0), fov=65),
    drift("tl_stream_south", (-8, -42, -16), (3, -20, -21), d=(0.6, 0.6, 0), fov=65),
    drift("tl_ring_north_roof", (-16, 52, -10), (-16, 30, -14), d=(0.8, 0, 0), fov=75),
    drift("tl_ring_south_roof", (17, -52, -10), (17, -30, -14), d=(-0.8, 0, 0), fov=75),
    drift("tl_valley_moon", (0, 35, -12), (-20, 0.4, -16), d=(0, -1, 0), fov=75),
    drift("tl_valley_clouds", (0, -35, -12), (20, -0.4, -16), d=(0, 1, 0), fov=75),
    drift("tl_valley_ring", (0, -35, -12), (-20, -0.4, -16), d=(-1, 0, 0), fov=75),
    drift("tl_west_cliffs", (-35, 40, -14), (0, 0, -20), d=(0.8, -0.8, 0), fov=70),
    drift("tl_east_glade", (30, 30, -14), (0, 0, -20), d=(-0.8, 0, 0), fov=70),
    drift("tl_ridge_trail", (-25, 20, -16), (5, 20, -21), d=(0, -0.3, 0), fov=65),
    drift("tl_moon_cliff", (-10, -10, -19), (-40, -30, -16), d=(0, 0, 0.6), fov=60),

    # close-ups: falls, water, rock, trees against the sky
    static("tl_falls_tele", (3, 22, -20.5), (13.4, 50.6, -14), fov=22),
    static("tl_falls_pool", (11, 46, -16), (13.4, 50.6, -15.5), fov=45),
    static("tl_ripples", (2.5, 20, -20.5), (3.5, 26, -22.2), fov=45),
    static("tl_stream_stones", (1, -6, -20.5), (3, -12, -22), fov=40),
    static("tl_boulder_moss", (-4, 6, -20.5), (-1.9, 2.7, -21.7), fov=40),
    static("tl_pines_planet", (0, -35, -14), (-20, -30, -6), fov=40),
    static("tl_sun_planet", (5, -20, -20), (-10, -30, -12), fov=45),
    static("tl_ring_tele", (0, -35, -12), (-40, -0.4, 5), fov=25),
    static("tl_planet_tele", (0, 35, -12), (-20, 0.4, -6), fov=30),

    # fly-throughs and orbits
    move("tl_up_the_stream", 90, [((2, 10, -20.5), (5, 30, -21)), ((6, 34, -19.5), FALLS)], fov=62),
    move("tl_crane_falls", 85, [((5, 30, -20.5), FALLS), ((5, 30, -14), FALLS)], fov=60),
    arc("tl_orbit_stream", 90, 10, 225, 265, -18.5, look=(3, 22, -21.5), cx=3, cy=22, fov=62),
    move("tl_pan_valley", 80, [((0, -35, -12), (30, -10, -18)), ((0, -35, -12), (-30, 0, -18))], fov=66),
    move("tl_glide_south", 90, [((-6, -28, -19), (-1, -15, -22)), ((0, -10, -19), (3, 5, -22))], fov=62),
    move("tl_rise_roof", 85, [((-16, 45, -16), (-16, 25, -16)), ((-16, 45, -10), (-16, 25, -14))], fov=70),

    # interiors: the two bases' flag rooms (the doorways' red/blue floor lights stay out of frame)
    drift("tl_north_room", (-16, 53, -16.5), (-16, 60, -17), d=(0, 1, 0), fov=80),
    drift("tl_south_room", (17, -53, -16.5), (17, -60, -17), d=(0, -1, 0), fov=80),
]
