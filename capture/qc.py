#!/usr/bin/env python3
"""qc.py lists/X.py : flag bad captures in $HALO_DIR/caps.

Checks each shot's capture for: missing/short files, hard cuts inside the shot (another shot or
a game restart got spliced in), black frames, and large areas of out-of-map void (Death Island
and other CE maps render it as flat lavender, b30 as flat purple). Exit status 1 if anything is flagged.
`shotlist.py run` calls check() after every capture and refilms flagged shots, so this script is
for re-checking a whole list.
"""
import importlib.util, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CAPS = os.path.join(os.environ.get("HALO_DIR", os.path.expanduser("~/halo-trial")), "caps")
W, H, FPS = 80, 60, 5
VOIDS = [(160, 160, 208), (51, 45, 85)]   # flat out-of-map colours (CE lavender, b30 purple)


def check(path, secs):
    """List of problems with one capture (empty = OK)."""
    if not os.path.exists(path):
        return ["missing"]
    issues = []
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={FPS},scale={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).astype(np.int16)
    if len(f) < secs * FPS:
        issues.append(f"short ({len(f) / FPS:.0f}s of {secs}s)")
    if len(f) > 1:
        d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2, 3))
        # a moving camera changes smoothly; a splice is a single huge jump
        for k in np.nonzero(d > max(25, 6 * np.median(d) + 8))[0][:3]:
            issues.append(f"cut at {k / FPS:.1f}s")
    if len(f):
        lum = f.mean(axis=3).mean(axis=(1, 2))
        if (lum < 8).any():
            issues.append(f"black at {np.argmax(lum < 8) / FPS:.1f}s")
        for c in VOIDS:
            frac = (np.abs(f - np.array(c)).max(axis=3) < 10).mean(axis=(1, 2))
            if (frac > 0.15).any():
                issues.append(f"void {frac.max():.0%} at {np.argmax(frac > 0.15) / FPS:.1f}s")
    return issues


if __name__ == "__main__":
    spec = importlib.util.spec_from_file_location("lst", sys.argv[1]); m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, HERE); spec.loader.exec_module(m)
    bad = 0
    for i, (name, secs, keys, ease) in enumerate(m.SHOTS, 1):
        issues = check(os.path.join(CAPS, name + ".mp4"), secs)
        bad += bool(issues)
        print(f"{i:3} {name:<22} {'OK' if not issues else '; '.join(issues)}")
    print(f"{bad} flagged")
    sys.exit(1 if bad else 0)
