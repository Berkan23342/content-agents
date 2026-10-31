"""Sound polish for Bubbly Kids TV: voice processing, synthesized cartoon sound effects and mastering.

Everything is generated here (numpy/scipy), so there are no third-party samples to license.
"""
from fractions import Fraction

import numpy as np
from scipy import ndimage, signal

SR = 44100


def db(x):
    return 10 ** (x / 20)


def resample(x, sr_from, sr_to):
    if sr_from == sr_to:
        return x.astype(np.float32)
    f = Fraction(int(round(sr_to)), int(round(sr_from))).limit_denominator(2000)
    return signal.resample_poly(x, f.numerator, f.denominator).astype(np.float32)


# ---------------------------------------------------------------- filters (RBJ biquads)
def _biquad(kind, f0, sr, q=0.707, gain_db=0.0):
    a_ = db(gain_db / 2)
    w0 = 2 * np.pi * f0 / sr
    cw, sw = np.cos(w0), np.sin(w0)
    alpha = sw / (2 * q)
    if kind == "peak":
        b = [1 + alpha * a_, -2 * cw, 1 - alpha * a_]
        a = [1 + alpha / a_, -2 * cw, 1 - alpha / a_]
    elif kind == "highshelf":
        sq = 2 * np.sqrt(a_) * alpha
        b = [a_ * ((a_ + 1) + (a_ - 1) * cw + sq), -2 * a_ * ((a_ - 1) + (a_ + 1) * cw), a_ * ((a_ + 1) + (a_ - 1) * cw - sq)]
        a = [(a_ + 1) - (a_ - 1) * cw + sq, 2 * ((a_ - 1) - (a_ + 1) * cw), (a_ + 1) - (a_ - 1) * cw - sq]
    else:
        raise ValueError(kind)
    return np.array(b) / a[0], np.array(a) / a[0]


def eq(x, sr, kind, f0, gain_db, q=0.9):
    b, a = _biquad(kind, f0, sr, q, gain_db)
    return signal.lfilter(b, a, x, axis=0).astype(np.float32)


def highpass(x, sr, f0, order=2):
    sos = signal.butter(order, f0, "highpass", fs=sr, output="sos")
    return signal.sosfilt(sos, x, axis=0).astype(np.float32)


def lowpass(x, sr, f0, order=2):
    sos = signal.butter(order, f0, "lowpass", fs=sr, output="sos")
    return signal.sosfilt(sos, x, axis=0).astype(np.float32)


def bandpass(x, sr, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], "bandpass", fs=sr, output="sos")
    return signal.sosfilt(sos, x, axis=0).astype(np.float32)


# ---------------------------------------------------------------- dynamics
def envelope(x, sr, attack, release, block=0.002):
    """Peak-ish level (linear) per sample with separate attack and release times."""
    mono = np.abs(x) if x.ndim == 1 else np.abs(x).max(axis=1)
    n = int(sr * block)
    blocks = len(mono) // n + 1
    padded = np.pad(mono, (0, blocks * n - len(mono)))
    level = padded.reshape(blocks, n).max(axis=1)
    ka, kr = np.exp(-block / attack), np.exp(-block / release)
    out = np.empty(blocks, dtype=np.float32)
    e = 0.0
    for i, v in enumerate(level):
        k = ka if v > e else kr
        e = k * e + (1 - k) * v
        out[i] = e
    return np.repeat(out, n)[: len(mono)]


def compress(x, sr, threshold_db=-20.0, ratio=3.0, attack=0.005, release=0.12, knee_db=6.0):
    env_db = 20 * np.log10(envelope(x, sr, attack, release) + 1e-9)
    over = env_db - threshold_db
    # soft knee
    gain_db = np.where(over <= -knee_db / 2, 0.0,
                       np.where(over >= knee_db / 2, -over * (1 - 1 / ratio),
                                -((over + knee_db / 2) ** 2) / (2 * knee_db) * (1 - 1 / ratio)))
    g = db(gain_db).astype(np.float32)
    return x * (g if x.ndim == 1 else g[:, None])


def limiter(x, sr, ceiling_db=-1.0, lookahead=0.005, release=0.08):
    ceiling = db(ceiling_db)
    peak = np.abs(x).max(axis=1) if x.ndim == 2 else np.abs(x)
    need = np.minimum(1.0, ceiling / np.maximum(peak, 1e-9))
    la = max(1, int(sr * lookahead))
    need = ndimage.minimum_filter1d(need, size=2 * la + 1, mode="nearest")
    # smooth recovery: one-pole on 1 ms blocks, instant attack
    n = int(sr * 0.001)
    blocks = len(need) // n + 1
    padded = np.pad(need, (0, blocks * n - len(need)), constant_values=1.0)
    blk = padded.reshape(blocks, n).min(axis=1)
    kr = np.exp(-0.001 / release)
    g = np.empty(blocks, dtype=np.float32)
    cur = 1.0
    for i, v in enumerate(blk):
        cur = v if v < cur else kr * cur + (1 - kr) * v
        g[i] = cur
    gain = np.repeat(g, n)[: len(need)]
    return x * (gain[:, None] if x.ndim == 2 else gain)


def loudness(x, sr):
    import pyloudnorm as pyln

    return pyln.Meter(sr).integrated_loudness(x)


def master(x, sr=SR, target_lufs=-14.0):
    """Gentle glue compression, loudness to YouTube's -14 LUFS, then a -1 dBFS peak limiter."""
    x = compress(x, sr, threshold_db=-16, ratio=1.8, attack=0.01, release=0.25)
    lufs = loudness(x, sr)
    x = x * db(target_lufs - lufs)
    for _ in range(2):  # the limiter lowers loudness a little; nudge back
        y = limiter(x, sr)
        diff = target_lufs - loudness(y, sr)
        if abs(diff) < 0.3:
            break
        x = x * db(diff)
    return limiter(x, sr).astype(np.float32)


# ---------------------------------------------------------------- voice
def voice(x, sr_in, pitch=1.0, target_db=-17.0):
    """Clean, present narration: resample (pitch > 1 = higher and faster cartoon voice), trim, EQ, compress, level."""
    y = resample(np.asarray(x, dtype=np.float32), sr_in * pitch, SR)
    loud = np.where(np.abs(y) > 0.01)[0]
    if len(loud):
        y = y[max(loud[0] - 300, 0): loud[-1] + 2000]
    y = highpass(y, SR, 85)
    y = eq(y, SR, "peak", 280, -2.0, 1.0)  # less boxy
    y = eq(y, SR, "peak", 3200, 2.5, 0.8)  # presence, clearer words
    y = eq(y, SR, "highshelf", 9000, 1.5)  # air
    y = compress(y, SR, threshold_db=-24, ratio=3.0, attack=0.004, release=0.1)
    active = np.abs(y) > 0.02
    rms = np.sqrt(np.mean(y[active] ** 2)) if active.any() else 1.0
    y = y * db(target_db) / max(rms, 1e-6)
    # fade edges to avoid clicks
    f = min(300, len(y) // 4)
    if f:
        y[:f] *= np.linspace(0, 1, f)
        y[-f:] *= np.linspace(1, 0, f)
    return y.astype(np.float32)


# ---------------------------------------------------------------- cartoon sound effects
def _t(seconds):
    return np.arange(int(SR * seconds)) / SR


def _pan(x, p):
    """p = -1 (left) .. 1 (right), constant power."""
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1).astype(np.float32)


def _tone(freq, t):
    return np.sin(2 * np.pi * np.cumsum(np.broadcast_to(freq, t.shape)) / SR)


def _fm_bell(f, seconds, decay):
    t = _t(seconds)
    index = 3.0 * np.exp(-t / (decay * 0.4))
    x = np.sin(2 * np.pi * f * t + index * np.sin(2 * np.pi * f * 3.5 * t))
    return x * np.exp(-t / decay)


def _attack(x, seconds=0.004):
    n = min(len(x), int(SR * seconds))
    x[:n] *= np.linspace(0, 1, n)
    return x


def sfx_pop(rng):
    t = _t(0.09)
    f = 380 * (1 + 2.6 * (1 - np.exp(-t / 0.018)))
    x = _tone(f, t) * np.exp(-t / 0.028)
    x[:60] += rng.normal(0, 0.4, 60) * np.linspace(1, 0, 60)
    return _pan(_attack(x, 0.001) * 0.8, rng.uniform(-0.3, 0.3))


def sfx_boing(rng):
    t = _t(0.7)
    f = 140 * (1 + 0.55 * np.exp(-t / 0.2) * np.sin(2 * np.pi * 11 * t)) * (1 + 0.6 * np.exp(-t / 0.08))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)) * np.exp(-t / 0.3)
    return _pan(_attack(x) * 0.6, 0)


def sfx_whoop(rng):  # slide whistle going up
    t = _t(0.5)
    f = 520 * (1700 / 520) ** (np.minimum(t / 0.42, 1)) * (1 + 0.012 * np.sin(2 * np.pi * 7 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.12 * np.sin(2 * ph)
    breath = bandpass(rng.normal(0, 1, len(t)), SR, 1500, 5000) * 0.05
    env = np.minimum(1, t / 0.03) * np.minimum(1, (0.5 - t) / 0.08)
    return _pan((x + breath) * env * 0.35, 0)


def sfx_whoosh(rng):
    secs = 0.75
    t = _t(secs)
    noise = rng.normal(0, 1, len(t))
    out = np.zeros_like(noise)
    hop = int(SR * 0.02)
    win = np.hanning(2 * hop)
    for i in range(0, len(t) - 2 * hop, hop):
        c = 350 + 2600 * np.sin(np.pi * (i / len(t))) ** 2
        seg = bandpass(noise[i:i + 2 * hop], SR, c * 0.6, min(c * 1.6, 18000))
        out[i:i + 2 * hop] += seg * win
    env = np.sin(np.pi * t / secs) ** 1.5
    x = out * env * 0.5
    p = np.linspace(-0.7, 0.7, len(t))
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1).astype(np.float32)


def sfx_sparkle(rng):
    notes = [2093, 2637, 3136, 3520, 4186]  # C7 pentatonic-ish
    out = np.zeros((int(SR * 1.1), 2), dtype=np.float32)
    for k, f in enumerate(notes):
        b = _fm_bell(f, 0.6, 0.22) * 0.18
        i = int(SR * k * 0.055)
        out[i:i + len(b)] += _pan(b, -0.6 + 0.3 * k)[: len(out) - i]
    return out


def sfx_ding(rng):
    out = np.zeros(int(SR * 1.6), dtype=np.float32)
    for f, g in ((1046.5, 0.5), (1318.5, 0.35), (1568, 0.3), (2093, 0.15)):
        out += _fm_bell(f, 1.6, 0.6) * g
    return _pan(out * 0.4, 0)


def sfx_tick(rng):
    t = _t(0.06)
    x = (np.sin(2 * np.pi * 950 * t) + 0.6 * np.sin(2 * np.pi * 2300 * t)) * np.exp(-t / 0.012)
    return _pan(_attack(x, 0.0005) * 0.45, rng.uniform(-0.2, 0.2))


def sfx_splash(rng):
    t = _t(0.7)
    body = lowpass(highpass(rng.normal(0, 1, len(t)), SR, 300), SR, 4500) * np.exp(-t / 0.15) * 0.4
    out = _pan(body, 0)
    for _ in range(9):
        dt = _t(0.05)
        f = rng.uniform(900, 1800) * (1 + 1.5 * dt / 0.05)
        drop = _tone(f, dt) * np.exp(-dt / 0.015) * 0.18
        i = int(rng.uniform(0.02, 0.45) * SR)
        out[i:i + len(drop)] += _pan(drop, rng.uniform(-0.8, 0.8))
    return out


def sfx_thunder(rng):
    t = _t(2.8)
    brown = np.cumsum(rng.normal(0, 1, len(t)))
    brown = highpass(brown - np.mean(brown), SR, 25)
    rumble = lowpass(brown, SR, 180, 4)
    rumble /= np.abs(rumble).max() + 1e-9
    crack = highpass(rng.normal(0, 1, len(t)), SR, 800) * np.exp(-t / 0.06) * 0.3
    env = np.minimum(1, t / 0.02) * np.exp(-t / 1.0) * (1 + 0.4 * np.sin(2 * np.pi * 2.2 * t))
    x = (rumble * 0.8 + crack) * env * 0.6
    return np.stack([x, np.roll(x, 400)], axis=1).astype(np.float32)


def sfx_cheer(rng):
    """Light applause: many short hand-clap bursts."""
    secs = 2.4
    out = np.zeros((int(SR * secs), 2), dtype=np.float32)
    ct = _t(0.03)
    for _ in range(170):
        at = rng.uniform(0, secs - 0.05)
        amp = np.sin(np.pi * at / secs) ** 0.7
        clap = bandpass(rng.normal(0, 1, len(ct)), SR, 900, 3500) * np.exp(-ct / 0.006) * 0.12 * amp
        i = int(at * SR)
        out[i:i + len(clap)] += _pan(clap, rng.uniform(-0.9, 0.9))
    return out


SFX = {"pop": sfx_pop, "boing": sfx_boing, "whoop": sfx_whoop, "whoosh": sfx_whoosh, "sparkle": sfx_sparkle,
       "ding": sfx_ding, "tick": sfx_tick, "splash": sfx_splash, "thunder": sfx_thunder, "cheer": sfx_cheer}


def render_sfx(events, n, seed=7):
    """events: (seconds, kind); returns a stereo track n samples long."""
    rng = np.random.default_rng(seed)
    out = np.zeros((n, 2), dtype=np.float32)
    for at, kind in events:
        x = SFX[kind](rng)
        i = int(at * SR)
        if i >= n:
            continue
        j = min(n, i + len(x))
        out[i:j] += x[: j - i]
    return out
