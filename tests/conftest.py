import json, os, sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "capture")]

SHOTS = '''from shotlist import static, move
SHOTS = [
    static("t_one", (0, 0, 5), (10, 0, 5), secs=60),
    move("t_two", 70, [((0, 0, 5), (10, 0, 5)), ((5, 0, 5), (10, 0, 5))]),
]
'''


@pytest.fixture
def maproot(tmp_path):
    """A maps/ folder holding one valid map, 'testmap'."""
    import soundtrack
    d = tmp_path / "testmap"
    d.mkdir()
    (d / "map.json").write_text(json.dumps(dict(game="ce", strip=True, load_wait=35, output="test_1h",
                                                sheet=None, sheet_approved=None)))
    (d / "score.json").write_text(json.dumps(soundtrack.settings("original", seed=7)))
    (d / "glitch.json").write_text(json.dumps(dict(minutes=1, seed=7, calm=True, min_seg=45, max_seg=90,
                                                   mosh=2.5, bloom=0.3, tear=1.0, soft_tears=6)))
    (d / "shots.py").write_text(SHOTS)
    return tmp_path
