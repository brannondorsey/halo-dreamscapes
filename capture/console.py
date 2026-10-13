#!/usr/bin/env python3
"""console.py screenshot.png : exit 0 if Halo's console is open (its magenta "halo(" prompt shows in the
bottom-left corner), else 1. con.sh uses it to keep the console's open/closed state in sync: a dropped
` keypress during a heavy load once left the console open, which pauses the game (b30's intro froze).
"""
import subprocess, sys

import numpy as np


def is_open(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    w = int(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width", "-of", "csv=p=0", path],
                           capture_output=True, text=True, check=True).stdout.split()[0])
    img = np.frombuffer(raw, np.uint8).reshape(-1, w, 3).astype(int)
    corner = img[-40:, :120]
    r, g, b = corner[..., 0], corner[..., 1], corner[..., 2]
    return int(((r > 150) & (b > 150) & (g < 100)).sum()) > 15


if __name__ == "__main__":
    sys.exit(0 if is_open(sys.argv[1]) else 1)
