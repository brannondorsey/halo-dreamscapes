#!/usr/bin/env python3
"""Film and render maps' one-hour cuts from their maps/<name>/ folders, recording what each render used.

    ./render.py deathisland               # film missing shots (QC'd), render cuts/<output>.mp4, write a record
    ./render.py deathisland --no-film     # render from the captures already in $HALO_DIR/caps
    ./render.py deathisland --share       # also upload with share.sh and keep the link in the record
    ./render.py --share-record maps/deathisland/renders/<stamp>.json   # upload later (e.g. after a failed upload)
    ./render.py --replay maps/deathisland/renders/<stamp>.json [-o again.mp4] [--caps DIR]
                                          # re-render with the recorded settings, report what still matches

Each render writes maps/<name>/renders/<UTC stamp>.json: git commit (+ dirty flag), the full map, score,
glitch and shot-list settings, tool versions, sha256 of every capture and of the output, and the link.
Commit the record. Filming needs run.sh up with Chimera + rig.lua; get the contact sheet approved first.
"""
import argparse, datetime, hashlib, json, os, platform, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import maps  # noqa: E402


def run(cmd, **kw):
    if cmd[0].endswith(".py"):
        cmd = [sys.executable, *cmd]      # same interpreter (the venv with a working scipy)
    return subprocess.run(cmd, check=True, **kw)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def film(m, halo):
    env = {**os.environ, "HALO_DIR": halo, "MAPS_DIR": os.path.dirname(m["dir"])}
    cap = os.path.join(HERE, "capture")
    run([os.path.join(cap, "setup.sh"), m["name"]], env=env)
    run([os.path.join(cap, "shotlist.py"), m["shots_path"], "run"], env=env)
    run([os.path.join(cap, "shot.sh"), ""], env=env)


def glitch_cmd(m, caps, out, glitch_path=None, score_path=None):
    return [os.path.join(HERE, "glitch.py"), *caps, "--config", glitch_path or m["glitch_path"],
            "--score", score_path or m["score_path"], "-o", out]


def versions():
    import numpy, scipy
    ff = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout.split("\n")[0]
    return dict(python=platform.python_version(), numpy=numpy.__version__, scipy=scipy.__version__, ffmpeg=ff)


def git(*a):
    return subprocess.run(["git", *a], cwd=HERE, capture_output=True, text=True).stdout.strip()


def record(m, caps, out, link=None):
    with open(m["shots_path"]) as f:
        shots = f.read()
    rec = dict(map=m["name"], created=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
               commit=git("rev-parse", "HEAD"), dirty=bool(git("status", "--porcelain")),
               settings=dict(map=m["map"], score=m["score"], glitch=m["glitch"], shots=shots),
               versions=versions(),
               captures=[dict(name=os.path.basename(c), bytes=os.path.getsize(c), sha256=sha256(c)) for c in caps],
               output=dict(file=os.path.basename(out), bytes=os.path.getsize(out), sha256=sha256(out)),
               link=link)
    d = os.path.join(m["dir"], "renders")
    os.makedirs(d, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
    path, k = os.path.join(d, stamp + ".json"), 1
    while os.path.exists(path):
        path, k = os.path.join(d, f"{stamp}-{k}.json"), k + 1
    with open(path, "w") as f:
        json.dump(rec, f, indent=2)
        f.write("\n")
    return path


def replay(rec_path, caps_dir, out):
    with open(rec_path) as f:
        rec = json.load(f)
    if rec["commit"] != git("rev-parse", "HEAD"):
        print(f"note: recorded at commit {rec['commit'][:10]}; `git checkout` it for an exact replay")
    caps = [os.path.join(caps_dir, c["name"]) for c in rec["captures"]]
    caps_match = all(os.path.exists(p) and sha256(p) == c["sha256"] for p, c in zip(caps, rec["captures"]))
    tmp = tempfile.mkdtemp(prefix="replay-")
    paths = {}
    for k in ("glitch", "score"):
        paths[k] = os.path.join(tmp, k + ".json")
        with open(paths[k], "w") as f:
            json.dump(rec["settings"][k], f)
    run(glitch_cmd(None, caps, out, paths["glitch"], paths["score"]))
    return dict(captures_match=caps_match, output_match=sha256(out) == rec["output"]["sha256"])


def share(path):
    out = subprocess.run([os.path.join(HERE, "share.sh"), path], capture_output=True, text=True, check=True).stdout
    return next(w for w in out.split() if w.startswith("https://"))


def finish(m, caps, out, share=False):
    """Write the render's record, then (optionally) upload; a failed upload keeps the record, link null."""
    rec = record(m, caps, out)
    if share:
        try:
            share_record(rec, os.path.dirname(out))
        except subprocess.CalledProcessError:
            print(f"upload failed; retry later with ./render.py --share-record {os.path.relpath(rec, HERE)}")
    return rec


def share_record(rec_path, cuts_dir=None):
    """Upload a record's output (it must still be the recorded file) and store the link in the record."""
    with open(rec_path) as f:
        rec = json.load(f)
    out = os.path.join(cuts_dir or os.path.join(HERE, "cuts"), rec["output"]["file"])
    if sha256(out) != rec["output"]["sha256"]:
        raise ValueError(f"{out} has changed since the render (sha256 differs); not sharing it under this record")
    rec["link"] = share(out)
    with open(rec_path, "w") as f:
        json.dump(rec, f, indent=2)
        f.write("\n")
    print("link:", rec["link"])
    return rec["link"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("maps", nargs="*")
    ap.add_argument("--no-film", action="store_true")
    ap.add_argument("--share", action="store_true")
    ap.add_argument("--replay", metavar="RECORD")
    ap.add_argument("--share-record", metavar="RECORD", help="upload a past render's cut and add the link to its record")
    ap.add_argument("--caps", help="--replay: capture folder (default: $HALO_DIR/caps for the record's map)")
    ap.add_argument("-o", "--out", help="--replay: output file")
    o = ap.parse_args()
    if o.share_record:
        share_record(o.share_record)
        return
    if o.replay:
        with open(o.replay) as f:
            name = json.load(f)["map"]
        caps_dir = o.caps or os.path.join(maps.halo_dir(maps.load(name)), "caps")
        out = o.out or os.path.join(HERE, "cuts", f"{name}_replay.mp4")
        res = replay(o.replay, caps_dir, out)
        print(f"{out}: captures {'match' if res['captures_match'] else 'DIFFER'}, "
              f"output {'identical' if res['output_match'] else 'differs'}")
        return
    if not o.maps:
        ap.error("name at least one map (./maps.py list)")
    for name in o.maps:
        m = maps.load(name)
        if not m["map"]["sheet_approved"]:
            sys.exit(f"{name}: no sheet_approved in map.json; get the owner's approval of the contact sheet first")
        halo = maps.halo_dir(m)
        if not o.no_film:
            film(m, halo)
        caps = maps.caps(m, halo)
        missing = [c for c in caps if not os.path.exists(c)]
        if missing:
            sys.exit(f"{name}: {len(missing)} captures missing, e.g. {missing[0]}")
        os.makedirs(os.path.join(HERE, "cuts"), exist_ok=True)
        out = os.path.join(HERE, "cuts", m["map"]["output"] + ".mp4")
        run(glitch_cmd(m, caps, out))
        print("record:", finish(m, caps, out, o.share))


if __name__ == "__main__":
    main()
