#!/usr/bin/env python3
"""Per-map settings: maps/<name>/ holds everything a map's hour cut depends on.

    map.json     game (trial|ce), strip (true: delete AI and bodies, vehicles, weapons etc.; "hide": park them
                 out of view instead, for levels whose scripts crash if they're deleted; it can't be off),
                 load_wait (s after
                 map_name before setup goes on), output (cut name in cuts/), sheet + sheet_approved (approved contact sheet, ISO date);
                 optional remove: scenery tag-path fragments strip mode also deletes (CTF beacons, flag bases)
    shots.py     the shot list (capture/shotlist.py helpers)
    score.json   full score settings (soundtrack.py --dump <preset> --seed N, then edit)
    glitch.json  glitch.py option values (keys are glitch.py's option names, e.g. min_seg)
    renders/     one JSON record per render (render.py)

    ./maps.py list                 # map folders
    ./maps.py <name> get <key>     # a map.json value (bools print 1/0); used by capture/setup.sh
    ./maps.py <name> caps          # capture paths in shot order, under $HALO_DIR
    ./maps.py <name> check         # validate the folder
"""
import contextlib, importlib.util, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "capture")]
import glitch, shotlist, soundtrack  # noqa: E402

MAP_KEYS = {"game", "strip", "load_wait", "output", "sheet", "sheet_approved"}
OPTIONAL_MAP_KEYS = {"remove"}
GAMES = {"trial": "~/halo-trial", "ce": "~/halo-ce"}


def maps_dir(root=None):
    return str(root or os.environ.get("MAPS_DIR") or os.path.join(HERE, "maps"))


def names(root=None):
    r = maps_dir(root)
    return sorted(n for n in os.listdir(r) if os.path.exists(os.path.join(r, n, "map.json")))


def load(name, root=None):
    d = os.path.join(maps_dir(root), name)
    if not os.path.exists(os.path.join(d, "map.json")):
        raise ValueError(f"no map folder {d}")
    with open(os.path.join(d, "map.json")) as f:
        mp = json.load(f)
    if MAP_KEYS - set(mp):
        raise ValueError(f"map.json: missing {sorted(MAP_KEYS - set(mp))}")
    if set(mp) - MAP_KEYS - OPTIONAL_MAP_KEYS:
        raise ValueError(f"map.json: unknown {sorted(set(mp) - MAP_KEYS - OPTIONAL_MAP_KEYS)}")
    rm = mp.get("remove", [])
    if not isinstance(rm, list) or not all(isinstance(p, str) and p and not p.split()[1:] and p.strip() == p for p in rm):
        raise ValueError("map.json: remove must be a list of tag-path fragments without spaces")
    if mp["game"] not in GAMES:
        raise ValueError(f"map.json: game must be one of {sorted(GAMES)}")
    if mp["strip"] not in (True, "hide"):   # strip mode keeps AI, bodies, vehicles and weapons out of shot
        raise ValueError('map.json: strip must be true or "hide"')
    m = dict(name=name, dir=d, map=mp, score_path=os.path.join(d, "score.json"),
             glitch_path=os.path.join(d, "glitch.json"), shots_path=os.path.join(d, "shots.py"))
    try:
        m["score"] = soundtrack.load(m["score_path"])
    except ValueError as e:
        raise ValueError(f"score.json: {e}") from None
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):
            glitch.parse(["x", "--config", m["glitch_path"]])
    except SystemExit:
        raise ValueError(f"glitch.json: {err.getvalue().strip().splitlines()[-1]}") from None
    with open(m["glitch_path"]) as f:
        m["glitch"] = json.load(f)
    return m


def shots(m):
    spec = importlib.util.spec_from_file_location(f"shots_{m['name']}", m["shots_path"])
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("shotlist", shotlist)
    spec.loader.exec_module(mod)
    return mod.SHOTS


def halo_dir(m):
    return os.environ.get("HALO_DIR") or os.path.expanduser(GAMES[m["map"]["game"]])


def caps(m, halo=None):
    return [os.path.join(halo or halo_dir(m), "caps", s[0] + ".mp4") for s in shots(m)]


if __name__ == "__main__":
    a = sys.argv[1:]
    try:
        if a == ["list"]:
            print("\n".join(names()))
        elif len(a) == 3 and a[1] == "get":
            v = load(a[0])["map"].get(a[2], [] if a[2] in OPTIONAL_MAP_KEYS else None)
            if v is None:
                raise KeyError(a[2])
            print("\n".join(v) if isinstance(v, list) else int(v) if isinstance(v, bool) else v)
        elif len(a) == 2 and a[1] == "caps":
            print("\n".join(caps(load(a[0]))))
        elif len(a) == 2 and a[1] == "check":
            m = load(a[0])
            print(f"{a[0]}: OK ({len(shots(m))} shots)")
        else:
            sys.exit(__doc__)
    except (ValueError, KeyError) as e:
        sys.exit(f"{a[0]}: {e}")
