#!/usr/bin/env python3
"""scout.py shots.txt out.png : each line 'x y z tx ty tz [fov]' -> numbered contact sheet of stills.

    ./shotlist.py lists/bloodgulch.py scout > s.txt && ./scout.py s.txt sheet.png
"""
import os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
NOW = os.path.join(os.environ.get("HALO_DIR", os.path.expanduser("~/halo-trial")), "now.png")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

lines = [l.split() for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]
tmp = tempfile.mkdtemp(prefix="scout-")
for i, v in enumerate(lines):
    fov = v[6] if len(v) > 6 else "70"
    tbl = "{ keys = { {0, %s,%s,%s, %s,%s,%s, %s} } }" % (*v[:6], fov)
    subprocess.run([os.path.join(HERE, "shot.sh"), tbl, "1.3"], check=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", NOW, "-vf",
                    f"scale=320:240,drawtext=fontfile={FONT}:text='{i}':fontsize=28:fontcolor=yellow:box=1:boxcolor=black@0.6:x=6:y=6",
                    os.path.join(tmp, f"{i:03d}.png")], check=True)
cols = 5
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", "1", "-i", os.path.join(tmp, "%03d.png"),
                "-vf", f"tile={cols}x{(len(lines) + cols - 1) // cols}", "-frames:v", "1", sys.argv[2]], check=True)
