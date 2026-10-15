"""glitch.py reads its settings from a JSON file; command-line flags still win."""
import json

import pytest

import glitch
import soundtrack


def cfg(tmp_path, **kw):
    p = tmp_path / "glitch.json"
    p.write_text(json.dumps(kw))
    return str(p)


def test_config_sets_options(tmp_path):
    o = glitch.parse(["a.mp4", "--config", cfg(tmp_path, minutes=60, seed=41, soft_tears=4)])
    assert (o.minutes, o.seed, o.soft_tears) == (60, 41, 4)


def test_flags_override_config(tmp_path):
    o = glitch.parse(["a.mp4", "--config", cfg(tmp_path, seed=41), "--seed", "5"])
    assert o.seed == 5


def test_calm_preset_does_not_clobber_config_values(tmp_path):
    o = glitch.parse(["a.mp4", "--config", cfg(tmp_path, calm=True, min_seg=30, mosh=2.0)])
    assert (o.min_seg, o.mosh) == (30, 2.0)          # from the file
    assert (o.max_seg, o.bloom) == (90, 0.3)         # calm fills in the rest


def test_calm_preset_still_works_without_config():
    o = glitch.parse(["a.mp4", "--calm"])
    assert (o.min_seg, o.max_seg, o.mosh, o.bloom) == (45, 90, 2.5, 0.3)


def test_unknown_config_key_is_an_error(tmp_path):
    with pytest.raises(SystemExit):
        glitch.parse(["a.mp4", "--config", cfg(tmp_path, minuts=60)])


def test_score_file_becomes_the_score(tmp_path):
    p = tmp_path / "score.json"
    p.write_text(json.dumps(soundtrack.settings("bg_dust", seed=9)))
    o = glitch.parse(["a.mp4", "--score", str(p)])
    assert o.score == json.loads(json.dumps(soundtrack.settings("bg_dust", seed=9)))


def test_score_and_style_are_exclusive(tmp_path):
    p = tmp_path / "score.json"
    p.write_text(json.dumps(soundtrack.settings("original", seed=1)))
    with pytest.raises(SystemExit):
        glitch.parse(["a.mp4", "--score", str(p), "--style", "bg_dust"])


def test_style_flag_still_selects_a_preset():
    o = glitch.parse(["a.mp4", "--style", "di_moonlit"])
    assert o.score == "di_moonlit"


def test_durations_and_seg_frames_come_from_config(tmp_path):
    o = glitch.parse(["a.mp4", "--config", cfg(tmp_path, durations={"a.mp4": 77.0333}, seg_frames={"3": 1909})])
    assert o.durations == {"a.mp4": 77.0333} and o.seg_frames == {"3": 1909}


def test_durations_override_measured_lengths(monkeypatch):
    monkeypatch.setattr(glitch, "duration", lambda p: 77.0)
    lens = glitch.lengths(["caps/a.mp4", "caps/b.mp4"], {"a.mp4": 2311 / 30})
    assert lens == {"caps/a.mp4": 2311 / 30, "caps/b.mp4": 77.0}


def test_seg_frames_pin_each_segments_frame_count(tmp_path):
    """A pinned segment has exactly that many frames, whatever its length rounds to."""
    import subprocess
    clip = str(tmp_path / "c.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=320x240:r=30", "-t", "6",
                    "-pix_fmt", "yuv420p", clip], check=True)
    segs = [dict(src=clip, start=0.2, len=2.0, into="cut", events=[], frames=57),
            dict(src=clip, start=1.0, len=1.5, into="cut", events=[], frames=46)]
    out = str(tmp_path / "o.mp4")
    glitch.render(segs, out, str(tmp_path), __import__("random").Random(1), mute=True)
    n = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_entries", "stream=nb_read_frames",
                        "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
    assert int(n) == 57 + 46


def test_ntsc_conforms_to_29_97_keeping_every_frame(tmp_path):
    """NTSC CRTs run at 59.94 fields/s: 30.00 fps would drop a frame every ~33 s. --ntsc keeps every
    frame at 30000/1001 and slows the score by the same 0.1%, so picture and sound stay in sync."""
    import subprocess
    clip = str(tmp_path / "c.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=320x240:r=30", "-t", "8",
                    "-pix_fmt", "yuv420p", clip], check=True)
    segs = [dict(src=clip, start=0.0, len=6.0, into="cut", events=[], frames=180)]
    out = str(tmp_path / "o.mp4")
    glitch.render(segs, out, str(tmp_path), __import__("random").Random(1), ntsc=True)
    probe = lambda sel, entries: subprocess.run(["ffprobe", "-v", "error", "-select_streams", sel, "-count_frames",
                                                 "-show_entries", entries, "-of", "json", out],
                                                capture_output=True, text=True).stdout
    v = json.loads(probe("v", "stream=r_frame_rate,nb_read_frames,duration"))["streams"][0]
    a = json.loads(probe("a", "stream=duration"))["streams"][0]
    assert v["r_frame_rate"] == "30000/1001" and int(v["nb_read_frames"]) == 180
    assert abs(float(a["duration"]) - 180 * 1001 / 30000) < 0.05
    assert glitch.parse(["a.mp4", "--config", cfg(tmp_path, ntsc=True)]).ntsc
