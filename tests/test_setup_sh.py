"""capture/setup.sh takes strip mode and the load wait from the map folder (console and sleep stubbed)."""
import os, shutil, subprocess, sys

import pytest

from conftest import ROOT


@pytest.fixture
def rig(tmp_path):
    cap = tmp_path / "capture"
    cap.mkdir()
    shutil.copy(os.path.join(ROOT, "capture", "setup.sh"), cap)
    shutil.copy(os.path.join(ROOT, "capture", "rig.lua"), cap)
    log = tmp_path / "log"
    (cap / "con.sh").write_text(f'#!/bin/bash\necho "con $1" >> {log}\n')
    (tmp_path / "maps.py").write_text(f"import runpy\nrunpy.run_path({os.path.join(ROOT, 'maps.py')!r}, run_name='__main__')\n")
    stubs = tmp_path / "bin"
    stubs.mkdir()
    # each sleep also logs whether strip mode is on at that moment
    (stubs / "sleep").write_text(f'#!/bin/bash\necho "sleep $1" >> {log}\n'
                                 f'[ -n "$(find {tmp_path}/halo -name strip 2>/dev/null)" ] && echo "  (strip on)" >> {log}\n'
                                 'true\n')
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
        run.raw = log.read_text().splitlines()
        run.mode = strip.read_text() if strip.exists() else None
        lines = [l for l in run.raw if l not in ("sleep 1.5", "  (strip on)")]   # con()'s per-command pause
        run.rig = strip.parents[3] / "scripts" / "global" / "rig.lua"
        return strip.exists(), lines
    return run


def test_deathisland_strips_and_waits_35(rig):
    strip, lines = rig("deathisland", "ce")
    assert strip and rig.mode == ""
    assert "con map_name deathisland" in lines
    assert lines[lines.index("con map_name deathisland") + 1] == "sleep 35"


def test_b30_hides_vehicles_and_waits_out_the_cutscene(rig):
    strip, lines = rig("b30")
    assert strip and rig.mode.strip() == "hide"
    assert lines[lines.index("con map_name b30") + 1] == "sleep 155"


def test_strip_env_still_overrides(rig):
    strip, _ = rig("bloodgulch", STRIP="0")
    assert not strip
    strip, _ = rig("b30", STRIP="1")
    assert strip and rig.mode == ""


def test_unknown_map_fails(rig):
    with pytest.raises(subprocess.CalledProcessError):
        rig("nomap")


def test_installs_the_current_rig(rig):
    rig("bloodgulch")
    assert rig.rig.read_text() == open(os.path.join(ROOT, "capture", "rig.lua")).read()


def test_strip_starts_only_after_the_map_has_loaded(rig):
    """b30's intro cutscene breaks (stuck letterbox, black fades) if its dropship is deleted mid-scene."""
    rig("b30")
    raw = rig.raw
    wait = raw.index("sleep 155")
    assert "  (strip on)" not in raw[:wait + 1]
    assert raw[-1] == "  (strip on)"


def test_remove_patterns_go_to_the_rig(rig):
    strip, _ = rig("timberland", "ce")
    assert strip and rig.mode.splitlines() == ["", "remove beacon", "remove flag_base"]
    strip, _ = rig("deathisland", "ce")
    assert rig.mode == ""
