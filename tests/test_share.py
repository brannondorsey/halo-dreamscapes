"""share.sh uploads to Filebin (a fresh random bin per run) and prints one download link per file."""
import os, subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fake_curl(tmp_path, status="201"):
    bin_ = tmp_path / "bin"; bin_.mkdir()
    log = tmp_path / "curl.log"
    (bin_ / "curl").write_text(f"""#!/bin/bash
echo "$@" >> {log}
for a in "$@"; do case $a in -w) want=1;; *) [ -n "$want" ] && {{ echo -n {status}; want=; }};; esac; done
exit 0
""")
    (bin_ / "curl").chmod(0o755)
    return dict(os.environ, PATH=f"{bin_}:{os.environ['PATH']}"), log


def test_share_uploads_to_filebin(tmp_path):
    f = tmp_path / "cut one.mp4"; f.write_bytes(b"x" * 2000)
    env, log = fake_curl(tmp_path)
    out = subprocess.run([os.path.join(HERE, "share.sh"), str(f)], env=env, capture_output=True, text=True, check=True).stdout
    url = out.split()[0]
    assert url.startswith("https://filebin.net/") and url.endswith("/cut%20one.mp4")
    assert len(url.split("/")[3]) >= 16          # unguessable bin name
    assert "--data-binary" in log.read_text() and url in log.read_text()


def test_share_fails_when_upload_fails(tmp_path):
    f = tmp_path / "a.mp4"; f.write_bytes(b"x")
    env, _ = fake_curl(tmp_path, status="500")
    r = subprocess.run([os.path.join(HERE, "share.sh"), str(f)], env=dict(env, SHARE_RETRY_WAIT="0"), capture_output=True, text=True)
    assert r.returncode != 0 and "https://" not in r.stdout
