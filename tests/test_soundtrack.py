"""Score settings: every preset expands to a complete, JSON-serialisable settings dict that renders
exactly like the preset, and the original score never changes."""
import hashlib, json, subprocess, sys, wave

import numpy as np
import pytest

import soundtrack
from conftest import ROOT

# sha256 of render(12, seed) from the score engine before settings files existed (commit 0a047cf)
GOLDEN = {30: "15cbc8b6080be17636e75daa60a077a024c6be44e335109838b4821fc8be4bd9",
          31: "9603256fab7ef7531187b6b53e48b30a83b794714ed9a6b3fcd3774d3021a530",
          41: "938b2f533ccc2746dad20b7b7acf22bf5b1e185b17409909cbff9e532b451692"}


def sha(x):
    return hashlib.sha256(x.tobytes()).hexdigest()


@pytest.mark.parametrize("seed", sorted(GOLDEN))
def test_original_score_is_unchanged(seed):
    assert sha(soundtrack.render(12, seed=seed)) == GOLDEN[seed]


@pytest.mark.parametrize("name", sorted(soundtrack.STYLES))
def test_preset_round_trips_through_json(name):
    s = json.loads(json.dumps(soundtrack.settings(name, seed=3)))
    assert s["seed"] == 3
    assert set(s) == soundtrack.SETTING_KEYS | {"seed"}
    a = soundtrack.render(10, seed=3, style=name)
    b = soundtrack.render(10, seed=3, style=s)
    assert np.array_equal(a, b)


def test_settings_seed_is_used_when_render_gets_no_seed():
    s = soundtrack.settings("original", seed=31)
    assert sha(soundtrack.render(12, style=s)) == GOLDEN[31]


def test_unknown_or_missing_keys_are_rejected():
    s = soundtrack.settings("original")
    with pytest.raises(ValueError, match="unknown"):
        soundtrack.validate({**s, "bogus": 1})
    del s["prog"]
    with pytest.raises(ValueError, match="missing"):
        soundtrack.validate(s)


def test_cli_dump_and_config(tmp_path):
    out = subprocess.run([sys.executable, "soundtrack.py", "--dump", "di_moonlit", "--seed", "41"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    assert json.loads(out) == json.loads(json.dumps(soundtrack.settings("di_moonlit", seed=41)))
    cfg = tmp_path / "score.json"
    cfg.write_text(out)
    wav = tmp_path / "s.wav"
    subprocess.run([sys.executable, "soundtrack.py", "--config", str(cfg), "--seconds", "6", "-o", str(wav)],
                   cwd=ROOT, check=True, capture_output=True)
    with wave.open(str(wav)) as w:
        got = np.frombuffer(w.readframes(w.getnframes()), "<i2")
    want = (np.clip(soundtrack.render(6, seed=41, style="di_moonlit"), -1, 1) * 32767).astype("<i2").ravel()
    assert np.array_equal(got, want)
