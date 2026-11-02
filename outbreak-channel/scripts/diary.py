"""Plans and voices one Outbreak Diary episode: a vertical 45-65 second part of a serialized zombie survival story.

The channel runs several stories side by side; story/series.json lists them, each with its own narrator.
The episode script comes from story/<series>/new/ (the lowest episode number first), written by the story writer
routine (see AGENT.md and story/<series>/bible.md). After building, it moves to story/<series>/used/<date>/.
Part N of a story is always Day N.
The narrator (always a woman) and any characters who speak are voiced by Chatterbox (scripts/voice_cb.py, run in its
own Python environment), copying the voices in voices/*.wav; mixing and the master come from the kids channel's scripts
(kids-channel/scripts/episode.py and audio.py); the horror sounds and the score are in scripts/dread.py.

Writes build/<id>/{props,meta}.json and public/audio/<id>.wav.
Run with ../kids-channel/.venv/bin/python scripts/diary.py --series harbor-view --id 2026-11-02-e1 [--file ...] [--keep]
"""
import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import wave

import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "kids-channel", "scripts"))

import audio  # noqa: E402
from episode import SR, Builder, mix  # noqa: E402
import dread  # noqa: E402,F401  (registers the horror sounds)
from diarycheck import DiaryError, check_episode, sfx_name  # noqa: E402

BUILD = os.path.join(ROOT, "build")
PUBLIC = os.path.join(ROOT, "public")
STORY = os.path.join(ROOT, "story")
SERIES = {s["id"]: s for s in json.load(open(os.path.join(STORY, "series.json")))}
VOICES = os.path.join(ROOT, "voices")
CB_PYTHON = os.environ.get("CB_PYTHON", os.path.join(ROOT, ".venv-cb", "bin", "python"))
EXAGGERATION = 0.55  # Chatterbox: how dramatic the delivery is
CFG = 0.45  # Chatterbox: lower is slower and more deliberate
GAP = 0.35  # silence after each beat
END_CARD = 2.8
SHAKES = {"bang", "thud", "glass", "sting"}


def voice_cache(voice, text):
    key = hashlib.sha1(f"{EXAGGERATION}|{CFG}|{text}".encode()).hexdigest()[:16]
    return os.path.join(BUILD, "cb-cache", voice, f"{key}.wav")


def speak_all(lines):
    """Makes every (voice, text) line that is not cached yet, in one Chatterbox run."""
    jobs = []
    for voice, text in dict.fromkeys(lines):
        out = voice_cache(voice, text)
        if not os.path.exists(out):
            os.makedirs(os.path.dirname(out), exist_ok=True)
            jobs.append({"text": text, "ref": os.path.join(VOICES, f"{voice}.wav"), "out": out,
                         "exaggeration": EXAGGERATION, "cfg": CFG, "seed": 7})
    if not jobs:
        return
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(jobs, fh)
    subprocess.run([CB_PYTHON, os.path.join(ROOT, "scripts", "voice_cb.py"), fh.name], check=True)
    os.remove(fh.name)


def clip(voice, text):
    data, sr = sf.read(voice_cache(voice, text), dtype="float32")
    return audio.voice(data, sr)


def take_episode(series, vid):
    """The script this video already used (on a re-run), else the lowest episode waiting in story/<series>/new."""
    date, _, slot = vid.rpartition("-")
    used = sorted(glob.glob(os.path.join(STORY, series, "used", date, f"{slot}-*.json")))
    if used:
        return used[0]
    waiting = []
    for path in glob.glob(os.path.join(STORY, series, "new", "*.json")):
        try:
            spec = json.load(open(path))
            check_episode(spec, SERIES[series]["cast"])
        except (DiaryError, json.JSONDecodeError) as e:
            print(f"skipping {os.path.basename(path)}: {e}")
            continue
        waiting.append((spec["episode"], path))
    if not waiting:
        raise SystemExit(f"no episode script in story/{series}/new")
    return min(waiting)[1]


def chunks_for(text, hl, t0, t1, f, talk=False):
    """Splits a line into 1-3 word captions, timed by word length and punctuation across [t0, t1] seconds."""
    tokens = text.split()
    weights = []
    for w in tokens:
        k = len(re.sub(r"[^A-Za-z0-9]", "", w)) + 2
        k += 6 if w.endswith("...") else 5 if w[-1] in ".!?" else 3 if w[-1] in ",;:" else 0
        weights.append(k)
    edges = np.concatenate([[0], np.cumsum(weights)]) / sum(weights) * (t1 - t0) + t0
    marked = {w.lower() for h in hl for w in re.findall(r"[A-Za-z0-9']+", h)}
    out, cur = [], []
    for i, w in enumerate(tokens):
        cur.append(i)
        if len(cur) == 3 or len(" ".join(tokens[j] for j in cur)) > 14 or w[-1] in ".!?,;:" or i == len(tokens) - 1:
            out.append(cur)
            cur = []
    chunks = []
    for k, idx in enumerate(out):
        at = edges[idx[0]]
        until = edges[out[k + 1][0]] if k + 1 < len(out) else edges[idx[-1] + 1] + 0.3
        ws = [tokens[j] for j in idx]
        chunks.append({"words": ws, "hl": [re.sub(r"[^A-Za-z0-9']", "", w).lower() in marked for w in ws],
                       "at": f(at), "until": f(until), "talk": talk})
    return chunks


def build(spec, series):
    b = Builder()
    lines = [(beat.get("speaker", series["narrator"]), beat["text"]) for beat in spec["beats"]]
    speak_all(lines)

    def say(at, voice, text):
        c = clip(voice, text)
        b.voices.append((at, c))
        return len(c) / SR

    beats, chunks = [], []
    b.sfx.append((0.05, "thud"))
    cur = 0.3
    scenes = [x["scene"] for x in spec["beats"]]
    sting_at = None
    for i, beat in enumerate(spec["beats"]):
        start = cur
        voice, text = lines[i]
        d = say(start + 0.1, voice, text)
        chunks += chunks_for(text, beat.get("hl", []), start + 0.12, start + 0.1 + d, b.f, "speaker" in beat)
        hits = []
        for s in beat.get("sfx", []):
            name = sfx_name(s)
            at = float(str(s).partition("@")[2] or 0.1)
            b.sfx.append((start + at, name))
            if name in SHAKES:
                hits.append(b.f(at))
        last = i == len(spec["beats"]) - 1
        end = start + 0.1 + d + float(beat.get("hold", GAP))
        if last:
            sting_at = start + 0.1 + d + 0.15
            if "sting" not in [sfx_name(s) for s in beat.get("sfx", [])]:
                b.sfx.append((sting_at, "sting"))
                hits.append(b.f(sting_at - start))
            end = sting_at + 0.6 + END_CARD
        params = {k: v for k, v in beat.items() if k not in ("scene", "text", "hl", "sfx", "cam", "tone", "rain", "fog",
                                                              "flashlight", "alarm", "hold", "speaker")}
        beats.append({"from": b.f(start), "duration": b.f(end) - b.f(start), "scene": beat["scene"], "p": params,
                      "cam": beat.get("cam", "push"), "tone": beat.get("tone", "night"), "rain": bool(beat.get("rain")),
                      "fog": bool(beat.get("fog")), "flashlight": bool(beat.get("flashlight")),
                      "alarm": bool(beat.get("alarm")), "cutIn": i == 0 or scenes[i - 1] != beat["scene"],
                      "cutOut": not last and scenes[i + 1] != beat["scene"], "hits": hits})
        cur = end
    b.t = cur
    b.mutes = [(sting_at - 0.6, sting_at)]  # the score drops out just before the final hit
    ambience = spec.get("ambience", "night")
    b.music = [(0, b.t, lambda length, work: dread.score(length, work, f"score-{series['id']}-{spec['episode']}",
                                                         None if ambience == "none" else ambience, 0.5))]
    b.music_gain = 0.2
    n = spec["episode"]
    props = {"durationInFrames": b.f(b.t), "day": n, "series": series["name"], "title": spec["title"],
             "beats": beats, "chunks": chunks, "endAt": b.f(sting_at + 0.6)}
    title = f"Day {n}: {spec['title']} | {series['name']} | Zombie Survival Story #shorts"
    meta = {
        "title": title[:100],
        "description": "\n".join([
            f"{series['name']}, day {n}. {spec['summary']}",
            "",
            f"{series['about']} A new day of this story, and of the other Outbreak Diary stories, every day.",
            "Follow so you don't miss what happens next.",
            "An original animated story. All characters and events are fictional.",
            "",
            "#zombie #survival #horrorstory #shorts #animation",
        ]),
        "tags": ["zombie", "zombie apocalypse", "zombie survival", "survival story", "horror story", "animated horror",
                 "scary story", "outbreak diary"],
    }
    return b, props, meta


def write_audio(b, work, name):
    data = mix(b, work)
    folder = os.path.join(PUBLIC, "audio")
    os.makedirs(folder, exist_ok=True)
    for old in glob.glob(os.path.join(folder, "*.wav")):
        os.remove(old)  # keep the Remotion bundle small
    with wave.open(os.path.join(folder, f"{name}.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((data * 32767).astype(np.int16).tobytes())
    return f"audio/{name}.wav"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--series", required=True, choices=sorted(SERIES))
    p.add_argument("--id", required=True, help="video id, <date>-<slot>")
    p.add_argument("--file", help="build this script instead of the next one in story/new")
    p.add_argument("--keep", action="store_true", help="do not move the script to story/used (for previews)")
    a = p.parse_args()
    series = SERIES[a.series]
    path = a.file or take_episode(a.series, a.id)
    spec = json.load(open(path))
    try:
        check_episode(spec, series["cast"])
    except DiaryError as e:
        raise SystemExit(f"episode error in {path}: {e}")
    work = os.path.join(BUILD, a.id)
    os.makedirs(work, exist_ok=True)
    b, props, meta = build(spec, series)
    props["audio"] = write_audio(b, work, a.id)
    with open(os.path.join(work, "props.json"), "w") as fh:
        json.dump(props, fh)
    with open(os.path.join(work, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
    date, _, slot = a.id.rpartition("-")
    used = os.path.join(STORY, a.series, "used", date)
    if not a.keep and os.path.dirname(os.path.abspath(path)) != used:
        os.makedirs(used, exist_ok=True)
        os.rename(path, os.path.join(used, f"{slot}-{os.path.basename(path)}"))
    print(f"{series['name']} day {spec['episode']} {spec['title']!r}: {b.t:.1f}s, {len(props['beats'])} beats -> {a.id}")


if __name__ == "__main__":
    main()
