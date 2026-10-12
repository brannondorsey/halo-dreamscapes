#!/usr/bin/env python3
"""Generative ambient score: monk choir, drones, soft synth arps, cathedral reverb.

Original material in the spirit of early-2000s sci-fi shooter soundtracks (no
quoted melodies). glitch.py calls render(); run standalone to audition:

    ./soundtrack.py -o score.wav --seconds 180 --seed 1 [--style di_moonlit | --config maps/X/score.json]
    ./soundtrack.py --dump di_moonlit --seed 41 > maps/deathisland/score.json   # adopt a preset
"""
import argparse, json, re, wave
import numpy as np
from scipy import signal

SR = 44100
rng = np.random.default_rng()


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def env(n, a, r, sustain=1.0):
    """Linear-in, cosine-out envelope of n samples, attack a / release r seconds."""
    e = np.full(n, sustain, np.float32)
    A, R = min(int(a * SR), n // 2), min(int(r * SR), n // 2)
    e[:A] = np.linspace(0, sustain, A, dtype=np.float32)
    e[n - R:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, R))).astype(np.float32)
    return e


def osc(freq, n, kind="saw", vib=0.0, vib_rate=5.0, drift=0.0):
    t = np.arange(n, dtype=np.float32) / SR
    f = freq * (1 + vib * np.sin(2 * np.pi * vib_rate * t + rng.uniform(0, 6)) + drift * np.sin(2 * np.pi * 0.13 * t + rng.uniform(0, 6)))
    ph = np.cumsum(f / SR) + rng.uniform(0, 1)
    ph = ph - np.floor(ph)
    if kind == "saw":
        return (2 * ph - 1).astype(np.float32)
    if kind == "square":
        return np.where(ph < 0.5, 1.0, -1.0).astype(np.float32)
    if kind == "tri":
        return (4 * np.abs(ph - 0.5) - 1).astype(np.float32)
    return np.sin(2 * np.pi * ph).astype(np.float32)


def lowpass(x, fc, order=2):
    b, a = signal.butter(order, min(fc, SR * 0.45) / (SR / 2))
    return signal.lfilter(b, a, x).astype(np.float32)


def resonators(x, formants):
    """Parallel band-pass formant bank (vowel colour)."""
    out = np.zeros_like(x)
    for f, bw, g in formants:
        b, a = signal.iirpeak(f, f / bw, SR)
        out += g * signal.lfilter(b, a, x).astype(np.float32)
    return out


VOWEL_OO = [(320, 80, 1.0), (800, 90, 0.5), (2300, 120, 0.12)]
VOWEL_AH = [(650, 90, 1.0), (1100, 100, 0.55), (2500, 130, 0.15)]


def add(buf, x, at):
    at = max(0, at)
    end = min(len(buf), at + len(x))
    if end > at:
        buf[at:end] += x[: end - at]


# Original harmony: D minor/dorian. Chords as MIDI note lists (low voices).
PROG = [
    [38, 50, 57, 62, 65],   # Dm
    [34, 46, 53, 58, 62],   # Bb
    [41, 48, 57, 60, 65],   # F
    [36, 48, 55, 60, 64],   # C
    [38, 50, 57, 62, 65],   # Dm
    [43, 50, 55, 58, 62],   # Gm
    [34, 46, 53, 58, 65],   # Bb
    [33, 45, 52, 57, 61],   # A
]
# Original chant phrases (MIDI, tonic D = 62), each note held ~1-3 beats.
CHANT = [
    [(62, 2), (65, 1), (67, 1), (69, 3), (67, 1), (65, 2), (64, 2), (62, 4)],
    [(69, 2), (72, 2), (70, 1), (69, 1), (67, 2), (69, 4), (65, 2), (67, 2)],
    [(62, 3), (60, 1), (62, 2), (65, 2), (64, 2), (62, 2), (57, 4)],
    [(65, 2), (67, 2), (69, 2), (70, 2), (69, 3), (67, 1), (65, 2), (62, 4)],
]
VOWEL_OH = [(450, 80, 1.0), (850, 90, 0.45), (2600, 130, 0.1)]
VOWEL_EE = [(300, 70, 1.0), (2100, 140, 0.35), (2900, 160, 0.15)]

# Scales as semitones above the tonic (for re-moding the chant phrases).
DORIAN, AEOLIAN, LYDIAN = [0, 2, 3, 5, 7, 9, 10], [0, 2, 3, 5, 7, 8, 10], [0, 2, 4, 6, 7, 9, 11]
MIXOLYDIAN, PHRYGIAN = [0, 2, 4, 5, 7, 9, 10], [0, 1, 3, 5, 7, 8, 10]


def chord(root, q):
    """Low voicing like PROG's: bass, octave, fifth, 2nd octave, third (q: m, M or s = sus2)."""
    r = 33 + (root - 33) % 12            # bass between A1 and G#2
    top = {"m": 3, "M": 4, "s": 2}[q]
    return [r, r + 12, r + 19, r + 24, r + 24 + top]


def prog(tonic, steps):
    """steps: (semitones above tonic, quality) pairs."""
    return [chord(tonic + off, q) for off, q in steps]


def chants(tonic, scale):
    """The original chant contours, mapped degree-for-degree onto another tonic and mode."""
    out = []
    for phrase in CHANT:
        p = []
        for note, beats in phrase:
            off = note - 62
            octv, semi = divmod(off, 12)
            deg = min(range(7), key=lambda i: abs(DORIAN[i] - semi))
            p.append((60 + tonic % 12 + 12 * octv + scale[deg] - (12 if tonic % 12 > 7 else 0), beats))
        out.append(p)
    return out


# Per-map scores: one engine, each map with its own key, harmony, pace and balance. "original" is the
# score Silent Cartographer and Blood Gulch first shipped with. Keys: chord_len (s), layer odds
# (choir/chant/pad/arp per 8-chord section), gain per bus, choir vowels, arp waveform/octave,
# boom odds, air (wind level, cutoff Hz), surf (sea swell level), hall (seconds, wet).
BASE = dict(prog=PROG, chants=CHANT, chord_len=7.5,
            odds=dict(choir=0.8, chant=0.55, pad=0.85, arp=0.45),
            gain=dict(choir=1.3, chant=1.4, pad=0.9, sub=0.6, arp=0.9, air=1.0, boom=1.0),
            vowels=(VOWEL_OO, VOWEL_AH), arp_wave="square", arp_oct=12, boom=1.0,
            air=(1.0, 700), surf=0.0, hall=(5.0, 0.55))
STYLES = {
    "original": {},
    # Silent Cartographer: tropical island, open sea, Forerunner halls underneath.
    "sc_tide": dict(chord_len=9.0, surf=1.0, odds=dict(choir=0.7, chant=0.4, pad=0.95, arp=0.35),
                    gain=dict(choir=1.0, chant=1.2, pad=1.1, sub=0.6, arp=0.8, air=0.8, boom=0.8)),
    "sc_cartographer": dict(prog=prog(39, [(0, "M"), (2, "M"), (-3, "m"), (-5, "M"), (0, "M"), (7, "s"),
                                           (2, "M"), (-5, "s")]),
                            chants=chants(51, LYDIAN), chord_len=7.0, arp_wave="tri",
                            odds=dict(choir=0.75, chant=0.5, pad=0.85, arp=0.7),
                            gain=dict(choir=1.2, chant=1.2, pad=0.9, sub=0.5, arp=1.1, air=0.7, boom=0.7),
                            vowels=(VOWEL_OH, VOWEL_AH), surf=0.5),
    "sc_shrine": dict(prog=prog(45, [(0, "m"), (-4, "M"), (0, "m"), (-2, "M"), (0, "m"), (5, "m"),
                                     (-4, "M"), (-5, "M")]),
                      chants=chants(57, AEOLIAN), chord_len=10.0,
                      odds=dict(choir=0.9, chant=0.85, pad=0.6, arp=0.15),
                      gain=dict(choir=1.4, chant=1.6, pad=0.7, sub=0.8, arp=0.7, air=0.8, boom=1.1),
                      hall=(7.0, 0.65)),
    # Blood Gulch: dry box canyon, wind, long afternoon.
    "bg_canyon": dict(prog=prog(36, [(0, "m"), (-4, "M"), (-2, "M"), (0, "m"), (5, "m"), (-4, "M"),
                                     (-2, "s"), (0, "s")]),
                      chants=chants(48, AEOLIAN), chord_len=9.0, air=(2.6, 1100), boom=1.4,
                      odds=dict(choir=0.65, chant=0.45, pad=0.8, arp=0.3),
                      gain=dict(choir=1.1, chant=1.3, pad=0.9, sub=0.8, arp=0.8, air=1.0, boom=1.2)),
    "bg_dust": dict(prog=prog(43, [(0, "M"), (-2, "M"), (5, "M"), (0, "M"), (-5, "M"), (-2, "M"),
                                   (5, "s"), (0, "s")]),
                    chants=chants(55, MIXOLYDIAN), chord_len=8.0, arp_wave="tri", arp_oct=0,
                    odds=dict(choir=0.6, chant=0.4, pad=0.95, arp=0.6),
                    gain=dict(choir=1.0, chant=1.2, pad=1.2, sub=0.6, arp=1.0, air=1.4, boom=0.8),
                    vowels=(VOWEL_OH, VOWEL_OO), air=(1.4, 900)),
    "bg_vigil": dict(prog=prog(40, [(0, "m"), (1, "M"), (0, "m"), (-2, "m"), (0, "m"), (1, "M"),
                                    (3, "M"), (1, "M")]),
                     chants=chants(52, PHRYGIAN), chord_len=8.5,
                     odds=dict(choir=0.9, chant=0.8, pad=0.7, arp=0.25),
                     gain=dict(choir=1.4, chant=1.6, pad=0.8, sub=0.7, arp=0.8, air=1.0, boom=1.1),
                     air=(1.8, 800)),
    # Death Island: night sea, moon, the ring overhead.
    "di_moonlit": dict(prog=prog(41, [(0, "M"), (2, "M"), (0, "M"), (-3, "m"), (0, "M"), (2, "M"),
                                      (7, "s"), (0, "s")]),
                       chants=chants(53, LYDIAN), chord_len=9.0, surf=1.2,
                       odds=dict(choir=0.5, chant=0.3, pad=0.95, arp=0.35),
                       gain=dict(choir=0.9, chant=1.0, pad=1.2, sub=0.5, arp=0.8, air=1.0, boom=0.6),
                       vowels=(VOWEL_OO, VOWEL_OH), air=(1.6, 900), hall=(6.0, 0.6)),
    "di_nightwatch": dict(prog=prog(34, [(0, "m"), (-4, "M"), (0, "m"), (3, "M"), (0, "m"), (-4, "M"),
                                         (-2, "M"), (0, "s")]),
                          chants=chants(46, AEOLIAN), chord_len=11.0, surf=0.8, boom=0.7,
                          odds=dict(choir=0.6, chant=0.35, pad=0.9, arp=0.2),
                          gain=dict(choir=1.1, chant=1.2, pad=1.0, sub=0.9, arp=0.7, air=1.2, boom=0.9),
                          hall=(7.5, 0.65)),
    "di_ringlight": dict(prog=prog(45, [(0, "m"), (-2, "M"), (-4, "M"), (-2, "M"), (0, "m"), (5, "M"),
                                        (3, "M"), (7, "M")]),
                         chants=chants(57, DORIAN), chord_len=7.5, arp_wave="tri", surf=0.6,
                         odds=dict(choir=0.8, chant=0.45, pad=0.8, arp=0.75),
                         gain=dict(choir=1.2, chant=1.2, pad=0.9, sub=0.5, arp=1.2, air=0.8, boom=0.7),
                         vowels=(VOWEL_EE, VOWEL_OO)),
}


SETTING_KEYS = set(BASE)


def style(name):
    st = {**BASE, **STYLES[name]}
    for k in ("odds", "gain"):
        st[k] = {**BASE[k], **STYLES[name].get(k, {})}
    return st


def settings(name, seed=None):
    """A preset expanded to the complete, JSON-ready settings a map's score.json stores."""
    s = json.loads(json.dumps(style(name)))
    if seed is not None:
        s["seed"] = seed
    return s


def validate(s):
    keys = set(s) - {"seed"}
    if keys - SETTING_KEYS:
        raise ValueError(f"unknown score settings: {sorted(keys - SETTING_KEYS)}")
    if SETTING_KEYS - keys:
        raise ValueError(f"missing score settings: {sorted(SETTING_KEYS - keys)}")
    return s


def load(path):
    with open(path) as f:
        return validate(json.load(f))


def dumps(s):
    """JSON with short lists kept on one line, so chord and chant tables stay readable."""
    one = lambda m: re.sub(r"\s+", " ", m.group()).replace("[ ", "[").replace(" ]", "]")
    out = re.sub(r"\[[^\[\]{}]*\]", one, json.dumps(s, indent=2))
    return re.sub(r"\[(\s*\[[^\[\]{}]*\],?)+\s*\]", lambda m: one(m) if len(one(m)) < 100 else m.group(), out)


def compose(seconds, seed, style_name="original"):
    """style_name: a STYLES preset or a full settings dict (see settings())."""
    global rng
    S = style(style_name) if isinstance(style_name, str) else validate(style_name)
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    bus = {k: np.zeros(n, np.float32) for k in ("choir", "chant", "pad", "sub", "arp", "air", "boom")}
    chord_len = S["chord_len"]
    beat = chord_len / 8
    odds, PR = S["odds"], S["prog"]
    # Sections of 8 chords; each turns layers on/off for an ebb-and-flow arrangement.
    t, ci, sec = 0.0, 0, 0
    while t < seconds:
        if ci % 8 == 0:
            sec += 1
            layers = {"choir": rng.random() < odds["choir"], "chant": rng.random() < odds["chant"] and sec > 1,
                      "pad": rng.random() < odds["pad"], "arp": rng.random() < odds["arp"], "sub": True}
            if S["boom"] >= 1 or rng.random() < S["boom"]:
                add(bus["boom"], boom(), int(t * SR))
        chord = PR[ci % len(PR)]
        L = int((chord_len + 2.5) * SR)
        at = int(t * SR)
        if layers["choir"]:
            for note in chord[1:]:
                for d in (-0.06, 0.0, 0.07):
                    v = osc(midi(note + d), L, "saw", vib=0.004, vib_rate=4.6 + rng.random(), drift=0.002)
                    add(bus["choir"], v * env(L, 2.2, 3.0) * 0.08, at)
        if layers["pad"]:
            for note in chord[:4]:
                for d in (-0.1, 0.1):
                    v = osc(midi(note + 12 + d), L, "saw", drift=0.003)
                    add(bus["pad"], v * env(L, 3.0, 3.0) * 0.05, at)
        if layers["sub"]:
            add(bus["sub"], osc(midi(chord[0] - 12 if chord[0] > 36 else chord[0]), L, "sine") * env(L, 2.5, 3.0) * 0.35, at)
        if layers["arp"]:
            pat = [chord[2], chord[3], chord[4], chord[3] + 12, chord[4], chord[3], chord[2] + 12, chord[4]]
            for k in range(16):
                nl = int(0.9 * SR)
                note = pat[k % 8] + S["arp_oct"]
                v = osc(midi(note), nl, S["arp_wave"]) * np.exp(-np.arange(nl) / (0.18 * SR)).astype(np.float32)
                add(bus["arp"], lowpass(v, 1800 + 1200 * np.sin(t * 0.2 + k)) * 0.05, at + int(k * beat / 2 * SR))
        if layers["chant"] and ci % 8 in (0, 4):
            phrase = S["chants"][rng.integers(len(S["chants"]))]
            pt = at
            for note, beats in phrase:
                nl = int((beats * beat + 0.4) * SR)
                for oct_, gain in ((0, 0.11), (-12, 0.07)):
                    for d in (-0.05, 0.05):
                        v = osc(midi(note + oct_ + d), nl, "saw", vib=0.006, vib_rate=5.2)
                        add(bus["chant"], v * env(nl, 0.25, 0.4) * gain, pt)
                pt += int(beats * beat * SR)
        t += chord_len
        ci += 1
    # wind / air
    wn = rng.standard_normal(n).astype(np.float32)
    sweep = (0.5 + 0.5 * np.sin(2 * np.pi * np.arange(n) / SR / 23.0)).astype(np.float32)
    lvl, cut = S["air"]
    bus["air"] = lowpass(wn, cut) * (0.02 + 0.03 * sweep) * lvl
    if S["surf"]:
        bus["air"] += surf(n) * S["surf"]

    # colour each bus
    g, (v1, v2) = S["gain"], S["vowels"]
    choir = 0.6 * resonators(bus["choir"], v1) + 0.4 * resonators(bus["choir"], v2)
    chant = resonators(bus["chant"], VOWEL_AH) * 0.9 + resonators(bus["chant"], VOWEL_OO) * 0.5
    pad = lowpass(bus["pad"], 1400)
    arp = bus["arp"]
    dry = (choir * g["choir"] + chant * g["chant"] + pad * g["pad"] + bus["sub"] * g["sub"] + arp * g["arp"]
           + bus["air"] * g["air"] + bus["boom"] * g["boom"])
    st = np.stack([dry + 0.25 * arp, dry - 0.25 * arp], 1)
    st = hall(st, seed, *S["hall"])
    return st


def surf(n):
    """Slow, irregular sea swells: filtered noise under a wave-shaped envelope."""
    x = lowpass(rng.standard_normal(n).astype(np.float32), 900, 2)
    e = np.zeros(n, np.float32)
    t = 0
    while t < n:
        period = int(rng.uniform(6, 11) * SR)
        w = np.linspace(0, 1, period, dtype=np.float32)
        swell = (np.sin(np.pi * w ** 0.6) ** 2) * rng.uniform(0.5, 1.0)   # quick rise, long fall
        e[t:t + period] += swell[: n - t]
        t += int(period * 0.8)
    return x * e * 0.05


def boom():
    n = int(4 * SR)
    t = np.arange(n) / SR
    f = 38 + 50 * np.exp(-t * 6)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.4)
    x += lowpass(rng.standard_normal(n).astype(np.float32), 300) * np.exp(-t * 5) * 0.6
    return (x * 0.45).astype(np.float32)


def hall(st, seed, secs=5.0, wet=0.55):
    r = np.random.default_rng(seed + 99)
    n = int(secs * SR)
    t = np.arange(n) / SR
    out = np.empty_like(st)
    for ch in range(2):
        ir = r.standard_normal(n).astype(np.float32) * np.exp(-t * 6.9 / secs).astype(np.float32)
        ir = lowpass(ir, 5000)
        ir[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
        ir /= np.sqrt(np.sum(ir ** 2))
        out[:, ch] = (1 - wet) * st[:, ch] + wet * signal.oaconvolve(st[:, ch], ir)[: len(st)] * 0.9
    return out


# ---- glitches -----------------------------------------------------------------

def _xfade_loop(grain, n):
    """Repeat a grain to length n with short crossfades (a frozen buffer)."""
    g = len(grain)
    f = max(1, min(g // 4, int(0.01 * SR)))
    win = np.ones(g, np.float32); win[:f] = np.linspace(0, 1, f); win[-f:] = np.linspace(1, 0, f)
    out = np.zeros((n + g, grain.shape[1]), np.float32)
    step = g - f
    for i in range(0, n, step):
        out[i:i + g] += grain * win[:, None]
    return out[:n]


def apply_glitches(st, events, r):
    """events: list of (start_s, dur_s, kind). Mutates and returns st."""
    for start, dur, kind in events:
        a, n = int(start * SR), int(dur * SR)
        if a >= len(st) or n <= 0:
            continue
        n = min(n, len(st) - a)
        seg = st[a:a + n].copy()
        if kind == "mosh":
            # freeze a grain from the cut, sinking in pitch as it smears
            g = st[a:a + int(r.uniform(0.08, 0.22) * SR)]
            if len(g) < 32:
                continue
            fr = _xfade_loop(g, n)
            sink = np.interp(np.linspace(0, 1, n), [0, 1], [1.0, r.uniform(0.55, 0.85)])
            idx = np.clip(np.cumsum(sink).astype(int), 0, n - 1)
            fr = fr[idx]
            mix = env(n, 0.03, min(0.6, dur / 2))[:, None]
            seg = seg * (1 - 0.8 * mix) + lowpass_st(fr, 3500) * 0.9 * mix
        elif kind == "bloom":
            g = int(r.uniform(0.03, 0.09) * SR)
            seg = _xfade_loop(st[a:a + g], n) * 1.1
        elif kind == "tear":
            bits = r.integers(4, 7)
            hold = int(r.integers(4, 14))
            crushed = np.round(seg * 2 ** bits) / 2 ** bits
            crushed = np.repeat(crushed[::hold], hold, axis=0)[:n]
            # interleave stutters
            out = crushed.copy()
            k = 0
            while k < n:
                ln = int(r.uniform(0.02, 0.12) * SR)
                if r.random() < 0.5:
                    rep = _xfade_loop(crushed[k:k + max(64, ln // 3)], ln)
                    out[k:k + ln] = rep[: len(out[k:k + ln])]
                k += ln
            seg = out * 0.9
        elif kind == "soft":
            # light crush blended under the music
            hold = int(r.integers(2, 5))
            crushed = np.round(seg * 2 ** 8) / 2 ** 8
            crushed = np.repeat(crushed[::hold], hold, axis=0)[:n]
            mix = env(n, 0.05, 0.15)[:, None] * 0.6
            seg = seg * (1 - mix) + lowpass_st(crushed, 5000) * mix
        elif kind == "roll":
            speed = np.linspace(1, 0.05, n) ** 1.5
            idx = np.clip(np.cumsum(speed).astype(int), 0, n - 1)
            seg = lowpass_st(seg[idx], 2500) * env(n, 0.0, 0.15)[:, None]
        elif kind == "drop":
            seg *= 0.0
        st[a:a + n] = seg
    return st


def lowpass_st(x, fc):
    return np.stack([lowpass(x[:, 0], fc), lowpass(x[:, 1], fc)], 1)


def render(seconds, events=(), seed=None, chunk=300.0, overlap=8.0, style="original"):
    """style: a STYLES preset or a settings dict; seed defaults to the settings' seed, else 0."""
    if seed is None:
        seed = style.get("seed", 0) if isinstance(style, dict) else 0
    if seconds <= chunk:
        st = compose(seconds + 1, seed, style)[: int(seconds * SR)]
    else:
        # long scores: compose in chunks and crossfade them, keeping memory bounded
        n = int(seconds * SR)
        st = np.zeros((n, 2), np.float32)
        ov = int(overlap * SR)
        i, k = 0, 0
        while i < n:
            part = compose(chunk + overlap + 1, seed * 1000 + k, style)[: int((chunk + overlap) * SR)]
            part = part / (np.max(np.abs(part)) or 1) * 0.8
            if k:
                part[:ov] *= np.linspace(0, 1, ov, dtype=np.float32)[:, None]
            part[-ov:] *= np.linspace(1, 0, ov, dtype=np.float32)[:, None]
            end = min(n, i + len(part))
            st[i:end] += part[: end - i]
            i += int(chunk * SR)
            k += 1
    st = apply_glitches(st, list(events), np.random.default_rng(seed + 7))
    # loop-friendly: short fade at each end so the wrap doesn't click
    f = int(0.5 * SR)
    st[:f] *= np.linspace(0, 1, f)[:, None]; st[-f:] *= np.linspace(1, 0, f)[:, None]
    peak = np.max(np.abs(st)) or 1
    st = np.tanh(st / peak * 1.4) * 0.89
    return st.astype(np.float32)


def write_wav(path, st):
    pcm = (np.clip(st, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", default="score.wav")
    ap.add_argument("--seconds", type=float, default=120)
    ap.add_argument("--seed", type=int, help="default: the config's seed, else 1")
    ap.add_argument("--style", default="original", choices=sorted(STYLES))
    ap.add_argument("--config", help="score settings JSON (a map's score.json) instead of --style")
    ap.add_argument("--dump", metavar="STYLE", choices=sorted(STYLES),
                    help="print a preset as full settings JSON (with --seed) and exit")
    o = ap.parse_args()
    if o.dump:
        print(dumps(settings(o.dump, seed=o.seed)))
    else:
        st = load(o.config) if o.config else o.style
        seed = o.seed if o.seed is not None else (st.get("seed", 1) if o.config else 1)
        write_wav(o.out, render(o.seconds, seed=seed, style=st))
        print("wrote", o.out)
