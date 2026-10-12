"""End to end on synthetic footage: render a map from its folder, then replay the record bit-for-bit."""
import json, os, subprocess

import maps
import render


def test_render_then_replay_is_identical(maproot, tmp_path):
    caps = tmp_path / "halo" / "caps"
    caps.mkdir(parents=True)
    for name, src in (("t_one", "testsrc2"), ("t_two", "mandelbrot")):
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"{src}=s=320x240:r=30", "-t", "8",
                        "-pix_fmt", "yuv420p", str(caps / f"{name}.mp4")], check=True)
    d = maproot / "testmap"
    (d / "glitch.json").write_text(json.dumps(dict(minutes=0.25, seed=3, min_seg=2, max_seg=4)))
    m = maps.load("testmap", root=maproot)
    files = maps.caps(m, str(tmp_path / "halo"))
    out = str(tmp_path / "cut.mp4")
    render.run(render.glitch_cmd(m, files, out))
    rec = render.record(m, files, out)
    assert os.path.getsize(out) > 0
    res = render.replay(rec, str(caps), str(tmp_path / "again.mp4"))
    assert res == {"captures_match": True, "output_match": True}
