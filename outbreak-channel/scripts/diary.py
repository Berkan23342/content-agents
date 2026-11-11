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
import zlib

import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "kids-channel", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "shared"))

import audio  # noqa: E402
from episode import SR, Builder, mix  # noqa: E402
import dread  # noqa: E402,F401  (registers the horror sounds)
from diarycheck import DiaryError, check_against, check_episode, sfx_name  # noqa: E402
from captions import chunks_for  # noqa: E402

BUILD = os.path.join(ROOT, "build")
PUBLIC = os.path.join(ROOT, "public")
STORY = os.path.join(ROOT, "story")
SERIES = {s["id"]: s for s in json.load(open(os.path.join(STORY, "series.json")))}
VOICES = os.path.join(ROOT, "voices")
CB_PYTHON = os.environ.get("CB_PYTHON", os.path.join(ROOT, ".venv-cb", "bin", "python"))
EXAGGERATION = 0.55  # Chatterbox: how dramatic the delivery is
FLIPPABLE = {"building", "window", "street", "rooftop", "forest", "tower", "hallway", "lake", "gas_station", "supermarket",
             "skybridge"}  # keep in step with FLIPPABLE in src/scenes.tsx
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
    episode, path = min(waiting)
    published = [json.load(open(p))["episode"] for p in glob.glob(os.path.join(STORY, series, "used", "*", "*.json"))]
    if episode != max(published, default=0) + 1:  # never skip or repeat a day
        raise SystemExit(f"{series}: the next part should be {max(published, default=0) + 1}, the first waiting is {episode}")
    try:
        check_against(path, json.load(open(path)))
    except DiaryError as e:  # better no video today than a repeat
        raise SystemExit(f"{series}: {os.path.basename(path)} not published: {e}")
    return path


# Each story has its own look (story/series.json "frame"); a special takes the look of its kind.
SPECIAL_FRAME = {"story": "diary", "broadcast": "broadcast", "found": "camcorder", "journal": "journal"}


def radio(c):
    """A voice heard through a radio or a TV speaker: narrow band, a little crunch."""
    from scipy.signal import butter, sosfilt

    sos = butter(4, [320, 3300], btype="bandpass", fs=SR, output="sos")
    y = sosfilt(sos, c, axis=0)
    y = np.tanh(y * 2.2) / np.tanh(2.2)
    peak = np.max(np.abs(y)) or 1.0
    return (y / peak * np.max(np.abs(c))).astype(np.float32)


def frame_for(spec, series):
    if series.get("label"):
        return SPECIAL_FRAME.get(spec.get("kind", "story"), "diary")
    return series.get("frame", "diary")


LOG = os.path.join(ROOT, "logs", "uploaded.txt")
DAY_OPENING = re.compile(r"^\s*Day\s+[\w-]+[.,:!]\s+(?=\S)", re.I)


def opening(text):
    """The first line starts on the moment itself: "Day twelve. Marek opened the cupboard." loses "Day twelve." because the
    day is already on screen, and the first second decides whether a viewer stays."""
    rest = DAY_OPENING.sub("", text, count=1)
    return rest[0].upper() + rest[1:] if rest else text


def day_one_url(series):
    """The YouTube link of the story's Day 1, from the uploaded list (None before it is out)."""
    for path in glob.glob(os.path.join(STORY, series["id"], "used", "*", "*.json")):
        try:
            if json.load(open(path))["episode"] != 1:
                continue
        except (json.JSONDecodeError, KeyError):
            continue
        vid = f"{os.path.basename(os.path.dirname(path))}-{os.path.basename(path).split('-')[0]}.mp4 "
        for line in open(LOG) if os.path.exists(LOG) else []:
            if line.startswith(vid) and "https://" in line:
                return line.split()[1]
    return None


FILMS = os.path.join(ROOT, "logs", "films.txt")


def latest_film():
    """(story id, link) of the newest full-story video (scripts/film.py), or None."""
    lines = [l.split() for l in open(FILMS)] if os.path.exists(FILMS) else []  # "film-<story>.mp4 <link>"
    return next(((l[0][len("film-"):-len(".mp4")], l[1]) for l in reversed(lines) if len(l) >= 2), None)


def voice_lines(spec, series):
    """(voice, text) of every beat: the narrator, or a speaking character in its own voice."""
    narrator = spec.get("narrator", series["narrator"])  # a special may pick its own narrator
    cast_voice = series.get("voices", {})  # a character may borrow a voice file under another name
    texts = [beat["text"] for beat in spec["beats"]]
    texts[0] = opening(texts[0])
    return narrator, [(cast_voice.get(beat["speaker"], beat["speaker"]) if "speaker" in beat else narrator, texts[i])
                      for i, beat in enumerate(spec["beats"])]


def build(spec, series):
    b = Builder()
    narrator, lines = voice_lines(spec, series)
    speak_all(lines)
    frame = frame_for(spec, series)

    def say(at, voice, text):
        c = clip(voice, text)
        if frame == "broadcast" and voice == narrator:
            c = radio(c)
        b.voices.append((at, c))
        return len(c) / SR

    beats, chunks = [], []
    # Variety: details change per part (seed); a story keeps its own doors, lift and radio (place), while every special
    # is a new place; repeated scenes cut between wide and close shots; some outdoor scenes are mirrored per part.
    crc = lambda text: zlib.crc32(text.encode()) % 997  # noqa: E731
    place = crc(f"{series['id']}-{spec['episode']}" if series.get("label") else series["id"])
    runs, shot, prev = {}, 0, None
    b.sfx.append((0.0, "thud"))
    cur = 0.05  # no title card: the first line starts at once
    scenes = [x["scene"] for x in spec["beats"]]
    sting_at = None
    for i, beat in enumerate(spec["beats"]):
        start = cur
        voice, text = lines[i]
        scene = beat["scene"]
        if scene != prev:
            runs[scene] = runs.get(scene, 0) + 1
            shot = runs[scene] - 1  # the first visit opens wide, a return opens on a close-up
        else:
            shot += 1
        prev = scene
        d = say(start + 0.1, voice, text)
        hl = [h for h in beat.get("hl", []) if h.lower() in text.lower()]
        chunks += chunks_for(text, hl, start + 0.02, start + 0.1 + d, b.f, "speaker" in beat)
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
            end = sting_at + 0.6 + END_CARD + (1.2 if spec.get("vote") else 0)  # time to read the two options
        params = {k: v for k, v in beat.items() if k not in ("scene", "text", "hl", "sfx", "cam", "tone", "rain", "fog",
                                                              "flashlight", "alarm", "hold", "speaker")}
        beats.append({"from": b.f(start), "duration": b.f(end) - b.f(start), "scene": beat["scene"], "p": params,
                      "cam": beat.get("cam", "push"), "tone": beat.get("tone", "night"), "rain": bool(beat.get("rain")),
                      "fog": bool(beat.get("fog")), "flashlight": bool(beat.get("flashlight")),
                      "alarm": bool(beat.get("alarm")), "cutIn": i > 0 and scenes[i - 1] != beat["scene"],  # the first frame is already the scene
                      "cutOut": not last and scenes[i + 1] != beat["scene"], "hits": hits,
                      "seed": crc(f"{series['id']}-{spec['episode']}-{scene}"), "place": place, "shot": shot,
                      "flip": scene in FLIPPABLE and crc(f"{series['id']}-{spec['episode']}-{scene}-flip") % 2 == 1})
        cur = end
    b.t = cur
    b.mutes = [(sting_at - 0.6, sting_at)]  # the score drops out just before the final hit
    ambience = spec.get("ambience", "night")
    b.music = [(0, b.t, lambda length, work: dread.score(length, work, f"score-{series['id']}-{spec['episode']}",
                                                         None if ambience == "none" else ambience, 0.5))]
    b.music_gain = 0.2
    n = spec["episode"]
    finale = bool(series.get("finale")) and n == series["finale"]
    props = {"durationInFrames": b.f(b.t), "day": n, "series": series["name"], "label": series.get("label"),
             "grade": series.get("grade"), "title": spec["title"], "frame": frame, "tagline": series.get("tagline"),
             "finale": finale, "beats": beats, "chunks": chunks, "endAt": b.f(sting_at + 0.6),
             "vote": spec.get("vote"), "voted": voted_badge(spec)}
    title = video_title(series, n, spec["title"])
    first = day_one_url(series) if n > 1 and not series.get("label") else None
    if series.get("label"):
        where = []
    elif n == 1:
        where = [f"Day 1 of a brand-new story. {series['about']}"]
    elif finale:
        where = [f"The final day of {series['name']}." + (f" Watch it from the start: {first}" if first else "")]
    else:
        where = [f"New here? Start from Day 1: {first}"] if first else []
    vote, badge = spec.get("vote"), voted_badge(spec)
    if vote:
        a, z = vote["options"]
        where.append(f"🗳 YOU DECIDE: {vote['question']} Comment {a} or {z}. The most votes decide Day {vote['decides']}.")
    if badge:
        counts = " to ".join(str(badge["votes"].get(o, 0)) for o in sorted(badge["votes"], key=lambda o: -badge["votes"][o]))
        where.append(f"You voted {badge['pick']} ({counts}), and this is what happened.")
    film = latest_film()
    if film and film[0] != series["id"]:
        where.append(f"▶ A whole finished story in one video: {film[1]}")
    meta = {
        "title": title[:100],
        "description": "\n".join([
            f"{series['name']}, day {n}. {spec['summary']}" if not series.get("label") else spec["summary"],
            *where,
            "",
            f"{series['about']} A new day of this story, and of the other Outbreak Diary stories, every day."
            if not finale else "A new Outbreak Diary story starts in its place soon, and the other stories go on every day.",
            "Follow so you don't miss what happens next.",
            "An original animated story. All characters and events are fictional.",
            "",
            "#zombie #survival #horrorstory #shorts #animation",
        ]),
        "tags": ["zombie", "zombie apocalypse", "zombie survival", "survival story", "horror story", "animated horror",
                 "scary story", "outbreak diary"],
    }
    return b, props, meta


def voted_badge(spec):
    """What the viewers chose, for the top of the part their vote decided (None when nobody voted)."""
    voted = spec.get("voted")
    if not voted or not sum(voted.get("votes", {}).values()):
        return None
    return {"pick": voted["pick"], "votes": voted["votes"]}


def video_title(series, day, title):
    """The story's name first, so viewers can tell the stories apart: "Harbor View · Day 3: Pier Four | ...".
    A one-part special has no days: "They Never Look Up | Outbreak Specials · Zombie Story"."""
    if series.get("label"):
        return f"{title} | {series['name']} · Zombie Survival Story #shorts"
    return f"{series['name']} · Day {day}: {title} | Zombie Survival Story #shorts"


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
