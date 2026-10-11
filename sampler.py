#!/usr/bin/env python3
"""Render a labeled reel that demos every glitch effect once, for picking favourites.

    ./sampler.py -o sampler.mp4            # needs the default clips/ captures
"""
import argparse, os, random, shutil, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glitch  # noqa: E402

C = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clips")


def seg(clip, start, length, into="cut", **kw):
    return dict(src=os.path.join(C, clip + ".mp4"), start=start, len=length, into=into, events=kw.pop("events", []), **kw)


# (title, subtitle, segments). Subtitles also name the matching audio glitch.
DEMOS = [
    ("0  CLEAN CUT", "reference, no glitch", [
        seg("sc_sea_static", 4, 3), seg("bg_low_static", 4, 4)]),
    ("1  MOSH -> flythrough", "keyframe dropped: new motion drags old image | audio: freeze", [
        seg("sc_sea_static", 4, 3), seg("bg_flythrough", 8, 7, "mosh", heal=5.5)]),
    ("2  MOSH -> orbit", "same, onto a slow orbit | audio: freeze", [
        seg("bg_ring_static", 4, 3), seg("sc_orbit", 6, 7, "mosh", heal=5.5)]),
    ("3  MOSH static -> static", "old picture holds, new one bleeds in | audio: freeze", [
        seg("bg_low_static", 4, 3), seg("sc_aerial_static", 4, 7, "mosh", heal=5.5)]),
    ("4  BLOOM (flythrough)", "one P-frame repeated: motion smears out | audio: stutter", [
        seg("bg_flythrough", 6, 7, bloom=(2.0, 40))]),
    ("5  BLOOM (orbit)", "same on a slow orbit | audio: stutter", [
        seg("sc_orbit", 4, 7, bloom=(2.0, 30))]),
    ("6  TEAR (in-shot)", "vsync tear: lower field lags + slips | audio: bitcrush", [
        seg("bg_orbit_base", 6, 7, events=[(1.5, 2.5, "tear")])]),
    ("7  TEAR (transition)", "tear burst across a cut | audio: bitcrush", [
        seg("sc_aerial_static", 4, 3), seg("bg_flythrough", 10, 4, "tear")]),
    ("8  SLIP", "h-sync band slips with RGB split | audio: bitcrush", [
        seg("sc_sea_static", 6, 7, events=[(1.5, 2.5, "slip")])]),
    ("9  ROLL", "vertical hold loss, black blanking bar | audio: tape stop", [
        seg("bg_ring_static", 6, 7, events=[(1.5, 2.0, "roll")])]),
    ("10 MOSH + BLOOM", "both stacked on one transition | audio: freeze + stutter", [
        seg("sc_sea_static", 4, 3), seg("bg_flythrough", 8, 8, "mosh", heal=6.5, bloom=(2.5, 30))]),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", default="sampler.mp4")
    ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--mute", action="store_true")
    o = ap.parse_args()
    segs = []
    for title, sub, ss in DEMOS:
        for s in ss:
            s["label"] = (title, sub)
            segs.append(s)
    tmp = tempfile.mkdtemp(prefix="halo-sampler-")
    try:
        glitch.render(segs, o.out, tmp, random.Random(o.seed), o.seed, o.mute)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
