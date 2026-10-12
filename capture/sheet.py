#!/usr/bin/env python3
"""sheet.py ../maps/X/shots.py out.png [names...] : numbered approval contact sheet, one tile per frame.

Static shots get one tile ("7 di_foam_close"); moving shots get their first and last key
("12a ..." / "12b ..."). Numbers follow the order of SHOTS, so they stay stable for review.
Needs the game running with the map set up (setup.sh) and the rig installed.
"""
import importlib.util, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import shotlist  # noqa: E402

NOW = os.path.join(os.environ.get("HALO_DIR", os.path.expanduser("~/halo-trial")), "now.png")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

spec = importlib.util.spec_from_file_location("lst", sys.argv[1]); m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
only = set(sys.argv[3:])
tmp = tempfile.mkdtemp(prefix="sheet-")
n = 0
for i, (name, secs, keys, ease) in enumerate(m.SHOTS, 1):
    if only and name not in only:
        continue
    ends = [(keys[0], ""), ] if len(keys) == 1 else [(keys[0], "a"), (keys[-1], "b")]
    for k, tag in ends:
        subprocess.run([os.path.join(HERE, "shot.sh"), shotlist.lua([(0, *k[1:])], False), "1.3"], check=True)
        label = f"{i}{tag} {name}".replace(":", r"\:")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", NOW, "-vf",
                        f"scale=320:240,drawtext=fontfile={FONT}:text='{label}':fontsize=15:fontcolor=yellow:"
                        "box=1:boxcolor=black@0.6:x=4:y=4", os.path.join(tmp, f"{n:03d}.png")], check=True)
        n += 1
cols = 4
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", "1", "-i", os.path.join(tmp, "%03d.png"),
                "-vf", f"tile={cols}x{(n + cols - 1) // cols}", "-frames:v", "1", sys.argv[2]], check=True)
print(f"{n} frames -> {sys.argv[2]}")
