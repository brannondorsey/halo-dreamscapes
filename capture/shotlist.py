#!/usr/bin/env python3
"""Shot-list helpers. A list module defines SHOTS = [(name, seconds, keys, ease)], keys = [(t, x,y,z, tx,ty,tz, fov)].

    shotlist.py lists/b30.py run       # capture every shot via cap.sh (real time), QC each one (qc.py)
    shotlist.py lists/b30.py scout     # print 'x y z tx ty tz fov' of first+last key for scout.py
"""
import importlib.util, math, os, subprocess, sys

def P(r, deg, z, cx=0.0, cy=0.0):
    a = math.radians(deg)
    return (cx + r * math.cos(a), cy + r * math.sin(a), z)

def static(name, cam, look, fov=70, secs=75):
    return (name, secs, [(0, *cam, *look, fov)], False)

def move(name, secs, pairs, fov=70, ease=True):
    """pairs: list of (cam, look) spread evenly over secs."""
    n = len(pairs) - 1
    return (name, secs, [(secs * i / n, *c, *l, fov) for i, (c, l) in enumerate(pairs)], ease)

def arc(name, secs, r, a0, a1, z, look=(0, 0, 4), fov=70, steps=8, cx=0, cy=0, lookz=None):
    pairs = []
    for i in range(steps + 1):
        a = a0 + (a1 - a0) * i / steps
        pairs.append((P(r, a, z, cx, cy), look))
    return move(name, secs, pairs, fov, ease=False)

def lua(keys, ease):
    ks = ", ".join("{" + ", ".join(f"{v:.2f}" for v in k) + "}" for k in keys)
    return "{ ease = %s, keys = { %s } }" % ("true" if ease else "false", ks)

if __name__ == "__main__":
    spec = importlib.util.spec_from_file_location("lst", sys.argv[1]); m = importlib.util.module_from_spec(spec)
    sys.modules["shotlist"] = sys.modules[__name__]; spec.loader.exec_module(m)
    only = set(sys.argv[3:])
    for name, secs, keys, ease in m.SHOTS:
        if only and name not in only:
            continue
        if sys.argv[2] == "names":
            print(name)
        elif sys.argv[2] == "scout":
            for k in (keys[0], keys[-1]) if len(keys) > 1 else (keys[0],):
                print(" ".join(f"{v:.1f}" for v in k[1:]), f"# {name}")
        else:
            if os.path.exists(os.path.join(os.environ.get("HALO_DIR", os.path.expanduser("~/halo-trial")), "caps", name + ".mp4")) and "--redo" not in os.environ.get("SHOT_FLAGS", ""):
                print("skip", name); continue
            # film, then QC straight away; refilm a flagged shot up to twice before giving up
            import qc
            path = os.path.join(os.environ.get("HALO_DIR", os.path.expanduser("~/halo-trial")), "caps", name + ".mp4")
            for attempt in range(3):
                subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)), "cap.sh"), name, str(secs + 2), lua(keys, ease)], check=True)
                issues = qc.check(path, secs)
                if not issues:
                    break
                print(f"QC {name} (attempt {attempt + 1}): {'; '.join(issues)}", flush=True)
                os.rename(path, path[:-4] + f".bad{attempt + 1}.mp4")
            else:
                sys.exit(f"QC failed 3 times for {name}; fix the shot or the game state and re-run")
