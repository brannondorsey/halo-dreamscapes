"""console.py tells whether Halo's console is open from a screenshot (its magenta "halo(" prompt)."""
import os, subprocess, sys

import numpy as np
import pytest

from conftest import ROOT

F = os.path.join(ROOT, "tests", "fixtures")
import console  # noqa: E402


def test_open_prompt_is_detected():
    assert console.is_open(os.path.join(F, "console_open.png"))


def test_game_frame_is_closed():
    assert not console.is_open(os.path.join(F, "console_closed.png"))


def test_letterbox_black_is_closed(tmp_path):
    p = str(tmp_path / "black.png")
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=black:s=640x480", "-frames:v", "1", p], check=True)
    assert not console.is_open(p)


def test_cli_exit_status():
    run = lambda f: subprocess.run([sys.executable, os.path.join(ROOT, "capture", "console.py"), os.path.join(F, f)]).returncode
    assert run("console_open.png") == 0
    assert run("console_closed.png") == 1
