#!/usr/bin/env python3
"""Cut clips into one long, glitched, CRT-ready loop with a generated score.

    ./glitch.py clips/*.mp4 -o loop.mp4 --minutes 20

Glitches are real bitstream damage plus scan-timing faults:
  mosh   cut to the next shot without its keyframe: new motion drags old pixels
  bloom  one P-frame repeated: whatever moved keeps smearing outward
  tear   vsync tear: the lower part of the screen lags/slips horizontally
  roll   vertical hold loss: the picture rolls through a black blanking bar
The score (soundtrack.py) freezes, stutters, bitcrushes and tape-stops in sync.
Needs ffmpeg, numpy and scipy.
"""
import argparse, json, os, random, shutil, subprocess, sys, tempfile
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soundtrack  # noqa: E402

W, H, FPS = 640, 480, 30
FIT = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}")
VOP, GOV = b"\x00\x00\x01\xb6", b"\x00\x00\x01\xb3"


def run(*args, **kw):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True, **kw)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True)
    return float(json.loads(out.stdout)["format"]["duration"])


# --- bitstream ---------------------------------------------------------------

def encode_m4v(src, start, length, out, keyframes=(), q=3):
    """MPEG-4 part 2, no B-frames, one keyframe at the head plus any requested."""
    kf = ",".join(f"{k:.3f}" for k in [0.0, *keyframes])
    run("-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", src, "-an", "-vf", FIT,
        "-c:v", "mpeg4", "-q:v", str(q), "-bf", "0", "-g", "100000", "-sc_threshold", "1000000000",
        "-force_key_frames", kf, "-f", "m4v", out)


def split_vops(data):
    """-> (header bytes, [vop bytes...]); GOV headers are dropped."""
    starts = []
    i = data.find(VOP)
    head = data[:i] if i >= 0 else data
    g = head.find(GOV)
    if g >= 0:
        head = head[:g]
    while i >= 0:
        starts.append(i)
        i = data.find(VOP, i + 4)
    vops = []
    for k, s in enumerate(starts):
        e = starts[k + 1] if k + 1 < len(starts) else len(data)
        chunk = data[s:e]
        g = chunk.find(GOV, 4)
        vops.append(chunk[:g] if g >= 0 else chunk)
    return head, vops


def vop_type(v):
    return "IPBS"[v[4] >> 6]


# --- planning ----------------------------------------------------------------

def plan(sources, lens, total, r, o):
    """Sequence of segments with transitions and in-segment events."""
    segs, t, last, bag = [], 0.0, None, []
    while t < total:
        if o.calm:
            # shuffle-bag: every shot plays once before any repeats
            if not bag:
                bag = [s for s in sources]
                r.shuffle(bag)
                if bag[0] == last and len(bag) > 1:
                    bag.append(bag.pop(0))
            src = bag.pop(0)
        else:
            pool = [s for s in sources if s != last] or sources
            # prefer a different location prefix (canyon_/beach_/...) than the last shot
            loc = lambda s: os.path.basename(s).split("_")[0]
            other = [s for s in pool if last is None or loc(s) != loc(last)]
            src = r.choice(other if other and r.random() < 0.75 else pool)
        ln = min(r.uniform(o.min_seg, o.max_seg), lens[src] - 0.1)
        start = r.uniform(0, max(0.0, lens[src] - ln - 0.05))
        kinds = ["mosh", "cut"] if o.calm else ["mosh", "tear", "cut"]
        weights = [o.mosh, 1.0] if o.calm else [o.mosh, o.tear, 1.0]
        into = "cut" if not segs else r.choices(kinds, weights)[0]
        seg = dict(src=src, start=start, len=ln, into=into, events=[])
        if into == "mosh":
            seg["heal"] = (r.uniform(3.0, min(ln - 1.0, 7.0)) if o.calm   # keyframe that ends the mosh
                           else r.uniform(1.2, min(ln - 0.3, 5.5)))
        if r.random() < o.bloom:
            b0 = r.uniform(0.6, ln - 1.0)
            seg["bloom"] = (b0, r.randint(10, 24) if o.calm else r.randint(8, 40))   # (at, repeats)
        for _ in range(np.random.default_rng(r.randint(0, 1 << 30)).poisson(o.tear * ln / 6)):
            if o.calm:
                seg["events"].append((r.uniform(0, ln), r.uniform(0.4, 1.0), "softtear"))
            else:
                seg["events"].append((r.uniform(0, ln), r.uniform(0.25, 1.6), r.choice(["tear", "tear", "slip", "roll"])))
        segs.append(seg)
        t += ln
        last = src
    return segs


# --- scan-timing glitches ----------------------------------------------------

class Scan:
    """Per-frame CRT/vsync faults applied to decoded RGB frames."""

    def __init__(self, r):
        self.r = r
        self.hist = []
        self.dx = 0.0

    def tear(self, f, k, n):
        r = self.r
        prev = self.hist[-min(len(self.hist), r.randint(1, 4))] if self.hist else f
        out = f.copy()
        y = int((H * (k / max(n, 1)) * r.uniform(0.8, 2.5) + r.randint(0, H)) % H)
        self.dx = np.clip(self.dx + r.uniform(-18, 18), -90, 90)
        lower = np.roll(prev[y:], int(self.dx), axis=1)
        out[y:] = lower
        if r.random() < 0.6:
            y2 = r.randint(0, H - 1)
            out[y2:] = np.roll(out[y2:], r.randint(-40, 40), axis=1)
        out[max(0, y - 1):y + 1] = np.clip(out[max(0, y - 1):y + 1].astype(np.int16) + 70, 0, 255)
        return out

    def softtear(self, f, k, n):
        """Gentle vsync tear: one line drifting down, lower field one frame late, small slip."""
        if k == 0:
            self.y0, self.sdx = self.r.randint(H // 5, H - H // 4), self.r.choice([-1, 1]) * self.r.randint(8, 24)
        prev = self.hist[-1] if self.hist else f
        y = int(self.y0 + k * 3) % H
        out = f.copy()
        dx = int(self.sdx * np.sin(np.pi * k / max(n, 1)))      # eases in and out
        out[y:] = np.roll(prev[y:], dx, axis=1)
        return out

    def slip(self, f, k, n):
        r, out = self.r, f.copy()
        for _ in range(r.randint(3, 10)):
            y, h = r.randint(0, H - 4), r.randint(3, 60)
            dx = r.randint(-120, 120)
            band = np.roll(out[y:y + h], dx, axis=1)
            band[..., 0] = np.roll(band[..., 0], r.randint(4, 14), axis=1)
            band[..., 2] = np.roll(band[..., 2], -r.randint(4, 14), axis=1)
            out[y:y + h] = band
        return out

    def roll(self, f, k, n):
        p = (k / max(n, 1))
        off = int((p ** 1.6) * H * self.r.choice([1, 1, 2])) % H
        out = np.roll(f, off, axis=0)
        bar = 28
        b0 = off - bar // 2
        for yy in range(b0, b0 + bar):
            out[yy % H] = 0
        # hsync wobble near the bar
        for yy in range(b0 + bar, b0 + bar + 40):
            out[yy % H] = np.roll(out[yy % H], int(12 * np.sin(yy * 0.4)), axis=0)
        return out

    def __call__(self, f, active):
        for kind, k, n in active:
            f = getattr(self, kind)(f, k, n)
        self.hist.append(f)
        if len(self.hist) > 6:
            self.hist.pop(0)
        return f


# --- main --------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="+")
    ap.add_argument("-o", "--out", default="loop.mp4")
    ap.add_argument("--minutes", type=float, default=20)
    ap.add_argument("--min-seg", type=float, default=5)
    ap.add_argument("--max-seg", type=float, default=12)
    ap.add_argument("--mosh", type=float, default=1.6, help="weight of moshed transitions vs clean cuts (1.0)")
    ap.add_argument("--tear", type=float, default=1.0, help="tear/roll bursts per ~6s of footage")
    ap.add_argument("--bloom", type=float, default=0.35, help="chance a segment gets a P-frame bloom")
    ap.add_argument("--cards", default="", help="'|'-separated bumper text, shown every --card-every segments")
    ap.add_argument("--card-every", type=int, default=10)
    ap.add_argument("--mute", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--calm", action="store_true",
                    help="long-form preset: 45-90s shots, mosh/cut transitions only, gentle blooms and soft tears, "
                         "no slips/rolls, no repeats until every shot has played")
    o = ap.parse_args()
    if o.calm:
        for k, v in (("min_seg", 45), ("max_seg", 90), ("mosh", 2.5), ("tear", 0.02), ("bloom", 0.3)):
            if getattr(o, k) == ap.get_default(k):
                setattr(o, k, v)

    r = random.Random(o.seed)
    tmp = tempfile.mkdtemp(prefix="halo-crt-")
    try:
        sources = list(o.sources)
        cards = [c.strip() for c in o.cards.split("|") if c.strip()]
        card_files = [make_card(c, os.path.join(tmp, f"card{i}.mp4")) for i, c in enumerate(cards)]
        lens = {s: duration(s) for s in sources + card_files}
        segs = plan(sources, lens, o.minutes * 60, r, o)
        if card_files:
            for i in range(o.card_every, len(segs), o.card_every):
                c = r.choice(card_files)
                segs[i] = dict(src=c, start=0, len=lens[c] - 0.1, into=r.choice(["mosh", "tear"]),
                               heal=1.0, events=[(0.3, 0.8, "slip")])

        render(segs, o.out, tmp, r, o.seed, o.mute)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def render(segs, out, tmp, r, seed=0, mute=False):
    """Splice segments into one bitstream, score it, apply scan faults, encode to out.
    A segment dict: src, start, len, into (cut|mosh|tear), optional heal, bloom (at, repeats),
    events [(at, dur, tear|slip|roll)] and label (title, subtitle) drawn while it plays."""
    # 1. encode + splice the bitstream
    header, stream, frame_events, audio_events, fi, labels = None, [], [], [], 0, []
    for i, s in enumerate(segs):
        m4v = os.path.join(tmp, f"s{i:04d}.m4v")
        encode_m4v(s["src"], s["start"], s["len"], m4v, [s["heal"]] if "heal" in s else [])
        head, vops = split_vops(open(m4v, "rb").read())
        header = header or head
        seg_start = fi
        out_vops = []
        for k, v in enumerate(vops):
            is_i = vop_type(v) == "I"
            if is_i and k == 0 and s["into"] == "mosh":
                continue                                   # the mosh: lose the keyframe
            out_vops.append(v)
            if "bloom" in s and k == int(s["bloom"][0] * FPS) and not is_i:
                out_vops += [v] * s["bloom"][1]
                audio_events.append(((seg_start + len(out_vops) - s["bloom"][1]) / FPS, s["bloom"][1] / FPS, "bloom"))
        stream += out_vops
        n = len(out_vops)
        if s["into"] == "mosh":
            audio_events.append((seg_start / FPS, s.get("heal", 2.0), "mosh"))
        elif s["into"] == "tear":
            frame_events.append((seg_start - 4, 14, "tear"))
            audio_events.append(((seg_start - 4) / FPS, 14 / FPS, "tear"))
        for at, d, kind in s["events"]:
            f0, fn = seg_start + int(at * FPS), int(d * FPS)
            frame_events.append((f0, fn, kind))
            audio_events.append((f0 / FPS, fn / FPS, {"slip": "tear", "softtear": "soft"}.get(kind, kind)))
        labels.append((seg_start, fi + n, s.get("label")))
        fi += n
        print(f"[{fi / FPS / 60:5.1f} min] {os.path.basename(s['src']):<26} {s['into']:<5}"
              f"{' bloom' if 'bloom' in s else ''}{' +' + str(len(s['events'])) + ' scan' if s['events'] else ''}", flush=True)
    total_frames = len(stream)
    joined = os.path.join(tmp, "joined.m4v")
    with open(joined, "wb") as f:
        f.write(header)
        for v in stream:
            f.write(v)

    # 2. score
    wav = None
    if not mute:
        print("scoring...", flush=True)
        wav = os.path.join(tmp, "score.wav")
        soundtrack.write_wav(wav, soundtrack.render(total_frames / FPS, audio_events, seed=seed))

    # 3. decode -> scan faults -> encode
    print("rendering...", flush=True)
    active_at = [[] for _ in range(total_frames)]
    for f0, fn, kind in frame_events:
        for k in range(max(0, fn)):
            if 0 <= f0 + k < total_frames:
                active_at[f0 + k].append((kind, k, fn))
    dec = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "quiet", "-err_detect", "ignore_err",
                            "-f", "m4v", "-r", str(FPS), "-i", joined, "-vf", "setpts=N/(30*TB)",
                            "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            *(["-i", wav] if wav else []), "-map", "0:v", *(["-map", "1:a"] if wav else []),
                            *label_filter(labels), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                            "-g", str(FPS * 2), *(["-c:a", "aac", "-b:a", "192k"] if wav else []),
                            "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    scan, size, k = Scan(r), W * H * 3, 0
    while True:
        buf = dec.stdout.read(size)
        if len(buf) < size:
            break
        f = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        f = scan(f, active_at[k] if k < total_frames else [])
        enc.stdin.write(np.ascontiguousarray(f).tobytes())
        k += 1
    enc.stdin.close(); enc.wait(); dec.wait()
    print(f"wrote {out}: {k} frames ({k / FPS / 60:.1f} min), {len(audio_events)} glitch events")


def label_filter(labels):
    """drawtext chain for segments carrying a (title, subtitle) label."""
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
    parts = []
    for f0, f1, lab in labels:
        if not lab:
            continue
        en = f"enable='between(n\\,{f0}\\,{f1 - 1})'"
        for i, (txt, size, y) in enumerate(((lab[0], 30, 18), (lab[1], 16, 56))):
            esc = txt.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\u2019").replace(",", "\\,")
            parts.append(f"drawtext=fontfile={font}:text='{esc}':fontsize={size}:fontcolor=white:"
                         f"box=1:boxcolor=black@0.7:boxborderw=6:x=18:y={y}:{en}")
    return ["-vf", ",".join(parts)] if parts else []


def make_card(text, out, secs=4.0):
    """Green-on-black interstitial with a slow scanning cursor."""
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
    esc = text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’")
    vf = (f"drawtext=fontfile={font}:text='{esc}':fontsize=40:fontcolor=0x7CFF9A:x=(w-tw)/2:y=(h-th)/2,"
          f"drawbox=x=0:y=mod(t*160\\,{H}):w={W}:h=2:color=0x7CFF9A@0.25:t=fill,format=yuv420p")
    run("-f", "lavfi", "-i", f"color=c=0x030806:s={W}x{H}:r={FPS}:d={secs}", "-vf", vf,
        "-c:v", "libx264", "-crf", "16", out)
    return out


if __name__ == "__main__":
    sys.exit(main())
