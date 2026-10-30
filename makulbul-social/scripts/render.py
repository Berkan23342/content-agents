"""Renders one day's content folder into a reel and a post.

  python3 scripts/render.py content/2026-10-31

Reads content/<day>/spec.json (see AGENT.md), writes reel.mp4 (1080x1920, with an original
background track made with FluidSynth) and post.png (1080x1350) into the same folder.
"""
import glob
import hashlib
import json
import os
import random
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUNDFONT = os.environ.get("SOUNDFONT", os.path.join(ROOT, "..", "kids-channel", "assets", "soundfont", "GeneralUser-GS.sf2"))
FPS = 30
DRUMS = 9


def reel_frames(spec):
    # keep in sync with reelFrames() in src/formats.tsx
    f = spec["format"]
    cta = 66
    if f == "compare":
        return 66 + 42 * len(spec["rows"]) + 80 + cta
    if f == "myth":
        return 120 + 38 * len(spec["points"]) + 45 + cta
    if f == "versus":
        return 190 + cta
    if f == "tips":
        return 55 + 66 * len(spec["items"]) + cta
    return 165 + cta


class Midi:
    def __init__(self, bpm):
        self.bpm = bpm
        self.events = []

    def tick(self, sec):
        return round(sec * 480 * self.bpm / 60)

    def add(self, sec, order, data):
        self.events.append((self.tick(sec), order, bytes(data)))

    def note(self, ch, pitch, sec, length, vel):
        self.add(sec, 2, [0x90 | ch, pitch, vel])
        self.add(sec + length, 1, [0x80 | ch, pitch, 0])

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


PROGRESSIONS = [  # roots (MIDI) of four-bar loops, minor/major triads
    [(57, "m"), (53, ""), (48, ""), (55, "")],  # Am F C G
    [(48, ""), (55, ""), (57, "m"), (53, "")],  # C G Am F
    [(50, "m"), (46, ""), (53, ""), (48, "")],  # Dm Bb F C
    [(52, "m"), (48, ""), (55, ""), (50, "")],  # Em C G D
    [(45, "m"), (53, ""), (48, ""), (52, "m")],  # Am F C Em
]
PADS = [4, 5, 89, 90]  # e-pianos, warm pad, polysynth
PLUCKS = [12, 11, 13, 46, 108]  # marimba, vibes, xylophone, harp, kalimba


def music(seconds, seed, path):
    """An original, upbeat background loop for a reel (no samples, no third-party tracks)."""
    rng = random.Random(seed)
    bpm = rng.choice([112, 116, 120, 124])
    beat = 60 / bpm
    prog = rng.choice(PROGRESSIONS)
    m = Midi(bpm)
    m.add(0, 0, [0xC0 | 1, 38])  # synth bass
    m.add(0, 0, [0xC0 | 2, rng.choice(PADS)])
    m.add(0, 0, [0xC0 | 3, rng.choice(PLUCKS)])
    for ch, vol in ((1, 92), (2, 62), (3, 78), (DRUMS, 92)):
        m.add(0, 0, [0xB0 | ch, 7, vol])
    arp = rng.choice([[0, 7, 12, 7], [0, 4, 7, 12], [12, 7, 4, 0], [0, 7, 4, 7]])
    t, bar = 0.0, 0
    while t < seconds + 2:
        root, q = prog[bar % 4]
        third = 3 if q == "m" else 4
        chord = [root + 12, root + 12 + third, root + 19]
        for p in chord:
            m.note(2, p, t, 4 * beat * 0.95, 44)
        for k in range(8):
            m.note(1, root - 12 + (12 if k % 4 == 3 else 0), t + k * beat / 2, beat * 0.4, 88)
        if bar >= 1:
            for k in range(8):
                step = arp[k % 4]
                m.note(3, root + 24 + (third if step == 4 else step), t + k * beat / 2, beat * 0.45, 58 + (8 if k % 2 == 0 else 0))
        for k in range(4):
            at = t + k * beat
            m.note(DRUMS, 36, at, 0.1, 96)
            if k % 2:
                m.note(DRUMS, 39, at, 0.1, 70)
            m.note(DRUMS, 42, at + beat / 2, 0.05, 50)
            m.note(DRUMS, 42, at, 0.05, 32)
        if bar % 4 == 3:
            m.note(DRUMS, 46, t + 3.5 * beat, 0.3, 50)
        t += 4 * beat
        bar += 1
    # fade out over the last 1.5 s
    for k in range(16):
        at = seconds - 1.5 + k * 0.1
        for ch in (1, 2, 3, DRUMS):
            m.add(at, 0, [0xB0 | ch, 7, max(0, int((92 if ch in (1, DRUMS) else 70) * (1 - k / 15)))])
    mid = path.replace(".wav", ".mid")
    m.save(mid)
    subprocess.run(["fluidsynth", "-ni", "-q", "-g", "0.7", "-r", "44100", "-F", path, SOUNDFONT, mid], check=True)
    os.remove(mid)


def remotion(*args):
    for attempt in range(3):
        if subprocess.run(["npx", "remotion", *args, "--timeout=120000", "--log=error"], cwd=ROOT).returncode == 0:
            return
        print(f"remotion attempt {attempt + 1} failed")
    raise SystemExit("render failed")


def main():
    day_dir = os.path.abspath(sys.argv[1])
    day = os.path.basename(day_dir)
    with open(os.path.join(day_dir, "spec.json")) as fh:
        spec = json.load(fh)
    seconds = reel_frames(spec) / FPS

    audio_dir = os.path.join(ROOT, "public", "audio")
    os.makedirs(audio_dir, exist_ok=True)
    for old in glob.glob(os.path.join(audio_dir, "*.wav")):
        os.remove(old)
    seed = int(hashlib.sha1(day.encode()).hexdigest()[:8], 16)
    music(seconds, seed, os.path.join(audio_dir, f"{day}.wav"))

    props = os.path.join(day_dir, "props.json")
    with open(props, "w") as fh:
        json.dump({**spec, "audio": f"audio/{day}.wav"}, fh, ensure_ascii=False)
    remotion("render", "src/index.tsx", "Reel", os.path.join(day_dir, "reel.mp4"), f"--props={props}")
    remotion("still", "src/index.tsx", "Post", os.path.join(day_dir, "post.png"), f"--props={props}")
    print(f"rendered {day}: reel {seconds:.1f}s + post")


if __name__ == "__main__":
    main()
