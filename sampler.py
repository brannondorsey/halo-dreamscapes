#!/usr/bin/env python3
"""Render a labeled reel that demos every glitch effect once, for picking favourites.

Each demo is numbered and titled on screen, and says whether the long-form --calm preset
(used for the hour cuts) uses it [CALM] or only the default/heavy mode does [FULL].

    ./sampler.py --still a.mp4 b.mp4 c.mp4 --moving fly.mp4 orbit.mp4 -o sampler.mp4
    ./sampler.py -o sampler.mp4        # old clips/ names (sc_sea_static, bg_flythrough, ...)

--still wants 3 locked-off clips (ideally with water/sky motion), --moving 2 camera moves
(a forward fly-through, then an orbit or pan). Every clip should be at least 12 s long.
"""
import argparse, os, random, shutil, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glitch  # noqa: E402

C = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clips")
OLD = dict(still=["sc_sea_static", "bg_low_static", "sc_aerial_static"], moving=["bg_flythrough", "sc_orbit"])


def demos(s1, s2, s3, fly, orbit):
    def seg(src, start, length, into="cut", **kw):
        return dict(src=src, start=start, len=length, into=into, events=kw.pop("events", []), **kw)
    # (title, subtitle, segments). Subtitles also name the matching audio glitch.
    return [
        ("0  CLEAN CUT [CALM+FULL]", "reference, no glitch", [
            seg(s1, 2, 3), seg(s2, 2, 4)]),
        ("1  MOSH -> fly-through [CALM+FULL]", "keyframe dropped: new motion drags old image | audio: freeze", [
            seg(s1, 2, 3), seg(fly, 2, 7, "mosh", heal=5.5)]),
        ("2  MOSH -> orbit [CALM+FULL]", "same, onto a slow orbit | audio: freeze", [
            seg(s3, 2, 3), seg(orbit, 2, 7, "mosh", heal=5.5)]),
        ("3  MOSH still -> still [CALM+FULL]", "old picture holds, new one bleeds in | audio: freeze", [
            seg(s2, 2, 3), seg(s3, 2, 7, "mosh", heal=5.5)]),
        ("4  BLOOM gentle [CALM]", "one P-frame repeated 16x: motion smears out | audio: stutter", [
            seg(fly, 2, 7, bloom=(2.0, 16))]),
        ("5  BLOOM heavy [FULL]", "one P-frame repeated 40x | audio: stutter", [
            seg(orbit, 2, 7, bloom=(2.0, 40))]),
        ("6  SOFT TEAR [CALM]", "one gentle slip of the lower field | audio: light crush", [
            seg(s1, 2, 7, events=[(1.5, 0.8, "softtear"), (4.5, 0.6, "softtear")])]),
        ("7  TEAR in-shot [FULL]", "vsync tear: lower field lags + slips | audio: bitcrush", [
            seg(orbit, 2, 7, events=[(1.5, 2.5, "tear")])]),
        ("8  TEAR transition [FULL]", "tear burst across a cut | audio: bitcrush", [
            seg(s2, 2, 3), seg(fly, 4, 4, "tear")]),
        ("9  SLIP [FULL]", "h-sync band slips with RGB split | audio: bitcrush", [
            seg(s1, 2, 7, events=[(1.5, 2.5, "slip")])]),
        ("10 ROLL [FULL]", "vertical hold loss, black blanking bar | audio: tape stop", [
            seg(s3, 2, 7, events=[(1.5, 2.0, "roll")])]),
        ("11 MOSH + BLOOM [CALM+FULL]", "both stacked on one transition | audio: freeze + stutter", [
            seg(s1, 2, 3), seg(fly, 2, 8, "mosh", heal=6.5, bloom=(2.5, 24))]),
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", default="sampler.mp4")
    ap.add_argument("--still", nargs=3, metavar="MP4", help="three locked-off clips")
    ap.add_argument("--moving", nargs=2, metavar="MP4", help="fly-through clip, then orbit/pan clip")
    ap.add_argument("--only", type=int, nargs="+", metavar="N", help="render just these demo numbers")
    ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--mute", action="store_true")
    o = ap.parse_args()
    still = o.still or [os.path.join(C, n + ".mp4") for n in OLD["still"]]
    moving = o.moving or [os.path.join(C, n + ".mp4") for n in OLD["moving"]]
    segs = []
    for i, (title, sub, ss) in enumerate(demos(*still, *moving)):
        if o.only and i not in o.only:
            continue
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
