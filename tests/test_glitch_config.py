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
