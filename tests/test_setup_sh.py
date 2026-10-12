"""capture/setup.sh takes strip mode and the load wait from the map folder (console and sleep stubbed)."""
import os, shutil, subprocess, sys

import pytest

from conftest import ROOT


@pytest.fixture
def rig(tmp_path):
    cap = tmp_path / "capture"
    cap.mkdir()
    shutil.copy(os.path.join(ROOT, "capture", "setup.sh"), cap)
    log = tmp_path / "log"
    (cap / "con.sh").write_text(f'#!/bin/bash\necho "con $1" >> {log}\n')
    (tmp_path / "maps.py").write_text(f"import runpy\nrunpy.run_path({os.path.join(ROOT, 'maps.py')!r}, run_name='__main__')\n")
    stubs = tmp_path / "bin"
    stubs.mkdir()
    (stubs / "sleep").write_text(f'#!/bin/bash\necho "sleep $1" >> {log}\n')
    for f in (cap / "con.sh", stubs / "sleep"):
        f.chmod(0o755)

    def run(name, game="trial", **env):
        halo = tmp_path / "halo"
        if game == "ce":
            (halo / "game").mkdir(parents=True, exist_ok=True)
            (halo / "game" / "haloce.exe").write_text("")
        log.write_text("")
        subprocess.run(["bash", str(cap / "setup.sh"), name], check=True,
                       env={**os.environ, "PATH": f"{stubs}:{os.path.dirname(sys.executable)}:{os.environ['PATH']}", "HALO_DIR": str(halo), **env})
        folder = "Halo CE" if game == "ce" else "Halo Trial"
        strip = halo / f"prefix/drive_c/users/{os.environ.get('USER', 'root')}/Documents/My Games/{folder}/chimera/lua/data/global/rig/strip"
        lines = [l for l in log.read_text().splitlines() if l != "sleep 1.5"]   # con()'s per-command pause
        return strip.exists(), lines
    return run


def test_deathisland_strips_and_waits_35(rig):
    strip, lines = rig("deathisland", "ce")
    assert strip
    assert "con map_name deathisland" in lines
    assert lines[lines.index("con map_name deathisland") + 1] == "sleep 35"


def test_b30_does_not_strip_and_waits_out_the_cutscene(rig):
    strip, lines = rig("b30")
    assert not strip
    assert lines[lines.index("con map_name b30") + 1] == "sleep 155"


def test_strip_env_still_overrides(rig):
    strip, _ = rig("b30", STRIP="1")
    assert strip


def test_unknown_map_fails(rig):
    with pytest.raises(subprocess.CalledProcessError):
        rig("nomap")
