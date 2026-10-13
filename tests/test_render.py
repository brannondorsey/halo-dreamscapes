"""render.py films and renders a map from its folder, records what it used, and can replay a record."""
import hashlib, json, os, subprocess

import pytest

import maps
import render


def touch(p, data=b"x"):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(data)
    return p


def test_glitch_command_uses_the_map_folder(maproot):
    m = maps.load("testmap", root=maproot)
    cmd = render.glitch_cmd(m, ["/h/caps/t_one.mp4", "/h/caps/t_two.mp4"], "/o/test_1h.mp4")
    assert cmd[1:] == ["/h/caps/t_one.mp4", "/h/caps/t_two.mp4", "--config", m["glitch_path"],
                       "--score", m["score_path"], "-o", "/o/test_1h.mp4"]
    assert cmd[0].endswith("glitch.py")


def test_film_commands(maproot, monkeypatch):
    calls = []
    monkeypatch.setattr(render, "run", lambda cmd, **kw: calls.append((cmd, kw.get("env", {}))))
    m = maps.load("testmap", root=maproot)
    render.film(m, "/h")
    assert [c[0][0].split("/")[-1] for c in calls] == ["setup.sh", "shotlist.py", "shot.sh"]
    assert calls[0][0][1] == "testmap"
    assert calls[1][0][1:] == [m["shots_path"], "run"]
    assert all(env["HALO_DIR"] == "/h" and env["MAPS_DIR"] == str(maproot) for _, env in calls)


def test_record(maproot, tmp_path):
    m = maps.load("testmap", root=maproot)
    caps = [touch(str(tmp_path / "caps" / n), n.encode()) for n in ("t_one.mp4", "t_two.mp4")]
    out = touch(str(tmp_path / "cuts" / "test_1h.mp4"), b"video")
    path = render.record(m, caps, out, link="https://litter.catbox.moe/abc.mp4")
    assert os.path.dirname(path) == os.path.join(m["dir"], "renders")
    r = json.load(open(path))
    assert r["map"] == "testmap"
    assert r["settings"]["map"] == m["map"]
    assert r["settings"]["score"] == m["score"]
    assert r["settings"]["glitch"] == m["glitch"]
    assert r["settings"]["shots"] == open(m["shots_path"]).read()
    assert r["captures"] == [{"name": "t_one.mp4", "bytes": 9, "sha256": hashlib.sha256(b"t_one.mp4").hexdigest()},
                             {"name": "t_two.mp4", "bytes": 9, "sha256": hashlib.sha256(b"t_two.mp4").hexdigest()}]
    assert r["output"] == {"file": "test_1h.mp4", "bytes": 5, "sha256": hashlib.sha256(b"video").hexdigest()}
    assert r["link"] == "https://litter.catbox.moe/abc.mp4"
    assert len(r["commit"]) == 40 and isinstance(r["dirty"], bool)
    assert {"python", "numpy", "scipy", "ffmpeg"} <= set(r["versions"])


def test_replay_writes_the_recorded_settings_back(maproot, tmp_path, monkeypatch):
    m = maps.load("testmap", root=maproot)
    caps = [touch(str(tmp_path / "caps" / n), n.encode()) for n in ("t_one.mp4", "t_two.mp4")]
    rec = render.record(m, caps, touch(str(tmp_path / "test_1h.mp4"), b"video"))
    # settings change after the render; a replay must still use the recorded ones
    (maproot / "testmap" / "glitch.json").write_text(json.dumps(dict(minutes=2, seed=99)))
    ran = []
    monkeypatch.setattr(render, "run", lambda cmd, **kw: ran.append(cmd) or touch(cmd[-1], b"video"))
    res = render.replay(rec, str(tmp_path / "caps"), str(tmp_path / "again.mp4"))
    cmd = ran[0]
    assert json.load(open(cmd[cmd.index("--config") + 1])) == json.load(open(rec))["settings"]["glitch"]
    assert json.load(open(cmd[cmd.index("--score") + 1])) == json.load(open(rec))["settings"]["score"]
    assert cmd[1:3] == caps
    assert res == {"captures_match": True, "output_match": True}


def test_replay_reports_changed_captures(maproot, tmp_path, monkeypatch):
    m = maps.load("testmap", root=maproot)
    caps = [touch(str(tmp_path / "caps" / n), n.encode()) for n in ("t_one.mp4", "t_two.mp4")]
    rec = render.record(m, caps, touch(str(tmp_path / "test_1h.mp4"), b"video"))
    touch(caps[0], b"refilmed")
    monkeypatch.setattr(render, "run", lambda cmd, **kw: touch(cmd[-1], b"different"))
    res = render.replay(rec, str(tmp_path / "caps"), str(tmp_path / "again.mp4"))
    assert res == {"captures_match": False, "output_match": False}


def test_share_parses_share_sh(monkeypatch):
    monkeypatch.setattr(render.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
        a, 0, stdout="https://litter.catbox.moe/xyz.mp4  f.mp4 (5 MB, expires in 72h)\n"))
    assert render.share("f.mp4") == "https://litter.catbox.moe/xyz.mp4"


def test_failed_share_keeps_the_record(maproot, tmp_path, monkeypatch, capsys):
    m = maps.load("testmap", root=maproot)
    caps = [touch(str(tmp_path / "caps" / n), n.encode()) for n in ("t_one.mp4", "t_two.mp4")]
    out = touch(str(tmp_path / "cut.mp4"), b"video")
    def fail(path):
        raise subprocess.CalledProcessError(1, ["share.sh"])
    monkeypatch.setattr(render, "share", fail)
    rec = render.finish(m, caps, out, share=True)
    assert json.load(open(rec))["link"] is None
    assert "upload failed" in capsys.readouterr().out


def test_share_record_adds_the_link_later(maproot, tmp_path, monkeypatch):
    m = maps.load("testmap", root=maproot)
    caps = [touch(str(tmp_path / "caps" / n), n.encode()) for n in ("t_one.mp4", "t_two.mp4")]
    out = touch(str(tmp_path / "cut.mp4"), b"video")
    rec = render.finish(m, caps, out)
    shared = []
    monkeypatch.setattr(render, "share", lambda p: shared.append(p) or "https://litter.catbox.moe/new.mp4")
    render.share_record(rec, str(tmp_path))
    assert shared == [out]
    assert json.load(open(rec))["link"] == "https://litter.catbox.moe/new.mp4"


def test_share_record_refuses_a_different_file(maproot, tmp_path, monkeypatch):
    m = maps.load("testmap", root=maproot)
    caps = [touch(str(tmp_path / "caps" / n), n.encode()) for n in ("t_one.mp4", "t_two.mp4")]
    out = touch(str(tmp_path / "cut.mp4"), b"video")
    rec = render.finish(m, caps, out)
    touch(out, b"re-rendered since")
    monkeypatch.setattr(render, "share", lambda p: "https://x")
    with pytest.raises(ValueError, match="sha256"):
        render.share_record(rec, str(tmp_path))


def test_refuses_to_film_or_render_before_the_sheet_is_approved(maproot, monkeypatch, capsys):
    """The owner approves the numbered contact sheet before anything is filmed (CLAUDE.md)."""
    def boom(*a, **kw):
        raise AssertionError("filmed or rendered an unapproved map")
    monkeypatch.setattr(render, "film", boom)
    monkeypatch.setattr(render, "run", boom)
    monkeypatch.setenv("MAPS_DIR", str(maproot))
    for argv in (["render.py", "testmap"], ["render.py", "testmap", "--no-film"]):
        monkeypatch.setattr("sys.argv", argv)
        with pytest.raises(SystemExit) as e:
            render.main()
        assert "sheet_approved" in str(e.value.code)
