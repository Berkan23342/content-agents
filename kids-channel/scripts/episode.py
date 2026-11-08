"""Plans and voices one daily Bubbly Kids TV episode (5+ minutes).

Each episode mixes five learning segments (colors, numbers, shapes, animals, ABC) in a
random order and selection seeded by the episode number, so every day is different but reproducible.

Writes:
  build/<id>/props.json   Remotion props (scenes in frames, audio path, thumbnail)
  build/<id>/meta.json    YouTube title / description / tags
  public/audio/<id>.wav   narration + music + SFX mix

Narration: Kokoro TTS (Apache 2.0). Music: public-domain nursery melodies rendered with
FluidSynth + GeneralUser GS. Run with .venv/bin/python.
"""
import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import random
import shutil
import struct
import subprocess
import wave

import numpy as np

import audio

SR = 44100
FPS = 30
VOICE = os.environ.get("VOICE", "af_heart")
SPEED = 0.95
MIN_SECONDS = 305

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
SOUNDFONT = os.environ.get("SOUNDFONT", os.path.join(ROOT, "assets", "soundfont", "GeneralUser-GS.sf2"))
KOKORO = os.path.join(ROOT, "assets", "kokoro")
AUDIO_DIR = os.path.join(ROOT, "public", "audio")
FIRST_EPISODE = dt.date(2026, 10, 29)

PALETTE = ["#FF3B3B", "#FF8A1F", "#FFC92E", "#3CC75A", "#2F8CFF", "#9B5CFF", "#FF6FB5"]

# ---------------------------------------------------------------- content library
COLORS = {
    "Red": ("#FF3B3B", [("apple", "apple"), ("heart", "heart"), ("van", "van"), ("umbrella", "umbrella")]),
    "Orange": ("#FF8A1F", [("carrot", "carrot"), ("pumpkin", "pumpkin"), ("orange", "orange")]),
    "Yellow": ("#FFC92E", [("sun", "sun"), ("star", "star"), ("moon", "moon"), ("chick", "chick")]),
    "Green": ("#3CC75A", [("leaf", "leaf"), ("frog", "frog"), ("tree", "tree")]),
    "Blue": ("#2F8CFF", [("fish", "fish"), ("drop", "raindrop"), ("kite", "kite"), ("umbrella", "umbrella")]),
    "Purple": ("#9B5CFF", [("grapes", "grapes"), ("flower", "flower"), ("yoyo", "yo-yo")]),
    "Pink": ("#FF6FB5", [("pig", "pig"), ("icecream", "ice cream"), ("jellyfish", "jellyfish")]),
    "Brown": ("#A0632F", [("cookie", "cookie"), ("dog", "dog"), ("owl", "owl"), ("nest", "nest")]),
}
NO_ARTICLE = {"grapes"}

NUMBER_WORDS = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"]
COUNTABLES = [
    ("apple", "apple", "apples", "#FF3B3B"), ("star", "star", "stars", "#FFC92E"),
    ("heart", "heart", "hearts", "#FF6FB5"), ("fish", "fish", "fish", "#2F8CFF"),
    ("balloon", "balloon", "balloons", None), ("flower", "flower", "flowers", "#9B5CFF"),
    ("carrot", "carrot", "carrots", "#FF8A1F"), ("cookie", "cookie", "cookies", "#C98B55"),
    ("duck", "duck", "ducks", "#FFC92E"), ("chick", "chick", "chicks", "#FFC92E"),
    ("egg", "egg", "eggs", "#FFF3D6"), ("orange", "orange", "oranges", "#FF8A1F"),
    ("leaf", "leaf", "leaves", "#3CC75A"),
]

SHAPES = [
    ("circle", "A circle is round, like a ball!"),
    ("square", "A square has four sides, all the same!"),
    ("triangle", "A triangle has three sides!"),
    ("rectangle", "A rectangle has two long sides and two short sides!"),
    ("star", "A star has five points!"),
    ("heart", "A heart means I love you!"),
    ("oval", "An oval looks like an egg!"),
    ("diamond", "A diamond looks like a kite!"),
]

ANIMALS = [  # icon, name, sound line, bubble, bubble colour
    ("cat", "cat", "The cat says meow! Meow!", "Meow!", "#F08A24"),
    ("dog", "dog", "The dog says woof woof!", "Woof!", "#A0632F"),
    ("cow", "cow", "The cow says moo! Moo!", "Moo!", "#2F8CFF"),
    ("pig", "pig", "The pig says oink oink!", "Oink!", "#FF6FB5"),
    ("sheep", "sheep", "The sheep says baa! Baa!", "Baa!", "#9B5CFF"),
    ("duck", "duck", "The duck says quack quack!", "Quack!", "#FF8A1F"),
    ("lion", "lion", "The lion says roar!", "Roar!", "#E8962F"),
    ("frog", "frog", "The frog says ribbit! Ribbit!", "Ribbit!", "#3CC75A"),
    ("chick", "chick", "The chick says cheep cheep!", "Cheep!", "#FF8A1F"),
    ("owl", "owl", "The owl says hoo hoo!", "Hoo!", "#A0632F"),
]

LETTERS = [  # letter, spoken name, word, icon, colour
    ("A", "Ay", "apple", "apple", "#FF3B3B"), ("B", "Bee", "balloon", "balloon", "#2F8CFF"),
    ("C", "See", "cat", "cat", "#F08A24"), ("D", "Dee", "dog", "dog", "#A0632F"),
    ("E", "Ee", "egg", "egg", "#FFF3D6"), ("F", "Eff", "fish", "fish", "#2F8CFF"),
    ("G", "Jee", "grapes", "grapes", "#9B5CFF"), ("H", "Aitch", "heart", "heart", "#FF3B3B"),
    ("I", "Eye", "ice cream", "icecream", "#FF6FB5"), ("J", "Jay", "jellyfish", "jellyfish", "#FF6FB5"),
    ("K", "Kay", "kite", "kite", "#FF8A1F"), ("L", "El", "lion", "lion", "#E8962F"),
    ("M", "Em", "moon", "moon", "#FFC92E"), ("N", "En", "nest", "nest", "#A0632F"),
    ("O", "Oh", "owl", "owl", "#A0632F"), ("P", "Pee", "pig", "pig", "#FF6FB5"),
    ("Q", "Cue", "queen", "crown", "#FFC92E"), ("R", "Ar", "rainbow", "rainbow", "#9B5CFF"),
    ("S", "Ess", "sun", "sun", "#FFC92E"), ("T", "Tee", "tree", "tree", "#3CC75A"),
    ("U", "You", "umbrella", "umbrella", "#9B5CFF"), ("V", "Vee", "van", "van", "#FF3B3B"),
    ("W", "Double you", "watermelon", "watermelon", "#3CC75A"), ("X", "Ex", "xylophone", "xylophone", "#2F8CFF"),
    ("Y", "Why", "yo-yo", "yoyo", "#3CC75A"), ("Z", "Zee", "zebra", "zebra", "#5B5B6B"),
]

# melodies: (midi, beats) notes and one chord per half bar (2 beats)
SONGS = {
    "twinkle": dict(bpm=96, notes=[(p, b) for ph in [
        [72, 72, 79, 79, 81, 81, 79], [77, 77, 76, 76, 74, 74, 72], [79, 79, 77, 77, 76, 76, 74],
        [79, 79, 77, 77, 76, 76, 74], [72, 72, 79, 79, 81, 81, 79], [77, 77, 76, 76, 74, 74, 72],
    ] for p, b in zip(ph, [1, 1, 1, 1, 1, 1, 2])],
        chords="C C F C F C G C C G C G C G C G C C F C F C G C".split()),
    "mary": dict(bpm=104, notes=[
        (76, 1), (74, 1), (72, 1), (74, 1), (76, 1), (76, 1), (76, 2), (74, 1), (74, 1), (74, 2), (76, 1), (79, 1), (79, 2),
        (76, 1), (74, 1), (72, 1), (74, 1), (76, 1), (76, 1), (76, 1), (76, 1), (74, 1), (74, 1), (76, 1), (74, 1), (72, 4)],
        chords="C C C C G G C C C C C C G G C C".split()),
    "frere": dict(bpm=100, notes=[
        (72, 1), (74, 1), (76, 1), (72, 1)] * 2 + [(76, 1), (77, 1), (79, 2)] * 2 + [
        (79, .5), (81, .5), (79, .5), (77, .5), (76, 1), (72, 1)] * 2 + [(72, 1), (67, 1), (72, 2)] * 2,
        chords="C C C C C C C C C G C G C G C G".split()),
    "london": dict(bpm=100, notes=[
        (79, 1.5), (81, .5), (79, 1), (77, 1), (76, 1), (77, 1), (79, 2), (74, 1), (76, 1), (77, 2), (76, 1), (77, 1), (79, 2),
        (79, 1.5), (81, .5), (79, 1), (77, 1), (76, 1), (77, 1), (79, 2), (74, 2), (79, 2), (76, 1), (72, 3)],
        chords="C C C C G G C C C C C C G G C C".split()),
    "macdonald": dict(bpm=108, notes=[
        (72, 1), (72, 1), (72, 1), (67, 1), (69, 1), (69, 1), (67, 2), (76, 1), (76, 1), (74, 1), (74, 1), (72, 4)] * 2,
        chords="C C F C C G C C C C F C C G C C".split()),
    "ode": dict(bpm=104, notes=[(p, 1) for p in [76, 76, 77, 79, 79, 77, 76, 74, 72, 72, 74, 76]] + [(76, 1.5), (74, .5), (74, 2)]
                + [(p, 1) for p in [76, 76, 77, 79, 79, 77, 76, 74, 72, 72, 74, 76]] + [(74, 1.5), (72, .5), (72, 2)],
                chords="C C G G C C G G C C G G C C G C".split()),
    "yankee": dict(bpm=112, notes=[(p, 1) for p in [72, 72, 74, 76, 72, 76, 74, 67, 72, 72, 74, 76]] + [(72, 2), (71, 2)]
                   + [(p, 1) for p in [72, 72, 74, 76, 77, 76, 74, 72, 71, 67, 69, 71]] + [(72, 2), (72, 2)],
                   chords="C C C G C C C G C C F C G G C C".split()),
    "hotcross": dict(bpm=100, notes=[(76, 1), (74, 1), (72, 2)] * 2 + [(72, .5)] * 4 + [(74, .5)] * 4 + [(76, 1), (74, 1), (72, 2)],
                     chords="C C C C C G C C".split()),
}
GENTLE_SONGS = ["twinkle", "mary", "frere", "london", "macdonald", "ode", "yankee"]
VOICINGS = {"C": [60, 64, 67], "F": [60, 65, 69], "G": [59, 62, 67]}
BASS = {"C": (36, 43), "F": (41, 36), "G": (43, 38)}
PIANO, MUSIC_BOX, VIBES, MARIMBA, NYLON_GTR, AC_BASS, HARP, FLUTE, GLOCK = 0, 10, 11, 12, 24, 32, 46, 73, 9
CELESTA, XYLOPHONE, EPIANO, FINGER_BASS, STRINGS, WARM_PAD, STEEL_DRUMS, TIMPANI = 8, 13, 4, 33, 48, 89, 114, 47
DRUMS = 9
DANCE_BPM = 120


# ---------------------------------------------------------------- audio helpers
def read_wav(path):
    with wave.open(path) as w:
        ch = w.getnchannels()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return data.reshape(-1, ch)


_kokoro = None


def kokoro_model():
    """The full-precision model sounds cleaner; the int8 one is the small fallback."""
    for name, tag in (("kokoro-v1.0.onnx", "fp32"), ("kokoro-v1.0.int8.onnx", "int8")):
        if os.path.exists(os.path.join(KOKORO, name)):
            return name, tag
    raise SystemExit("no Kokoro model in assets/kokoro")


def voice_style(voice):
    """A Kokoro voice name, or a blend of voices such as "af_heart:0.6+af_nicole:0.4" (weights are normalised)."""
    if "+" not in voice:
        return voice
    parts = [(name, float(w or 1)) for name, _, w in (p.partition(":") for p in voice.split("+"))]
    total = sum(w for _, w in parts)
    return sum(_kokoro.get_voice_style(name) * (w / total) for name, w in parts)


def tts(text, voice=None, speed=SPEED, pitch=1.0):
    """Processed mono narration clip at SR (see audio.voice), with the raw TTS cached on disk by text.
    pitch > 1 raises pitch and tempo together (cartoon voices)."""
    global _kokoro
    voice = voice or VOICE
    model, tag = kokoro_model()
    cache = os.path.join(BUILD, "tts-cache", tag, voice)
    os.makedirs(cache, exist_ok=True)
    key = hashlib.sha1(f"{speed}|{text}".encode()).hexdigest()[:16]
    wav = os.path.join(cache, f"{key}.wav")
    import soundfile as sf

    if not os.path.exists(wav):
        from kokoro_onnx import Kokoro

        if _kokoro is None:
            _kokoro = Kokoro(os.path.join(KOKORO, model), os.path.join(KOKORO, "voices-v1.0.bin"))
        samples, sr = _kokoro.create(text, voice=voice_style(voice), speed=speed, lang="en-gb" if voice.startswith("b") else "en-us")
        sf.write(wav + ".tmp.wav", samples, sr, subtype="FLOAT")
        os.replace(wav + ".tmp.wav", wav)
    data, sr = sf.read(wav, dtype="float32")
    return audio.voice(data, sr, pitch)


class Midi:
    def __init__(self, bpm, humanize=True):
        self.bpm = bpm
        self.events = []
        self.rng = random.Random(bpm) if humanize else None

    def tick(self, sec):
        return round(sec * 480 * self.bpm / 60)

    def program(self, ch, prog, sec=0.0):
        self.events.append((self.tick(sec), 0, bytes([0xC0 | ch, prog])))

    def control(self, ch, cc, val):
        self.events.append((0, 0, bytes([0xB0 | ch, cc, val])))

    def note(self, ch, pitch, sec, length, vel):
        if self.rng:  # a player is never perfectly even
            vel = max(1, min(127, vel + self.rng.randint(-7, 7)))
            if ch != DRUMS:
                sec = max(0.0, sec + self.rng.uniform(-0.008, 0.008))
        self.events.append((self.tick(sec), 2, bytes([0x90 | ch, pitch, vel])))
        self.events.append((self.tick(sec + length), 1, bytes([0x80 | ch, pitch, 0])))

    def save(self, path):
        def vlq(n):
            out = [n & 0x7F]
            n >>= 7
            while n:
                out.insert(0, (n & 0x7F) | 0x80)
                n >>= 7
            return bytes(out)

        body = b"\x00\xff\x51\x03" + round(60_000_000 / self.bpm).to_bytes(3, "big")
        last = 0
        for t, _, data in sorted(self.events, key=lambda e: (e[0], e[1])):
            body += vlq(t - last) + data
            last = t
        body += b"\x00\xff\x2f\x00"
        with open(path, "wb") as fh:
            fh.write(b"MThd" + struct.pack(">IHHH", 6, 0, 1, 480))
            fh.write(b"MTrk" + struct.pack(">I", len(body)) + body)


def render_midi(midi, path_base, gain=0.6):
    midi.save(path_base + ".mid")
    subprocess.run(["fluidsynth", "-ni", "-q", "-g", str(gain), "-r", str(SR),
                    "-o", "synth.reverb.active=1", "-o", "synth.reverb.room-size=0.55", "-o", "synth.reverb.damp=0.4",
                    "-o", "synth.reverb.width=0.9", "-o", "synth.reverb.level=0.55", "-o", "synth.chorus.active=1",
                    "-o", "synth.chorus.level=1.2", "-F", path_base + ".wav", SOUNDFONT, path_base + ".mid"], check=True)
    return read_wav(path_base + ".wav")


def song_audio(name, length_s, lead_offset, work, style="gentle"):
    song = SONGS[name]
    bpm = {"gentle": song["bpm"], "lullaby": round(song["bpm"] * 0.72), "dance": DANCE_BPM}[style]
    beat = 60 / bpm
    loop_beats = sum(b for _, b in song["notes"])
    m = Midi(bpm)
    if style == "lullaby":
        leads = [MUSIC_BOX, CELESTA, HARP, VIBES]
        m.program(1, HARP)
        m.program(2, AC_BASS)
        m.program(3, WARM_PAD)
        vols = ((0, 90), (1, 70), (2, 60), (3, 55))
    elif style == "dance":
        leads = [XYLOPHONE, STEEL_DRUMS, MARIMBA, FLUTE, VIBES]
        m.program(1, EPIANO)
        m.program(2, FINGER_BASS)
        vols = ((0, 105), (1, 70), (2, 100), (DRUMS, 95))
    else:
        leads = [PIANO, MARIMBA, FLUTE, VIBES, MUSIC_BOX]
        m.program(1, NYLON_GTR)
        m.program(2, AC_BASS)
        vols = ((0, 100), (1, 80), (2, 90), (DRUMS, 70))
    for ch, vol in vols:
        m.control(ch, 7, vol)
    for ch, pan in ((0, 64), (1, 38), (2, 64), (3, 92), (DRUMS, 64)):
        m.control(ch, 10, pan)
    t, loop = 0.0, 0
    while t < length_s + 1:
        m.program(0, leads[(loop + lead_offset) % len(leads)], t)
        nt = t
        for pitch, b in song["notes"]:
            m.note(0, pitch, nt, b * beat * 0.95, 70 if style == "lullaby" else 84 if style == "dance" else 78)
            nt += b * beat
        for k, ch in enumerate(song["chords"]):
            at = t + k * 2 * beat
            v = VOICINGS[ch]
            root, fifth = BASS[ch]
            if style == "lullaby":
                for i, p in enumerate([v[0], v[1], v[2], v[1]]):
                    m.note(1, p, at + i * beat / 2, beat, 34)
                for p in v:
                    m.note(3, p - 12, at, 2 * beat, 30)
                m.note(2, root, at, 2 * beat * 0.9, 44)
            elif style == "dance":
                for i in range(4):  # off-beat chord stabs, octave-jumping bass
                    for p in v:
                        m.note(1, p, at + i * beat / 2 + beat / 4, beat / 5, 46)
                for i in range(4):
                    m.note(2, root + (12 if i % 2 else 0), at + i * beat / 2, beat * 0.4, 84)
            else:
                for i, p in enumerate([v[0], v[1], v[2], v[1]]):
                    m.note(1, p, at + i * beat / 2, beat / 2, 46)
                m.note(2, root, at, beat * 0.9, 72)
                m.note(2, fifth, at + beat, beat * 0.9, 60)
        for k in range(int(loop_beats)):
            at = t + k * beat
            if style == "dance":
                m.note(DRUMS, 36, at, 0.1, 92)
                if k % 2 == 1:
                    m.note(DRUMS, 39, at, 0.1, 64)
                m.note(DRUMS, 42, at, 0.05, 38)
                m.note(DRUMS, 42, at + beat / 2, 0.05, 48)
                if k == 0:
                    m.note(DRUMS, 49, at, 0.5, 60)
            elif style == "gentle":
                if k % 4 == 0:
                    m.note(DRUMS, 36, at, 0.1, 50)
                if k % 4 == 2:
                    m.note(DRUMS, 37, at, 0.1, 34)
                m.note(DRUMS, 70, at + beat / 2, 0.05, 26)
        t += loop_beats * beat
        loop += 1
    audio = render_midi(m, os.path.join(work, f"music-{name}-{style}-{lead_offset}"))
    n = int(length_s * SR)
    audio = np.pad(audio, ((0, max(0, n - len(audio))), (0, 0)))[:n]
    return audio / (np.max(np.abs(audio)) + 1e-9)


# ---------------------------------------------------------------- episode builder
class Builder:
    def __init__(self):
        self.t = 0.0
        self.voices = []  # (sec, clip)
        self.sfx = []  # (sec, kind)
        self.scenes = []
        self.chapters = []  # (sec, title)
        self.music = []  # (start, end, song, style)
        self.music_gain = 0.32
        self.mutes = []  # (start, end) of music silence

    def say(self, at, text, voice=None, speed=SPEED, pitch=1.0, gain=1.0):
        clip = tts(text, voice, speed, pitch) * gain
        self.voices.append((at, clip))
        return len(clip) / SR

    @staticmethod
    def f(sec):
        return round(sec * FPS)

    def scene(self, start, end, **data):
        self.scenes.append({"from": self.f(start), "duration": self.f(end) - self.f(start), **data})

    # -- generic pieces
    def section(self, sub, text, line, heroes):
        start = self.t
        self.sfx.append((start + 0.1, "sparkle"))
        d = self.say(start + 0.5, line)
        end = start + 0.5 + d + 0.9
        self.scene(start, end, type="section", sub=sub, text=text, heroes=heroes)
        self.t = end

    def review(self, heading, color, line, entries):
        """entries: (hero, label, spoken)"""
        start = self.t
        d = self.say(start + 0.5, line)
        cur = 0.5 + d + 0.4
        out = []
        for hero, label, spoken in entries:
            dd = self.say(start + cur, spoken)
            self.sfx.append((start + cur, "tick"))
            out.append({"hero": hero, "label": label, "at": self.f(cur)})
            cur += max(dd + 0.25, 0.95)
        end = start + cur + 0.8
        self.scene(start, end, type="review", heading={"text": heading, "color": color}, entries=out)
        self.t = end


def an(word):
    return "an" if word[0].lower() in "aeiou" else "a"


def seg_colors(b, rng, count):
    names = rng.sample(list(COLORS), count)
    b.section("Let's learn", "Colors!", "Let's learn colors!", [{"kind": "balloon", "value": "", "color": COLORS[n][0]} for n in names[:4]])
    for name in names:
        hexc, items = COLORS[name]
        start = b.t
        b.sfx.append((start + 0.15, "whoop"))
        cur = 0.9 + b.say(start + 0.9, f"{name}! The balloon is {name.lower()}!") + 0.35
        out = []
        for icon, label in rng.sample(items, 2):
            line = f"{name} {label}!" if label in NO_ARTICLE else f"{an(name).capitalize()} {name.lower()} {label}!"
            d = b.say(start + cur, line)
            b.sfx.append((start + cur, "pop"))
            out.append({"kind": "icon", "value": icon, "color": hexc, "label": label, "at": b.f(cur)})
            cur += d + 0.3
        end = start + cur + 0.9
        b.scene(start, end, type="focus", layout="pair", tint=hexc, title={"text": name.upper(), "color": hexc, "at": b.f(0.9)},
                hero={"kind": "balloon", "value": "", "color": hexc, "at": 0}, items=out)
        b.t = end
    b.review("All together!", "#FF6FB5", "Let's say them all together!",
             [({"kind": "balloon", "value": "", "color": COLORS[n][0]}, n, f"{n}!") for n in names])
    return names


def seg_numbers(b, rng, top):
    picks = rng.sample(COUNTABLES, len(COUNTABLES))
    b.section("Let's count", "1 to 10!", "Let's count from one to ten!",
              [{"kind": "number", "value": str(i), "color": PALETTE[i % 7]} for i in (1, 2, 3)])
    for n in range(1, top + 1):
        icon, one, many, color = picks[(n - 1) % len(picks)]
        color = color or rng.choice(PALETTE)
        word = NUMBER_WORDS[n]
        hexc = PALETTE[(n - 1) % 7]
        start = b.t
        b.sfx.append((start + 0.1, "whoop"))
        cur = 0.4 + b.say(start + 0.4, f"Number {word.lower()}!") + 0.3
        items = []
        for k in range(1, n + 1):
            d = b.say(start + cur, f"{NUMBER_WORDS[k]}!")
            b.sfx.append((start + cur, "pop"))
            items.append({"kind": "icon", "value": icon, "color": color, "at": b.f(cur)})
            cur += max(d + 0.12, 0.62)
        cap_at = cur + 0.15
        d = b.say(start + cap_at, f"{word} {one if n == 1 else many}!")
        end = start + cap_at + d + 0.8
        b.scene(start, end, type="focus", layout="count", tint=hexc, title={"text": word.upper(), "color": hexc, "at": b.f(0.4)},
                hero={"kind": "number", "value": str(n), "color": hexc, "at": 0}, items=items,
                caption={"text": f"{n} {one if n == 1 else many}", "at": b.f(cap_at)})
        b.t = end
    b.review("Count with me!", "#FF8A1F", "Let's count together!",
             [({"kind": "number", "value": str(i), "color": PALETTE[(i - 1) % 7]}, str(i), f"{NUMBER_WORDS[i]}!") for i in range(1, top + 1)])
    return top


def seg_shapes(b, rng, count):
    picks = rng.sample(SHAPES, count)
    colors = PALETTE[:]
    rng.shuffle(colors)
    b.section("Let's learn", "Shapes!", "Let's learn shapes!",
              [{"kind": "shape", "value": s, "color": colors[i]} for i, (s, _) in enumerate(picks[:4])])
    heroes = []
    for i, (shape, fact) in enumerate(picks):
        hexc = colors[i % 7]
        start = b.t
        b.sfx.append((start + 0.1, "whoop"))
        cur = 0.5 + b.say(start + 0.5, f"{shape.capitalize()}! This is {an(shape)} {shape}.") + 0.3
        others = [c for c in PALETTE if c != hexc]
        rng.shuffle(others)
        items = []
        for k in range(3):
            b.sfx.append((start + cur + k * 0.35, "pop"))
            items.append({"kind": "shape", "value": shape, "color": others[k], "at": b.f(cur + k * 0.35)})
        d = b.say(start + cur, fact)
        end = start + cur + max(d, 1.2) + 0.9
        hero = {"kind": "shape", "value": shape, "color": hexc}
        heroes.append(hero)
        b.scene(start, end, type="focus", layout="trio", tint=hexc, title={"text": shape.upper(), "color": hexc, "at": b.f(0.5)},
                hero={**hero, "at": 0}, items=items)
        b.t = end
    b.review("Shapes!", "#9B5CFF", "Can you say the shapes?", [(h, s.capitalize(), f"{s.capitalize()}!") for h, (s, _) in zip(heroes, picks)])
    return [s for s, _ in picks]


def seg_animals(b, rng, count):
    picks = rng.sample(ANIMALS, count)
    b.section("Let's meet the", "Animals!", "Let's meet the animals!",
              [{"kind": "icon", "value": a[0], "color": a[4]} for a in picks[:4]])
    for icon, name, sound, bubble, color in picks:
        start = b.t
        b.sfx.append((start + 0.1, "whoop"))
        d = b.say(start + 0.5, f"Who is this? It's {an(name)} {name}!")
        cur = 0.5 + d + 0.3
        d2 = b.say(start + cur, sound)
        end = start + cur + d2 + 0.9
        b.scene(start, end, type="focus", layout="animal", tint=color, title={"text": name.upper(), "color": color, "at": b.f(0.5 + d * 0.55)},
                hero={"kind": "icon", "value": icon, "color": color, "body": True, "at": 0}, items=[], bubble={"text": bubble, "at": b.f(cur)})
        b.t = end
    b.review("Animal friends!", "#3CC75A", "Let's say their names!",
             [({"kind": "icon", "value": a[0], "color": a[4]}, a[1].capitalize(), f"{a[1].capitalize()}!") for a in picks])
    return [a[1] for a in picks]


def seg_abc(b, rng, ep_no, count):
    """Walks through the alphabet across episodes, `count` letters at a time."""
    lo = ((ep_no - 1) * count) % 26
    picks = [LETTERS[(lo + i) % 26] for i in range(count)]
    b.section("Let's learn the", "ABC!", "Let's learn the ABCs!",
              [{"kind": "letter", "value": L[0], "color": PALETTE[i]} for i, L in enumerate(picks[:3])])
    for i, (letter, spoken, word, icon, color) in enumerate(picks):
        hexc = PALETTE[(lo + i) % 7]
        start = b.t
        b.sfx.append((start + 0.1, "whoop"))
        cur = 0.5 + b.say(start + 0.5, f"{spoken}!") + 0.35
        d = b.say(start + cur, f"{spoken} is for {word}!")
        b.sfx.append((start + cur + d * 0.6, "pop"))
        items = [{"kind": "icon", "value": icon, "color": color, "label": word, "at": b.f(cur + d * 0.6)}]
        end = start + cur + d + 1.0
        b.scene(start, end, type="focus", layout="letter", tint=hexc, title={"text": f"{letter} is for…", "color": hexc, "at": b.f(cur)},
                hero={"kind": "letter", "value": letter, "color": hexc, "at": 0}, items=items)
        b.t = end
    b.review("Letters!", "#2F8CFF", "Let's say the letters!",
             [({"kind": "letter", "value": L[0], "color": PALETTE[(lo + i) % 7]}, L[0], f"{L[1]}!") for i, L in enumerate(picks)])
    return picks[0][0], picks[-1][0]


SEGMENT_NAMES = {"colors": "Colors", "numbers": "Numbers", "shapes": "Shapes", "animals": "Animals", "abc": "ABC"}


SEASONS = {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring", 6: "summer", 7: "summer",
           8: "summer", 9: "autumn", 10: "autumn", 11: "autumn"}
SEGMENT_BGS = ["garden", "playground", "park", "beach", "farm", "day", "underwater"]  # each segment in its own place


def look_for(day, salt=""):
    """The season (from the date) and a seed for the sky and small details, so no two days look the same."""
    return SEASONS[day.month], (day.toordinal() * 7 + sum(map(ord, salt))) % 997


def build(day: dt.date, sizes):
    ep_no = (day - FIRST_EPISODE).days + 1
    rng = random.Random(f"bubbly-{ep_no}")
    order = list(SEGMENT_NAMES)
    rng.shuffle(order)
    songs = list(GENTLE_SONGS)
    rng.shuffle(songs)

    b = Builder()
    pretty = [SEGMENT_NAMES[s] for s in order]
    spoken = [("the ABCs" if s == "abc" else SEGMENT_NAMES[s].lower()) for s in order]

    # intro
    b.sfx.append((0.2, "whoop"))
    d = b.say(1.4, "Hello, friends! Welcome to Bubbly Kids TV!")
    d2 = b.say(1.4 + d + 0.3, f"Today, let's learn {', '.join(spoken[:-1])}, and {spoken[-1]}!")
    intro_end = 1.4 + d + 0.3 + d2 + 0.8
    title = [f"Learn {pretty[0]}", f"& {pretty[1]}!"]
    b.scene(0, intro_end, type="intro", title=title, heroes=[])
    b.chapters.append((0, "Hello friends!"))
    b.t = intro_end

    summary = {}
    for i, seg in enumerate(order):
        seg_start = b.t
        b.chapters.append((seg_start, {"colors": "Learn Colors", "numbers": "Count 1 to 10", "shapes": "Learn Shapes",
                                       "animals": "Animal Sounds", "abc": "ABC Letters"}[seg]))
        if seg == "colors":
            summary[seg] = seg_colors(b, rng, sizes["colors"])
        elif seg == "numbers":
            summary[seg] = seg_numbers(b, rng, 10)
        elif seg == "shapes":
            summary[seg] = seg_shapes(b, rng, sizes["shapes"])
        elif seg == "animals":
            summary[seg] = seg_animals(b, rng, sizes["animals"])
        else:
            summary[seg] = seg_abc(b, rng, ep_no, sizes["letters"])
        b.music.append((0 if i == 0 else seg_start, b.t, songs[i % len(songs)]))
        place = SEGMENT_BGS[(i + ep_no) % len(SEGMENT_BGS)]
        for sc in b.scenes:
            if sc["from"] >= b.f(seg_start) and "bg" not in sc:
                sc["bg"] = place

    # outro
    start = b.t
    b.chapters.append((start, "Bye bye!"))
    b.sfx.append((start + 0.3, "ding"))
    b.sfx.append((start + 0.5, "cheer"))
    d = b.say(start + 0.3, "Great job today! You are so smart!")
    bye_at = 0.3 + d + 0.35
    d2 = b.say(start + bye_at, "Bye bye! See you tomorrow!")
    end = start + bye_at + d2 + 2.6
    b.scene(start, end, type="outro", byeAt=b.f(bye_at), heroes=[])
    s0, _, song = b.music[-1]
    b.music[-1] = (s0, end, song)
    b.t = end
    return b, order, summary, ep_no


MUSIC_LEVEL = 3.2  # music bus gain on top of b.music_gain (kids channels keep the music up front)
DUCK_DEPTH = 0.3  # how far the music dips under speech (0 = not at all, 1 = silent)


def mix(b: Builder, work, music_level=None, duck_depth=None):
    total = b.t
    n = int(total * SR)
    xf = int(0.6 * SR)
    music = np.zeros((n, 2), dtype=np.float32)
    for i, (s, e, song, *style) in enumerate(b.music):
        # a song name from SONGS, or a function (length_s, work) -> stereo music for other channels' own tracks
        a = song(e - s + 0.6, work) if callable(song) else song_audio(song, e - s + 0.6, i, work, *style)
        i0 = int(s * SR)
        seg = a[: max(0, min(len(a), n - i0))]
        ramp = np.ones(len(seg), dtype=np.float32)
        if i > 0:
            ramp[:xf] = np.linspace(0, 1, xf)
        if i < len(b.music) - 1:
            tail = min(xf, len(seg))
            ramp[-tail:] = np.minimum(ramp[-tail:], np.linspace(1, 0, tail))
        music[i0:i0 + len(seg)] += seg * ramp[:, None]

    voice = np.zeros(n, dtype=np.float32)
    for at, clip in b.voices:
        i = int(at * SR)
        j = min(n, i + len(clip))
        voice[i:j] += clip[: j - i]
    fx = audio.render_sfx(b.sfx, n)

    # music dips under speech: fast attack, slow release, so it breathes back between lines
    speaking = audio.envelope(voice, SR, attack=0.05, release=0.45)
    duck = 1.0 - (DUCK_DEPTH if duck_depth is None else duck_depth) * np.clip(speaking / 0.05, 0, 1)
    fade = np.minimum(1, (n - np.arange(n)) / (2.5 * SR))
    for ms, me in b.mutes:
        i0, i1 = int(ms * SR), int(me * SR)
        fade[i0:i1] = 0
        fade[max(0, i0 - 400):i0] *= np.linspace(1, 0, min(400, i0))
    music = audio.highpass(music, SR, 40)
    music = audio.eq(music, SR, "peak", 3000, -2.5, 0.7)  # leave room for the voice
    level = MUSIC_LEVEL if music_level is None else music_level
    out = music * (b.music_gain * level * duck * fade)[:, None] + voice[:, None] * 0.9 + fx * 0.55
    return audio.master(out, SR)


def fmt(sec):
    sec = int(sec)
    return f"{sec // 60}:{sec % 60:02d}"


def metadata(b, order, summary, ep_no):
    pretty = [SEGMENT_NAMES[s] for s in order]
    title = f"Learn {', '.join(pretty[:-1])} & {pretty[-1]} for Kids | Toddler Learning Video | Bubbly Kids TV"
    lines = {
        "colors": "🎨 Colors: " + ", ".join(summary["colors"]),
        "numbers": "🔢 Numbers: counting from 1 to 10",
        "shapes": "🔷 Shapes: " + ", ".join(s.capitalize() for s in summary["shapes"]),
        "animals": "🐮 Animal sounds: " + ", ".join(a.capitalize() for a in summary["animals"]),
        "abc": f"🔤 Letters: {summary['abc'][0]} to {summary['abc'][1]}",
    }
    desc = [
        f"Episode {ep_no} of Bubbly Kids TV! 🎈 Learn {', '.join(p.lower() if p != 'ABC' else 'the ABC' for p in pretty[:-1])} "
        f"and {pretty[-1].lower() if pretty[-1] != 'ABC' else 'the ABC'} with our smiling balloon friends, gentle music and nursery rhymes.",
        "",
        *[lines[s] for s in order],
        "",
        "⏱ Chapters",
        *[f"{fmt(t)} {name}" for t, name in b.chapters],
        "",
        "New learning videos for toddlers and preschoolers every day!",
        "",
        "#kidslearning #toddlerlearning #learncolors #abc #nurseryrhymes",
    ]
    tags = ["kids learning video", "toddler learning", "preschool", "learn colors", "learn numbers", "counting 1 to 10",
            "learn shapes", "animal sounds", "abc", "alphabet", "nursery rhymes", "kids songs", "bubbly kids tv"]
    return {"title": title[:100], "description": "\n".join(desc), "tags": tags}


def write_audio(b, work, name):
    """Mixes the episode audio into public/audio/<name>.wav and returns its path for staticFile()."""
    audio = mix(b, work)
    os.makedirs(AUDIO_DIR, exist_ok=True)
    for old in glob.glob(os.path.join(AUDIO_DIR, "*.wav")):
        os.remove(old)  # keep the Remotion bundle small
    wav_rel = f"audio/{name}.wav"
    with wave.open(os.path.join(ROOT, "public", wav_rel), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((audio * 32767).astype(np.int16).tobytes())
    return wav_rel


def write_json(work, props, meta):
    with open(os.path.join(work, "props.json"), "w") as fh:
        json.dump(props, fh)
    with open(os.path.join(work, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=dt.date.today().isoformat())
    a = p.parse_args()
    day = dt.date.fromisoformat(a.date)
    work = os.path.join(BUILD, a.date)
    os.makedirs(work, exist_ok=True)

    sizes = {"colors": 6, "shapes": 6, "animals": 6, "letters": 7}
    limits = {"colors": 8, "shapes": 8, "animals": 10, "letters": 13}
    while True:
        b, order, summary, ep_no = build(day, sizes)
        if b.t >= MIN_SECONDS or sizes == limits:
            break
        sizes = {k: min(limits[k], v + 1) for k, v in sizes.items()}

    wav_rel = write_audio(b, work, a.date)
    first_heroes = []
    for s in b.scenes:
        if s["type"] == "focus" and len(first_heroes) < 5 and not any(h.get("_seg") == s["layout"] for h in first_heroes):
            first_heroes.append({**{k: v for k, v in s["hero"].items() if k != "at"}, "_seg": s["layout"]})
    thumb_heroes = [{k: v for k, v in h.items() if k != "_seg"} for h in first_heroes]
    pretty = [SEGMENT_NAMES[s] for s in order]
    props = {
        "durationInFrames": b.f(b.t),
        "audio": wav_rel,
        "scenes": b.scenes,
        "thumb": {"title": ["Learn & Play!", " • ".join(pretty[:3])], "heroes": thumb_heroes},
        "season": look_for(day)[0],
        "look": look_for(day)[1],
    }
    write_json(work, props, metadata(b, order, summary, ep_no))
    print(f"episode {ep_no} {a.date}: {b.t:.1f}s, order={order}, {len(b.voices)} lines")


if __name__ == "__main__":
    main()
