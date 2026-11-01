"""Plans and voices one Outbreak Diary episode: a vertical 45-60 second part of a serialized zombie survival story.

The episode script comes from story/new/ (the lowest episode number first), written by the story writer routine
(see AGENT.md and story/bible.md). After building, the script moves to story/used/<date>/.
Voice, mixing and the master come from the kids channel's scripts (kids-channel/scripts/episode.py and audio.py);
the horror sounds and the score are in scripts/dread.py.

Writes build/<id>/{props,meta}.json and public/audio/<id>.wav.
Run with ../kids-channel/.venv/bin/python scripts/diary.py --id 2026-11-02-e1 [--file story/new/ep-0001.json] [--keep]
"""
import argparse
import glob
import json
import os
import re
import sys
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "kids-channel", "scripts"))

from episode import SR, Builder, mix  # noqa: E402
import dread  # noqa: E402,F401  (registers the horror sounds)
from diarycheck import DiaryError, check_episode, sfx_name  # noqa: E402

BUILD = os.path.join(ROOT, "build")
PUBLIC = os.path.join(ROOT, "public")
STORY = os.path.join(ROOT, "story")

NARRATOR = "af_nicole"  # the user picked this whispery voice
SPEED = 1.1
GAP = 0.35  # silence after each beat
END_CARD = 2.8
SHAKES = {"bang", "thud", "glass", "sting"}


def take_episode(vid):
    """The script this video already used (on a re-run), else the lowest episode waiting in story/new."""
    date, _, slot = vid.rpartition("-")
    used = sorted(glob.glob(os.path.join(STORY, "used", date, f"{slot}-*.json")))
    if used:
        return used[0]
    waiting = []
    for path in glob.glob(os.path.join(STORY, "new", "*.json")):
        try:
            spec = json.load(open(path))
            check_episode(spec)
        except (DiaryError, json.JSONDecodeError) as e:
            print(f"skipping {os.path.basename(path)}: {e}")
            continue
        waiting.append((spec["episode"], path))
    if not waiting:
        raise SystemExit("no episode script in story/new")
    return min(waiting)[1]


def chunks_for(text, hl, t0, t1, f):
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
                       "at": f(at), "until": f(until)})
    return chunks


def build(spec):
    b = Builder()
    say = lambda at, text: b.say(at, text, voice=NARRATOR, speed=SPEED)  # noqa: E731
    beats, chunks = [], []
    b.sfx.append((0.05, "thud"))
    cur = 0.3
    scenes = [x["scene"] for x in spec["beats"]]
    sting_at = None
    for i, beat in enumerate(spec["beats"]):
        start = cur
        d = say(start + 0.1, beat["text"])
        chunks += chunks_for(beat["text"], beat.get("hl", []), start + 0.12, start + 0.1 + d, b.f)
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
                                                              "flashlight", "alarm", "hold")}
        beats.append({"from": b.f(start), "duration": b.f(end) - b.f(start), "scene": beat["scene"], "p": params,
                      "cam": beat.get("cam", "push"), "tone": beat.get("tone", "night"), "rain": bool(beat.get("rain")),
                      "fog": bool(beat.get("fog")), "flashlight": bool(beat.get("flashlight")),
                      "alarm": bool(beat.get("alarm")), "cutIn": i == 0 or scenes[i - 1] != beat["scene"],
                      "cutOut": not last and scenes[i + 1] != beat["scene"], "hits": hits})
        cur = end
    b.t = cur
    b.mutes = [(sting_at - 0.6, sting_at)]  # the score drops out just before the final hit
    ambience = spec.get("ambience", "night")
    b.music = [(0, b.t, lambda length, work: dread.score(length, work, f"score-{spec['episode']}",
                                                         None if ambience == "none" else ambience, 0.5))]
    b.music_gain = 0.2
    props = {"durationInFrames": b.f(b.t), "day": spec["day"], "episode": spec["episode"], "title": spec["title"],
             "beats": beats, "chunks": chunks, "endAt": b.f(sting_at + 0.6)}
    title = f"Day {spec['day']}: {spec['title']} | Zombie Survival Story Part {spec['episode']} #shorts"
    meta = {
        "title": title[:100],
        "description": "\n".join([
            f"Part {spec['episode']} of Outbreak Diary. {spec['summary']}",
            "",
            "A new part every day. Follow so you don't miss what happens next.",
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
    p.add_argument("--id", required=True, help="video id, <date>-e1 or <date>-e2")
    p.add_argument("--file", help="build this script instead of the next one in story/new")
    p.add_argument("--keep", action="store_true", help="do not move the script to story/used (for previews)")
    a = p.parse_args()
    path = a.file or take_episode(a.id)
    spec = json.load(open(path))
    try:
        check_episode(spec)
    except DiaryError as e:
        raise SystemExit(f"episode error in {path}: {e}")
    work = os.path.join(BUILD, a.id)
    os.makedirs(work, exist_ok=True)
    b, props, meta = build(spec)
    props["audio"] = write_audio(b, work, a.id)
    with open(os.path.join(work, "props.json"), "w") as fh:
        json.dump(props, fh)
    with open(os.path.join(work, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
    date, _, slot = a.id.rpartition("-")
    used = os.path.join(STORY, "used", date)
    if not a.keep and os.path.dirname(os.path.abspath(path)) != used:
        os.makedirs(used, exist_ok=True)
        os.rename(path, os.path.join(used, f"{slot}-{os.path.basename(path)}"))
    print(f"episode {spec['episode']} (day {spec['day']}) {spec['title']!r}: {b.t:.1f}s, {len(props['beats'])} beats -> {a.id}")


if __name__ == "__main__":
    main()
