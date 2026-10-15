"""maps/<name>/ holds every setting a map's hour cut depends on."""
import json, os, subprocess, sys

import pytest

import glitch
import maps
import soundtrack
from conftest import ROOT


def test_load(maproot):
    m = maps.load("testmap", root=maproot)
    assert m["name"] == "testmap"
    assert m["map"]["strip"] is True
    assert m["score"]["seed"] == 7
    assert m["glitch"]["minutes"] == 1
    assert [s[0] for s in maps.shots(m)] == ["t_one", "t_two"]


def test_caps_follow_shot_order(maproot):
    m = maps.load("testmap", root=maproot)
    assert maps.caps(m, "/h") == ["/h/caps/t_one.mp4", "/h/caps/t_two.mp4"]


def test_halo_dir_defaults_by_game(maproot, monkeypatch):
    monkeypatch.delenv("HALO_DIR", raising=False)
    m = maps.load("testmap", root=maproot)
    assert maps.halo_dir(m) == os.path.expanduser("~/halo-ce")
    monkeypatch.setenv("HALO_DIR", "/x")
    assert maps.halo_dir(m) == "/x"


@pytest.mark.parametrize("bad, err", [
    (dict(strip=True), "missing"),
    (dict(game="ce", strip=True, load_wait=35, output="o", sheet=None, sheet_approved=None, extra=1), "unknown"),
    (dict(game="xbox", strip=True, load_wait=35, output="o", sheet=None, sheet_approved=None), "game"),
    (dict(game="ce", strip="yes", load_wait=35, output="o", sheet=None, sheet_approved=None), "strip"),
])
def test_bad_map_json(maproot, bad, err):
    (maproot / "testmap" / "map.json").write_text(json.dumps(bad))
    with pytest.raises(ValueError, match=err):
        maps.load("testmap", root=maproot)


def test_remove_is_optional_list_of_tag_patterns(maproot):
    """map.json "remove": scenery tag-path fragments the rig deletes too (e.g. CTF beacons)."""
    assert maps.load("testmap", root=maproot)["map"].get("remove", []) == []
    f = maproot / "testmap" / "map.json"
    mp = json.loads(f.read_text())
    f.write_text(json.dumps({**mp, "remove": ["beacon", "flag_base"]}))
    assert maps.load("testmap", root=maproot)["map"]["remove"] == ["beacon", "flag_base"]
    r = subprocess.run([sys.executable, os.path.join(ROOT, "maps.py"), "testmap", "get", "remove"],
                       capture_output=True, text=True, env={**os.environ, "MAPS_DIR": str(maproot)})
    assert r.stdout.split() == ["beacon", "flag_base"]
    for bad in ("beacon", ["two words"], [""]):
        f.write_text(json.dumps({**mp, "remove": bad}))
        with pytest.raises(ValueError, match="remove"):
            maps.load("testmap", root=maproot)


def test_bad_score_and_glitch_files(maproot):
    d = maproot / "testmap"
    good = d.joinpath("score.json").read_text()
    d.joinpath("score.json").write_text(json.dumps({**json.loads(good), "bogus": 1}))
    with pytest.raises(ValueError, match="score.json"):
        maps.load("testmap", root=maproot)
    d.joinpath("score.json").write_text(good)
    d.joinpath("glitch.json").write_text(json.dumps(dict(minuts=1)))
    with pytest.raises(ValueError, match="glitch.json"):
        maps.load("testmap", root=maproot)


def test_cli(maproot):
    run = lambda *a: subprocess.run([sys.executable, "maps.py", *a], cwd=ROOT, capture_output=True, text=True,
                                    env={**os.environ, "MAPS_DIR": str(maproot), "HALO_DIR": "/h"})
    assert run("testmap", "get", "strip").stdout == "1\n"
    assert run("testmap", "get", "load_wait").stdout == "35\n"
    assert run("testmap", "caps").stdout.split() == ["/h/caps/t_one.mp4", "/h/caps/t_two.mp4"]
    assert run("list").stdout.split() == ["testmap"]
    assert run("nomap", "get", "strip").returncode != 0


# --- the real maps -------------------------------------------------------------

REAL = {"b30": (30, "trial", "hide", 155, "silent_cartographer_1h"),
        "bloodgulch": (31, "trial", True, 35, "blood_gulch_1h"),
        "deathisland": (41, "ce", True, 35, "death_island_1h"),
        "timberland": (51, "ce", True, 35, "timberland_1h")}
# b30 is a campaign level whose scripts still reference its Pelicans: deleting them segfaults the
# game, so b30 "hide"s vehicles (moved out of view) instead. Marines and Covenant go via ai_erase_all.
# the owner's picks from the score auditions (2026-10-12)
SCORE = {"b30": "sc_cartographer", "bloodgulch": "bg_canyon", "deathisland": "di_ringlight",
         "timberland": "tl_dusk"}


def test_every_map_folder_is_valid():
    assert sorted(maps.names()) == sorted(REAL)
    for name in maps.names():
        m = maps.load(name)
        assert len(maps.shots(m)) >= 20


@pytest.mark.parametrize("name", sorted(REAL))
def test_real_maps_settings(name):
    seed, game, strip, wait, out = REAL[name]
    m = maps.load(name)
    assert (m["map"]["game"], m["map"]["strip"], m["map"]["load_wait"], m["map"]["output"]) == (game, strip, wait, out)
    # the old hour.sh used: --calm --minutes 60 --seed N; the score is the owner's pick, same seed
    o = glitch.parse(["a.mp4", "--config", m["glitch_path"], "--score", m["score_path"]])
    ref = glitch.parse(["a.mp4", "--calm", "--minutes", "60", "--seed", str(seed)])
    for k in vars(ref):
        if k not in ("score", "durations", "seg_frames", "ntsc"):   # pins reproduce a published cut; ntsc is the CRT rate
            assert getattr(o, k) == getattr(ref, k), k
    assert o.score == json.loads(json.dumps(soundtrack.settings(SCORE[name], seed=seed)))


APPROVED = {"b30": "2026-10-13", "bloodgulch": "2026-10-13", "deathisland": "2026-10-12", "timberland": "2026-10-14"}


def test_timberland_removes_its_ctf_markers():
    assert maps.load("timberland")["map"]["remove"] == ["beacon", "flag_base"]


@pytest.mark.parametrize("name", sorted(APPROVED))
def test_approved_sheet_is_in_the_folder(name):
    m = maps.load(name)
    assert m["map"]["sheet_approved"] == APPROVED[name]
    assert os.path.exists(os.path.join(m["dir"], m["map"]["sheet"]))
