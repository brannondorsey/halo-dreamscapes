"""The lockstep shim: an armed capture of a slow, irregular, clock-driven GL app is evenly spaced."""
import os, shutil, subprocess, time

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LS = os.path.join(ROOT, "capture", "lockstep")
W, H, SPEED, FPS = 320, 120, 60.0, 30

pytestmark = pytest.mark.skipif(not (shutil.which("Xvfb") and shutil.which("gcc")), reason="needs Xvfb and gcc")


@pytest.fixture
def app(tmp_path):
    subprocess.run([os.path.join(LS, "build.sh")], check=True)
    exe = tmp_path / "bar"
    subprocess.run(["gcc", "-O1", "-o", str(exe), os.path.join(ROOT, "tests", "fixtures", "bar.c"), "-lGL", "-lX11", "-lm"],
                   check=True)
    xvfb = subprocess.Popen(["Xvfb", ":97", "-screen", "0", "400x200x24", "+extension", "GLX"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    ctl = tmp_path / "ctl"
    env = {**os.environ, "DISPLAY": ":97", "LOCKSTEP_CTL": str(ctl), "LOCKSTEP_FPS": str(FPS),
           "LD_PRELOAD": os.path.join(LS, "out", "$LIB", "liblockstep.so"), "LIBGL_ALWAYS_SOFTWARE": "1"}
    proc = subprocess.Popen([str(exe), "20000000"], env=env)
    yield ctl, tmp_path
    proc.kill()
    xvfb.kill()


def arm(ctl, out, frames, timeout=120):
    (ctl.parent / "ctl.tmp").write_text(f"{frames} {out}\n")
    os.rename(ctl.parent / "ctl.tmp", ctl)
    t = time.time()
    while not os.path.exists(str(ctl) + ".done"):
        assert time.time() - t < timeout, "capture never finished"
        time.sleep(0.1)
    os.remove(str(ctl) + ".done")
    return np.fromfile(out, np.uint8).reshape(-1, H, W, 3)


def bar_x(frames):
    lum = frames.mean(axis=(1, 3))                  # column brightness per frame
    cols = np.arange(W)
    return np.array([(cols * (l > 128)).sum() / max((l > 128).sum(), 1) for l in lum])


def test_armed_capture_is_evenly_spaced(app):
    ctl, tmp = app
    time.sleep(1)                                   # runs on real time until armed
    f = arm(ctl, tmp / "a.rgb", 45)
    assert len(f) == 45
    step = np.diff(bar_x(f))
    step = step[np.abs(step) < 100]                 # drop the wrap-around
    assert np.allclose(step, SPEED / FPS, atol=0.05), step   # every frame exactly 1/30 s apart, no holds


def test_clock_resumes_after_a_capture(app):
    ctl, tmp = app
    a = arm(ctl, tmp / "a.rgb", 10)
    b = arm(ctl, tmp / "b.rgb", 10)                 # a second capture also works and is evenly spaced
    assert len(a) == len(b) == 10
    step = np.diff(bar_x(b))
    step = step[np.abs(step) < 100]
    assert np.allclose(step, SPEED / FPS, atol=0.05), step
