#!/usr/bin/env python3
"""Generative ambient score: monk choir, drones, soft synth arps, cathedral reverb.

Original material in the spirit of early-2000s sci-fi shooter soundtracks (no
quoted melodies). glitch.py calls render(); run standalone to audition:

    ./soundtrack.py -o score.wav --seconds 180 --seed 1
"""
import argparse, wave
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


# D dorian-ish harmony. Chords as MIDI note lists (low voices).
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
# Original chant phrases (MIDI), each note held ~1-3 beats.
CHANT = [
    [(62, 2), (65, 1), (67, 1), (69, 3), (67, 1), (65, 2), (64, 2), (62, 4)],
    [(69, 2), (72, 2), (70, 1), (69, 1), (67, 2), (69, 4), (65, 2), (67, 2)],
    [(62, 3), (60, 1), (62, 2), (65, 2), (64, 2), (62, 2), (57, 4)],
    [(65, 2), (67, 2), (69, 2), (70, 2), (69, 3), (67, 1), (65, 2), (62, 4)],
]


def compose(seconds, seed):
    global rng
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    bus = {k: np.zeros(n, np.float32) for k in ("choir", "chant", "pad", "sub", "arp", "air", "boom")}
    chord_len = 7.5
    beat = chord_len / 8
    # Sections of 8 chords; each turns layers on/off for an ebb-and-flow arrangement.
    t, ci, sec = 0.0, 0, 0
    while t < seconds:
        if ci % 8 == 0:
            sec += 1
            layers = {"choir": rng.random() < 0.8, "chant": rng.random() < 0.55 and sec > 1,
                      "pad": rng.random() < 0.85, "arp": rng.random() < 0.45, "sub": True}
            add(bus["boom"], boom(), int(t * SR))
        chord = PROG[ci % len(PROG)]
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
                note = pat[k % 8] + 12
                v = osc(midi(note), nl, "square") * np.exp(-np.arange(nl) / (0.18 * SR)).astype(np.float32)
                add(bus["arp"], lowpass(v, 1800 + 1200 * np.sin(t * 0.2 + k)) * 0.05, at + int(k * beat / 2 * SR))
        if layers["chant"] and ci % 8 in (0, 4):
            phrase = CHANT[rng.integers(len(CHANT))]
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
    bus["air"] = lowpass(wn, 700) * (0.02 + 0.03 * sweep)

    # colour each bus
    choir = 0.6 * resonators(bus["choir"], VOWEL_OO) + 0.4 * resonators(bus["choir"], VOWEL_AH)
    chant = resonators(bus["chant"], VOWEL_AH) * 0.9 + resonators(bus["chant"], VOWEL_OO) * 0.5
    pad = lowpass(bus["pad"], 1400)
    arp = bus["arp"]
    dry = choir * 1.3 + chant * 1.4 + pad * 0.9 + bus["sub"] * 0.6 + arp * 0.9 + bus["air"] + bus["boom"]
    st = np.stack([dry + 0.25 * arp, dry - 0.25 * arp], 1)
    st = hall(st, seed)
    return st


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


def render(seconds, events=(), seed=0, chunk=300.0, overlap=8.0):
    if seconds <= chunk:
        st = compose(seconds + 1, seed)[: int(seconds * SR)]
    else:
        # long scores: compose in chunks and crossfade them, keeping memory bounded
        n = int(seconds * SR)
        st = np.zeros((n, 2), np.float32)
        ov = int(overlap * SR)
        i, k = 0, 0
        while i < n:
            part = compose(chunk + overlap + 1, seed * 1000 + k)[: int((chunk + overlap) * SR)]
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
    ap.add_argument("--seed", type=int, default=1)
    o = ap.parse_args()
    write_wav(o.out, render(o.seconds, seed=o.seed))
    print("wrote", o.out)
