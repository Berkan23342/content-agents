"""Plans and voices one Brain Snack, the Brain Snack Quiz channel's format since 2026-11-08: one topic told in about a
minute, a different format every day.

  why      a curious question explained step by step, with a guess and a bonus fact
  how      how an everyday thing works, taken apart step by step
  mystery  a little riddle told as a story: suspects, clues, the viewer's guess, the solution
  myth     a common belief tested: myth or fact?
  real     a real-life "what would you do?" with the right answer and why
  whatif   "what if...?": what would really happen, step by step
  teaser   a logic puzzle: the viewer thinks, then the solution step by step
  origin   the story behind an everyday thing or word

One format a day, in turns (scripts/snackcheck.py ROTATION); each has its own host, look and colours.

Scripts come from snacks/new/ (written by the snack writer routine, see AGENT.md); after building, the script moves to
snacks/used/<date>/. The host is voiced by Chatterbox (outbreak-channel/scripts/voice_cb.py in its own environment),
copying the host's voice in voices/ (one per format, see HOSTS); the music, sounds and mix come from the kids channel's scripts.

  ../kids-channel/.venv/bin/python scripts/snack.py --date 2026-11-09 [--file snacks/new/x.json] [--keep]
"""
import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import random
import subprocess
import sys
import tempfile
import wave

import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(REPO, "kids-channel", "scripts"))
sys.path.insert(0, os.path.join(REPO, "shared"))

import audio  # noqa: E402
from captions import chunks_for  # noqa: E402
from episode import SR, Builder, mix  # noqa: E402
from quiz import quiz_music  # noqa: E402
from snackcheck import SnackError, check_against, check_snack, format_for  # noqa: E402

BUILD = os.path.join(ROOT, "build")
SNACKS = os.path.join(ROOT, "snacks")
CB_PYTHON = os.environ.get("CB_PYTHON", os.path.join(REPO, "outbreak-channel", ".venv-cb", "bin", "python"))
VOICE_CB = os.path.join(REPO, "outbreak-channel", "scripts", "voice_cb.py")
THINK = 3.0  # seconds to guess
# Every format has its own host (a female voice made by scripts/make_voices.py, copied by Chatterbox), its own look and
# its own colours; within a format, each snack still draws its colours, cards and transitions at random.
HOSTS = {  # format -> (voice, exaggeration, cfg)
    "why": ("bella", 0.7, 0.5), "how": ("sarah", 0.6, 0.5), "mystery": ("emma", 0.55, 0.45), "myth": ("aoede", 0.7, 0.5),
    "real": ("kore", 0.6, 0.5), "whatif": ("sky", 0.65, 0.5), "teaser": ("alice", 0.6, 0.5), "origin": ("lily", 0.55, 0.45),
}
LOOKS = {  # format -> (background, heading fonts, caption fonts); see src/Snack.tsx
    "why": ("blobs", ["lilita", "fredoka"], ["anton", "bebas"]),
    "how": ("grid", ["righteous", "archivo"], ["bebas", "oswald"]),
    "mystery": ("spotlight", ["elite", "archivo"], ["oswald", "bebas"]),
    "myth": ("stripes", ["bangers", "lilita"], ["bangers", "anton"]),
    "real": ("dots", ["fredoka", "lilita"], ["anton", "oswald"]),
    "whatif": ("stars", ["righteous", "bungee"], ["bebas", "anton"]),
    "teaser": ("chalk", ["marker", "fredoka"], ["marker", "anton"]),
    "origin": ("paper", ["archivo", "elite"], ["oswald", "anton"]),
}
CARDS = ["round", "sticker", "square"]
MOVES = ["rise", "slide", "zoom"]
THEMES = {  # several colourings per format
    "why": [("#2563EB", "#7C3AED", "#FACC15"), ("#0EA5E9", "#2563EB", "#FDE047"), ("#4F46E5", "#DB2777", "#FCD34D")],
    "how": [("#0B3B66", "#1D4ED8", "#FDE047"), ("#0F4C5C", "#155E75", "#FCD34D"), ("#1E3A8A", "#0E7490", "#FDBA74")],
    "mystery": [("#0F172A", "#4C1D95", "#F59E0B"), ("#134E4A", "#1E3A8A", "#FBBF24"), ("#3B0764", "#0F172A", "#F472B6")],
    "myth": [("#BE185D", "#6D28D9", "#A3E635"), ("#1E40AF", "#BE123C", "#FDE047"), ("#065F46", "#7E22CE", "#FCD34D")],
    "real": [("#EA580C", "#DB2777", "#FDE047"), ("#16A34A", "#0D9488", "#FDE047"), ("#DC2626", "#9333EA", "#FCD34D")],
    "whatif": [("#020617", "#312E81", "#38BDF8"), ("#0C0A09", "#4C1D95", "#F0ABFC"), ("#020617", "#164E63", "#FDE047")],
    "teaser": [("#14532D", "#1C3D2A", "#FDE047"), ("#1F2937", "#111827", "#F9A8D4"), ("#1E3A2F", "#0F2A1F", "#93C5FD")],
    "origin": [("#78350F", "#451A03", "#FCD34D"), ("#7C2D12", "#3F1D0B", "#FDBA74"), ("#57534E", "#292524", "#FDE68A")],
}
OUTRO = {  # the host's last line (short, and it invites a comment), then the end card asks to follow
    "why": "Did you guess right? Tell me below!",
    "how": "Did you know that? Tell me below!",
    "mystery": "Did you crack the case? Comment below!",
    "myth": "Did you believe it? Be honest, below!",
    "real": "What would you have done? Comment below!",
    "whatif": "Wild, right? What should I imagine next?",
    "teaser": "Did you solve it in time? Comment below!",
    "origin": "Did you know that story? Tell me below!",
}
TAGS = {"why": ["science", "fun facts", "why", "explained"], "how": ["how it works", "how things work", "explained", "engineering"],
        "myth": ["myth or fact", "myths busted", "true or false", "fun facts"], "mystery": ["riddle", "mystery", "detective", "can you solve it"],
        "real": ["life hacks", "what would you do", "safety tips", "real life"], "whatif": ["what if", "science", "hypothetical", "explained"],
        "teaser": ["brain teaser", "logic puzzle", "riddle", "can you solve it"], "origin": ["history", "origin story", "the story behind", "did you know"]}
NAMES = {"why": "Why?", "how": "How it works", "mystery": "Mystery", "myth": "Myth or Fact", "real": "Real life",
         "whatif": "What if?", "teaser": "Brain teaser", "origin": "The story behind"}


def voice_cache(text, host):
    name, ex, cfg = host
    key = hashlib.sha1(f"{ex}|{cfg}|{text}".encode()).hexdigest()[:16]
    return os.path.join(BUILD, "cb-cache", name, f"{key}.wav")


def speak_all(texts, host):
    jobs = []
    for text in dict.fromkeys(texts):
        out = voice_cache(text, host)
        if not os.path.exists(out):
            os.makedirs(os.path.dirname(out), exist_ok=True)
            jobs.append({"text": text, "ref": os.path.join(ROOT, "voices", f"{host[0]}.wav"), "out": out,
                         "exaggeration": host[1], "cfg": host[2], "seed": 11})
    if jobs:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(jobs, fh)
        subprocess.run([CB_PYTHON, VOICE_CB, fh.name], check=True)
        os.remove(fh.name)


def clip(text, host):
    data, sr = sf.read(voice_cache(text, host), dtype="float32")
    return audio.voice(data, sr)


def take_snack(date):
    """The script this date already used (a re-run), else the oldest waiting one, preferring the day's format."""
    used = sorted(glob.glob(os.path.join(SNACKS, "used", date, "*.json")))
    if used:
        return used[0]
    want = format_for(date)
    waiting = []
    for path in sorted(glob.glob(os.path.join(SNACKS, "new", "*.json"))):
        try:
            spec = json.load(open(path))
            check_snack(spec)
            check_against(path, spec, topics=False)
        except (SnackError, json.JSONDecodeError) as e:
            print(f"skipping {os.path.basename(path)}: {e}")
            continue
        waiting.append((spec["format"] != want, path))
    if not waiting:
        raise SystemExit("no snack script waiting in snacks/new")
    return min(waiting)[1]


def build(spec, seed):
    b = Builder()
    host = HOSTS[spec["format"]]
    texts = [x for beat in spec["beats"] for x in (beat["text"], beat.get("reveal")) if x]
    outro = OUTRO[spec["format"]]
    speak_all(texts + [outro], host)

    def say(at, text):
        c = clip(text, host)
        b.voices.append((at, c))
        return len(c) / SR

    beats, chunks = [], []
    choice = next(beat["visual"] for beat in spec["beats"] if beat["visual"]["kind"] == "choice")
    cur = 0.0  # the hook starts at once: no title, the first frame already asks the question
    for i, beat in enumerate(spec["beats"]):
        start = cur
        v = dict(beat["visual"])
        if i == 0 and v["kind"] == "hook":  # the choice's answers are on screen from the first frame (not which is right)
            v["options"] = [{"emoji": o["emoji"], "label": o.get("label", "")} for o in choice["options"]]
        b.sfx.append((start + 0.05, "whoosh"))
        lead = 0.05 if i == 0 else 0.15
        d = say(start + lead, beat["text"])
        chunks += chunks_for(beat["text"], beat.get("hl", []), start + lead + 0.02, start + lead + d, b.f)
        end = start + lead + d + 0.35
        if v["kind"] in ("steps", "clues", "scale"):
            n = len(v["items"])
            for i in range(n):
                b.sfx.append((start + min(d * 0.55, n * 0.8) * i / n + 0.1, "pop"))
        if v["kind"] == "choice":
            timer = 0.15 + d + 0.2
            for k in range(int(THINK)):
                b.sfx.append((start + timer + k, "tick"))
            reveal = timer + THINK
            b.sfx.append((start + reveal, "ding"))
            b.sfx.append((start + reveal + 0.05, "sparkle"))
            d2 = say(start + reveal + 0.2, beat["reveal"])
            chunks += chunks_for(beat["reveal"], beat.get("hl", []), start + reveal + 0.22, start + reveal + 0.2 + d2, b.f)
            v.update(timerAt=b.f(timer), timerLen=b.f(timer + THINK) - b.f(timer), revealAt=b.f(reveal))
            end = start + reveal + 0.2 + d2 + 0.5
        if v["kind"] == "suspects" and v.get("pick") is not None:
            v["revealAt"] = b.f(0.15 + d * 0.5)
            b.sfx.append((start + 0.15 + d * 0.5, "sparkle"))
        beats.append({"from": b.f(start), "duration": b.f(end) - b.f(start), "visual": v})
        cur = end
    end_at = cur
    b.sfx.append((end_at + 0.1, "cheer"))
    d = say(end_at + 0.2, outro)
    chunks += chunks_for(outro, [], end_at + 0.22, end_at + 0.2 + d, b.f)
    b.t = end_at + 0.2 + d + 0.8
    beats[-1]["duration"] = b.f(b.t) - beats[-1]["from"]  # the last visual stays under the end card
    rng = random.Random(seed)
    b.music = [(0, b.t, lambda length, work: quiz_music(length, work, f"snack-{seed}"))]
    b.music_gain = 0.18
    a, c, accent = rng.choice(THEMES[spec["format"]])
    bg, heads, caps = LOOKS[spec["format"]]
    look = {"bg": bg, "head": rng.choice(heads), "caption": rng.choice(caps), "card": rng.choice(CARDS), "move": rng.choice(MOVES),
            "seed": rng.randrange(1000)}
    props = {"durationInFrames": b.f(b.t), "format": spec["format"], "title": spec["title"],
             "theme": {"a": a, "b": c, "accent": accent}, "look": look, "beats": beats, "chunks": chunks, "endAt": b.f(end_at)}
    meta = {
        "title": f"{spec['title']} 🧠 #shorts"[:100],
        "description": "\n".join([spec["summary"], "",
                                  f"Today's format: {NAMES[spec['format']]}. A new Brain Snack every day!",
                                  "Tell us in the comments what we should explain next!", "",
                                  "#shorts #brainsnack #" + TAGS[spec["format"]][0].replace(" ", "")]),
        "tags": TAGS[spec["format"]] + ["brain snack", "learn something new", "shorts"],
    }
    return b, props, meta


def write_audio(b, work, name):
    data = mix(b, work)
    folder = os.path.join(ROOT, "public", "audio")
    os.makedirs(folder, exist_ok=True)
    for old in glob.glob(os.path.join(folder, "*.wav")):
        os.remove(old)
    with wave.open(os.path.join(folder, f"{name}.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((data * 32767).astype(np.int16).tobytes())
    return f"audio/{name}.wav"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=dt.date.today().isoformat())
    p.add_argument("--file", help="build this script instead of the next waiting one")
    p.add_argument("--keep", action="store_true", help="leave the script in snacks/new (for previews)")
    a = p.parse_args()
    path = a.file or take_snack(a.date)
    spec = json.load(open(path))
    try:
        check_snack(spec)
    except SnackError as e:
        raise SystemExit(f"snack error in {path}: {e}")
    name = f"{a.date}-snack"
    work = os.path.join(BUILD, name)
    os.makedirs(work, exist_ok=True)
    b, props, meta = build(spec, f"{a.date}-{spec['title']}")
    props["audio"] = write_audio(b, work, name)
    with open(os.path.join(work, "props.json"), "w") as fh:
        json.dump(props, fh, ensure_ascii=False)
    with open(os.path.join(work, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
    used = os.path.join(SNACKS, "used", a.date)
    if not a.keep and os.path.dirname(os.path.abspath(path)) != used:
        os.makedirs(used, exist_ok=True)
        os.rename(path, os.path.join(used, os.path.basename(path)))
    print(f"snack {spec['format']} {a.date}: {spec['title']!r}, {b.t:.1f}s, {len(props['beats'])} beats")


if __name__ == "__main__":
    main()
