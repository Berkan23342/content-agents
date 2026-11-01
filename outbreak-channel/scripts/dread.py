"""Sound for Outbreak Diary: synthesized horror effects, ambience beds and a dark drone score.

Everything is generated (numpy/scipy, FluidSynth for the drone), so there are no third-party samples to license.
The effects are added to kids-channel/scripts/audio.py's SFX table, so Builder.sfx and audio.render_sfx play them.
"""
import os
import random
import zlib

import numpy as np

import audio
from audio import SR, _attack, _pan, _t, _tone, bandpass, highpass, lowpass
from episode import Midi, render_midi


def _norm(x, peak=1.0):
    return x / (np.abs(x).max() + 1e-9) * peak


def _brown(rng, n):
    x = np.cumsum(rng.normal(0, 1, n))
    return highpass(x - x.mean(), SR, 20)


def _echo(x, delays=((0.13, 0.35), (0.29, 0.2), (0.47, 0.12))):
    """A cheap room/stairwell tail: a few quiet late copies."""
    out = np.concatenate([x, np.zeros(int(SR * max(d for d, _ in delays)) + 1, dtype=x.dtype)])
    for d, g in delays:
        i = int(SR * d)
        out[i:i + len(x)] += x * g
    return out


# ---------------------------------------------------------------- one-shot effects
def sfx_heartbeat(rng):
    """Lub-dub, with harmonics so it still reads on phone speakers."""
    out = np.zeros(int(SR * 0.9))
    for at, f, g in ((0.0, 62, 1.0), (0.23, 54, 0.7)):
        t = _t(0.3)
        ph = 2 * np.pi * np.cumsum(f * (1 + 0.7 * np.exp(-t / 0.015))) / SR
        x = (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph)) * np.exp(-t / 0.07)
        x += lowpass(rng.normal(0, 1, len(t)), SR, 350) * np.exp(-t / 0.015) * 0.6
        i = int(at * SR)
        out[i:i + len(x)] += x * g
    return _pan(_norm(out, 0.9), 0)


def _wood_hit(rng, modes, decay, noise_hi, gain):
    t = _t(0.35)
    x = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * a for f, a in modes) * np.exp(-t / decay)
    x += bandpass(rng.normal(0, 1, len(t)), SR, 150, noise_hi) * np.exp(-t / 0.012) * 0.8
    return _attack(x * gain, 0.0008)


def sfx_knock(rng):
    """Three knuckle knocks on a wooden door."""
    out = np.zeros(int(SR * 1.0))
    for k, at in enumerate((0.0, 0.2, 0.42)):
        hit = _wood_hit(rng, ((190, 1.0), (330, 0.6), (540, 0.35), (880, 0.15)), 0.045, 2600, 0.55 + 0.1 * (k == 2))
        i = int(at * SR)
        out[i:i + len(hit)] += hit
    return _pan(_norm(_echo(out, ((0.09, 0.25), (0.21, 0.12))), 0.8), 0)


def sfx_bang(rng):
    """Fists pounding on the door from the other side: three heavy hits and a rattling chain."""
    out = np.zeros(int(SR * 1.6))
    for at in (0.0, 0.36, 0.62):
        at = max(0.0, at + rng.uniform(-0.03, 0.03))
        hit = _wood_hit(rng, ((85, 1.0), (140, 0.8), (230, 0.5), (410, 0.3)), 0.08, 1800, 1.0)
        rattle_t = _t(0.25)
        rattle = bandpass(rng.normal(0, 1, len(rattle_t)), SR, 2500, 7000) * (rng.random(len(rattle_t)) < 0.02) * 3
        rattle = lowpass(rattle, SR, 8000) * np.exp(-rattle_t / 0.08)
        i = int(at * SR)
        out[i:i + len(hit)] += np.tanh(hit * 1.6)
        out[i:i + len(rattle)] += rattle * 0.25
    return _pan(_norm(_echo(out), 0.95), 0)


def sfx_creak(rng):
    """A slow door creak: stick-slip pulses through wood resonances."""
    secs = 1.4
    t = _t(secs)
    rate = 26 + 14 * np.sin(np.pi * t / secs) + 4 * np.sin(2 * np.pi * 1.3 * t)
    ph = np.cumsum(rate) / SR
    pulses = (np.diff(np.floor(ph), prepend=0) > 0).astype(float) * (0.6 + 0.4 * rng.random(len(t)))
    body = sum(bandpass(pulses, SR, f * 0.85, f * 1.15) * g for f, g in ((420, 1.0), (980, 0.7), (2100, 0.45), (3500, 0.2)))
    env = np.sin(np.pi * t / secs) ** 0.6
    return _pan(_norm(body * env, 0.6), rng.uniform(-0.3, 0.3))


def sfx_static(rng):
    """Radio static with crackles and a flutter."""
    secs = 1.6
    t = _t(secs)
    hiss = _norm(bandpass(rng.normal(0, 1, len(t)), SR, 400, 6000)) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * t) ** 2)
    crackle = _norm(highpass((rng.random(len(t)) < 0.0015) * rng.normal(0, 4, len(t)), SR, 1500))
    env = np.minimum(1, t / 0.05) * np.minimum(1, (secs - t) / 0.2)
    return _pan((hiss * 0.3 + crackle * 0.25) * env, 0)


def sfx_siren(rng):
    """A distant wailing siren, far away across the city."""
    secs = 4.5
    t = _t(secs)
    f = 760 + 330 * np.sin(2 * np.pi * t / 2.6 - np.pi / 2)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.3 * np.sin(2 * ph)
    x = lowpass(x, SR, 1800) * np.minimum(1, t / 0.8) * np.minimum(1, (secs - t) / 1.2)
    x = _echo(x, ((0.21, 0.5), (0.43, 0.35), (0.71, 0.22), (1.05, 0.12)))
    return np.stack([x * 0.9, np.roll(x, 900) * 0.7], axis=1).astype(np.float32) * 0.18


def sfx_groan(rng):
    """A zombie groan: a rough, wobbling voice through an 'uhh' vowel."""
    secs = 1.9
    t = _t(secs)
    f0 = rng.uniform(78, 98) * (1 + 0.08 * np.sin(2 * np.pi * 4.5 * t) + 0.05 * rng.normal(0, 1, len(t)).cumsum() / len(t) ** 0.5)
    f0 *= 1 - 0.18 * (t / secs) ** 2
    ph = np.cumsum(f0) / SR
    pulse = 2 * (ph % 1) - 1  # buzzy sawtooth glottis
    pulse += rng.normal(0, 0.35, len(t))  # breath and rasp
    voice = sum(bandpass(pulse, SR, f * 0.8, f * 1.25) * g for f, g in ((560, 1.0), (980, 0.6), (2450, 0.25)))
    env = np.minimum(1, t / 0.35) ** 2 * np.minimum(1, (secs - t) / 0.5) * (0.75 + 0.25 * np.sin(2 * np.pi * 1.7 * t))
    x = np.tanh(_norm(voice) * 2.2) * env
    return _pan(_norm(_echo(x, ((0.11, 0.2), (0.27, 0.1))), 0.7), rng.uniform(-0.4, 0.4))


def sfx_glass(rng):
    """Breaking glass: a crack, then shards ringing as they fall."""
    secs = 1.3
    out = np.zeros(int(SR * secs))
    t = _t(0.2)
    out[:len(t)] += highpass(rng.normal(0, 1, len(t)), SR, 2500) * np.exp(-t / 0.03)
    for _ in range(28):
        st = _t(0.25)
        ping = np.sin(2 * np.pi * rng.uniform(2800, 7500) * st) * np.exp(-st / rng.uniform(0.02, 0.07))
        i = int(rng.uniform(0.0, secs - 0.3) ** 1.6 * SR)
        out[i:i + len(st)] += ping * rng.uniform(0.15, 0.45)
    out = _norm(out, 0.7)
    return np.stack([out, np.roll(out, 300)], axis=1).astype(np.float32)


def sfx_steps(rng):
    """Four slow footsteps on a hard floor, as if from the floor above."""
    out = np.zeros(int(SR * 2.4))
    for k in range(4):
        t = _t(0.25)
        thud = lowpass(rng.normal(0, 1, len(t)), SR, 260) * np.exp(-t / 0.05) * 1.6
        scuff = bandpass(rng.normal(0, 1, len(t)), SR, 900, 2800) * np.exp(-t / 0.02) * 0.25
        i = max(0, int((k * 0.55 + rng.uniform(-0.04, 0.04)) * SR))
        out[i:i + len(t)] += (thud + scuff) * (0.8 + 0.2 * (k % 2))
    return _pan(_norm(lowpass(out, SR, 1600), 0.75), 0)


def sfx_sting(rng):
    """The cliffhanger hit: a low, distorted brass-like 'braam' that opens up and fades."""
    secs = 3.2
    t = _t(secs)
    x = np.zeros(len(t))
    for f in (43.65, 65.4, 87.3, 130.8):  # F power chord, low
        for det in (-0.25, 0.0, 0.3):
            ph = (f + det) * t + rng.uniform(0, 1)
            x += 2 * (ph % 1) - 1
    out = np.zeros(len(t))
    hop = int(SR * 0.025)
    for i in range(0, len(t), hop):  # filter sweeps open, then closes as it fades
        cut = 180 + 2400 * np.exp(-(i / SR) / 0.35) * (1 - np.exp(-(i / SR) / 0.03))
        seg = x[max(0, i - 2048):i + hop]
        out[i:i + hop] = lowpass(seg, SR, max(120.0, cut), 2)[-len(out[i:i + hop]):]
    sub = np.sin(2 * np.pi * 43.65 * t) * 0.8
    env = np.minimum(1, t / 0.01) * np.exp(-t / 1.1)
    y = np.tanh((_norm(out) + sub) * 1.8) * env
    hit = highpass(rng.normal(0, 1, len(t)), SR, 300) * np.exp(-t / 0.05) * 0.5
    y = _norm(y + hit, 1.0)
    return np.stack([y, np.roll(y, 220)], axis=1).astype(np.float32)


def sfx_thud(rng):
    t = _t(0.5)
    x = np.sin(2 * np.pi * 70 * t * (1 + 0.5 * np.exp(-t / 0.03))) * np.exp(-t / 0.12)
    x += lowpass(rng.normal(0, 1, len(t)), SR, 500) * np.exp(-t / 0.03) * 0.7
    return _pan(_norm(_echo(x), 0.85), 0)


def sfx_scratch(rng):
    """Nails dragging on the other side of the door."""
    secs = 1.8
    out = np.zeros(int(SR * secs))
    for k in range(5):
        dur = rng.uniform(0.18, 0.32)
        t = _t(dur)
        c = rng.uniform(2000, 3500) * (1 - 0.3 * t / dur)
        x = bandpass(rng.normal(0, 1, len(t)), SR, 1200, 6500) * (1 + np.sin(2 * np.pi * c / 40 * t)) * np.sin(np.pi * t / dur)
        i = int((k * 0.33 + rng.uniform(0, 0.08)) * SR)
        out[i:i + len(t)] += x[: len(out) - i]
    return _pan(_norm(lowpass(out, SR, 5000), 0.4), 0.1)


def sfx_buzz(rng):
    """A phone vibrating on a table: two pulses."""
    out = np.zeros(int(SR * 1.3))
    for at in (0.0, 0.6):
        t = _t(0.38)
        x = np.sign(np.sin(2 * np.pi * 155 * t)) * (1 + 0.3 * np.sin(2 * np.pi * 31 * t))
        x = lowpass(x, SR, 1200) * np.minimum(1, t / 0.01) * np.minimum(1, (0.38 - t) / 0.02)
        i = int(at * SR)
        out[i:i + len(x)] += x
    return _pan(_norm(out, 0.45), 0)


def sfx_click(rng):
    out = np.zeros(int(SR * 0.25))
    for at in (0.0, 0.07):
        t = _t(0.03)
        x = highpass(rng.normal(0, 1, len(t)), SR, 1800) * np.exp(-t / 0.004)
        i = int(at * SR)
        out[i:i + len(x)] += x
    return _pan(_norm(out, 0.6), 0)


def sfx_drip(rng):
    t = _t(0.12)
    f = 900 * (1 + 2.2 * t / 0.12)
    x = _tone(f, t) * np.exp(-t / 0.025)
    return _pan(_norm(_echo(x, ((0.18, 0.3), (0.37, 0.15))), 0.5), rng.uniform(-0.3, 0.3))


HORROR_SFX = {"heartbeat": sfx_heartbeat, "knock": sfx_knock, "bang": sfx_bang, "creak": sfx_creak, "static": sfx_static,
              "siren": sfx_siren, "groan": sfx_groan, "glass": sfx_glass, "steps": sfx_steps, "sting": sfx_sting,
              "thud": sfx_thud, "scratch": sfx_scratch, "buzz": sfx_buzz, "click": sfx_click, "drip": sfx_drip}
audio.SFX.update(HORROR_SFX)
SFX_NAMES = sorted(HORROR_SFX) + ["thunder", "whoosh"]


# ---------------------------------------------------------------- ambience beds (whole episode)
def bed_rain(rng, n):
    rain = lowpass(highpass(rng.normal(0, 1, n), SR, 500), SR, 7000) * 0.35
    drops = (rng.random(n) < 0.0008) * rng.normal(0, 1, n)
    drops = bandpass(drops, SR, 1500, 5000) * 4
    gust = 0.75 + 0.25 * np.sin(2 * np.pi * np.arange(n) / SR / 9 + rng.uniform(0, 6))
    x = (rain + drops * 0.3) * gust
    return np.stack([x, np.roll(x, 1300)], axis=1)


def bed_wind(rng, n):
    s = np.arange(n) / SR
    body = lowpass(_brown(rng, n), SR, 400)
    body = _norm(body) * (0.5 + 0.5 * np.sin(2 * np.pi * s / 7 + 1) ** 2)
    whistle = bandpass(rng.normal(0, 1, n), SR, 700, 1100) * (0.5 + 0.5 * np.sin(2 * np.pi * s / 5.3)) * 0.12
    x = body * 0.6 + whistle
    return np.stack([x, np.roll(x, 2200)], axis=1)


def bed_night(rng, n):
    """Room tone, plus the city far away: a siren now and then, a distant groan."""
    tone = _norm(lowpass(_brown(rng, n), SR, 140)) * 0.25
    out = np.stack([tone, np.roll(tone, 700)], axis=1)
    at = rng.uniform(2, 6)
    while at < n / SR - 4:
        fx = sfx_siren(rng) * 0.6 if rng.random() < 0.6 else sfx_groan(rng) * 0.08
        i = int(at * SR)
        j = min(n, i + len(fx))
        out[i:j] += fx[: j - i]
        at += rng.uniform(9, 16)
    return out


BEDS = {"rain": bed_rain, "wind": bed_wind, "night": bed_night}


# ---------------------------------------------------------------- score: a slow, dark drone in D minor
PAD_CHOIR, PAD_SWEEP, STRINGS, CELLO, PIANO = 91, 95, 49, 42, 0
CHORDS = [[38, 50, 53, 57], [34, 46, 50, 53], [31, 43, 46, 50], [33, 45, 49, 52]]  # Dm, Bb, Gm, A


def drone(length_s, work, seed):
    rng = random.Random(seed)
    m = Midi(60, humanize=False)
    for ch, prog, vol in ((0, PAD_CHOIR, 70), (1, STRINGS, 80), (2, CELLO, 90), (3, PIANO, 60), (4, PAD_SWEEP, 55)):
        m.program(ch, prog)
        m.control(ch, 7, vol)
    for ch, pan in ((0, 40), (1, 88), (2, 64), (3, 70), (4, 30)):
        m.control(ch, 10, pan)
    order = [0, 1, 0, 2, 0, 1, 3, 0] if rng.random() < 0.5 else [0, 2, 1, 3, 0, 2, 1, 3]
    t, k = 0.0, 0
    while t < length_s + 1:
        chord = CHORDS[order[k % len(order)]]
        m.note(2, chord[0], t, 7.9, 52)  # cello root
        for p in chord[1:]:
            m.note(1, p, t + 0.05, 7.9, 34)
            m.note(0, p + 12, t + 0.1, 7.9, 30)
        if k % 2 == 1:
            m.note(4, chord[1] + 12, t + 2, 5.5, 26)
        for beat in range(8):  # a lonely high piano note now and then
            if rng.random() < 0.28:
                m.note(3, rng.choice(chord[1:]) + 24, t + beat + rng.uniform(0, 0.3), 2.5, rng.randint(24, 36))
        t += 8
        k += 1
    music = render_midi(m, os.path.join(work, "drone"))
    n = int(length_s * SR)
    music = np.pad(music, ((0, max(0, n - len(music))), (0, 0)))[:n]
    return _norm(music)


def score(length_s, work, seed, bed=None, bed_level=0.5):
    """The drone, with an ambience bed under it."""
    out = drone(length_s, work, seed)
    if bed:
        rng = np.random.default_rng(zlib.crc32(str(seed).encode()))
        out = out + _norm(BEDS[bed](rng, len(out))) * bed_level
    return _norm(out)
