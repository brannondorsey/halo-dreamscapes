#!/usr/bin/env python3
"""qc.py ../maps/X/shots.py : flag bad captures in $HALO_DIR/caps.

Checks each shot's capture for: missing/short files, hard cuts inside the shot (another shot or
a game restart got spliced in), black frames, cutscene letterbox bars, an open console (both mean the
game was paused or mid-cutscene), AI the rig had to erase mid-shot (cap.sh's <capture>.ai), and large areas of out-of-map void (Death Island
and other CE maps render it as flat lavender, b30 as flat purple). Exit status 1 if anything is flagged.
`shotlist.py run` calls check() after every capture and refilms flagged shots, so this script is
for re-checking a whole list.
"""
import importlib.util, os, subprocess, sys, tempfile
import numpy as np

import console

HERE = os.path.dirname(os.path.abspath(__file__))
CAPS = os.path.join(os.environ.get("HALO_DIR", os.path.expanduser("~/halo-trial")), "caps")
W, H, FPS = 80, 60, 5
VOIDS = [(160, 160, 208), (51, 45, 85)]   # flat out-of-map colours (CE lavender, b30 purple)


def check(path, secs):
    """List of problems with one capture (empty = OK)."""
    if not os.path.exists(path):
        return ["missing"]
    issues = []
    if os.path.exists(path + ".ai"):   # cap.sh: the rig found (and erased) AI while this shot was filmed
        issues.append(f"AI on screen ({open(path + '.ai').read().strip()} rig polls)")
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
        # cutscene letterbox: flat black bands top and bottom (the game was mid-cutscene or paused)
        band = 7  # 60 px of 480
        top, bottom = f[:, :band].max(axis=(1, 2, 3)), f[:, -band:].max(axis=(1, 2, 3))
        if ((top < 8) & (bottom < 8)).mean() > 0.5:
            issues.append("letterbox")
    # an open console pauses the game; its prompt only reads at full resolution
    with tempfile.TemporaryDirectory() as d:
        png = os.path.join(d, "mid.png")
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(secs / 2), "-i", path, "-frames:v", "1", png])
        if os.path.exists(png) and console.is_open(png):
            issues.append("console open")
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
