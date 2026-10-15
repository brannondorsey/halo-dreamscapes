"""qc.check flags captures with cutscene letterbox bars or an open console (the game is paused)."""
import os, subprocess

import pytest

from conftest import ROOT
import qc

F = os.path.join(ROOT, "tests", "fixtures")


def clip(tmp_path, name, vf, extra=()):
    p = str(tmp_path / f"{name}.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "mandelbrot=s=640x480:r=30", *extra,
                    "-t", "4", "-filter_complex", vf, "-pix_fmt", "yuv420p", p], check=True)
    return p


def test_clean_clip_passes(tmp_path):
    assert qc.check(clip(tmp_path, "ok", "null"), 4) == []


def test_letterbox_is_flagged(tmp_path):
    p = clip(tmp_path, "lb", "drawbox=0:0:640:60:black:t=fill,drawbox=0:420:640:60:black:t=fill")
    assert any("letterbox" in i for i in qc.check(p, 4))


def test_open_console_is_flagged(tmp_path):
    p = clip(tmp_path, "con", "[0][1]overlay=0:440", extra=("-loop", "1", "-i", os.path.join(F, "console_open.png")))
    assert any("console" in i for i in qc.check(p, 4))


def test_ai_seen_during_capture_is_flagged(tmp_path):
    """cap.sh leaves <capture>.ai when the rig erased AI mid-shot: something may have walked into frame."""
    p = clip(tmp_path, "ai", "null")
    open(p + ".ai", "w").write("3\n")
    assert any("AI" in i for i in qc.check(p, 4))
