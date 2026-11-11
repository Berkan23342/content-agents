"""The full-story video of an Outbreak Diary story: once its finale is out, every day of it in one horizontal video.

Shorts views do not count towards YouTube's 4,000 watch hours, so each finished season also becomes one long video
(10-15 minutes): a short narrated opening, every day in order with chapters, and an ending that points to the story
that took over its slot. The days are rebuilt from their scripts (story/<id>/used/), with the narration cache, so
nothing new is written. The video is 16:9: the vertical part in the middle, the day and the season's days beside it
(src/Film.tsx). The opening and closing lines come from story/series.json "film" (title, intro, outro), which the
writer adds when it writes the finale.

  python3 scripts/film.py due                       stories whose film is due (finale published, no film yet)
  python3 scripts/film.py auto [--no-upload]        make and upload every film that is due
  python3 scripts/film.py harbor-view [--no-upload] [--parts 2]   one story (--parts: only the first N days, a test)
"""
import argparse
import datetime as dt
import glob
import json
import os
import shutil
import subprocess
import sys
import wave
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import ci_diary  # noqa: E402  (standard library only, so "due" runs before anything is installed)

BUILD = os.path.join(ROOT, "build")
PUBLIC = os.path.join(ROOT, "public")
STORY = os.path.join(ROOT, "story")
SERIES = {s["id"]: s for s in ci_diary.ALL}
TZ = ZoneInfo("Europe/Istanbul")
FILMS = os.path.join(ROOT, "logs", "films.txt")
FILM_AT = dt.time(21, 0)  # Istanbul; 14:00 in New York
GAP = 1.5  # the "DAY N" card before each day
TAIL = 0.9  # what is kept of a part after its final sting (the Shorts' end card is left out)
PLAYLIST = "Full Stories | Outbreak Diary"


def logged(sid):
    return os.path.exists(FILMS) and any(line.startswith(f"film-{sid}.mp4 ") for line in open(FILMS))


def parts(sid):
    """(episode, date, path) of every published part, in order."""
    out = []
    for path in glob.glob(os.path.join(STORY, sid, "used", "*", "*.json")):
        out.append((json.load(open(path))["episode"], os.path.basename(os.path.dirname(path)), path))
    return sorted(out)


def due(date):
    """Stories whose finale was made on an earlier day (so it is out by now) and that have no film yet."""
    out = []
    for s in ci_diary.ALL:
        fin = s.get("finale")
        if not fin or s.get("label") or logged(s["id"]):
            continue
        last = [d for n, d, _ in parts(s["id"]) if n == fin]
        if last and last[0] < date:
            out.append(s["id"])
    return out


def next_story(series):
    """The story that took over this one's slot."""
    later = ci_diary.ALL[[s["id"] for s in ci_diary.ALL].index(series["id"]) + 1:]
    return next((s for s in later if s["slot"] == series["slot"] and not s.get("label")), None)


def film_text(series, days):
    film = series.get("film") or {}
    return {
        "title": film.get("title") or series["tagline"][0].upper() + series["tagline"][1:],
        "intro": film.get("intro") or f"{series['about']} This is the whole story, all {days} days of it.",
        "outro": film.get("outro") or "That was my story. A new one has already begun on Outbreak Diary.",
    }


def build(sid, limit=None):
    import diary
    from diary import Builder, clip, day_one_url, dread, mix, speak_all, voice_lines
    from episode import SR, fmt

    def score(seed):
        return lambda length, work: dread.score(length, work, seed, "night", 0.5)

    series = SERIES[sid]
    found = parts(sid)
    numbers = [n for n, _, _ in found]
    if numbers != list(range(1, len(numbers) + 1)):
        raise SystemExit(f"{sid}: parts {numbers} are not 1..N")
    if not limit and series.get("finale") and numbers[-1:] != [series["finale"]]:
        raise SystemExit(f"{sid}: the finale (Day {series['finale']}) is not published yet")
    found = found[:limit] if limit else found
    specs = [json.load(open(p)) for _, _, p in found]
    days = series.get("finale") or len(specs)
    text = film_text(series, days)
    narrator = series["narrator"]

    # every line at once: Chatterbox loads its model only once (most lines are in the narration cache already)
    lines = [(narrator, text["intro"]), (narrator, text["outro"])]
    for spec in specs:
        lines += voice_lines(spec, series)[1]
    speak_all(lines)

    work = os.path.join(BUILD, f"film-{sid}")
    os.makedirs(work, exist_ok=True)
    fb = Builder()
    fb.music_gain = 0.2
    chapters = []

    # the opening: the film's title and one narrated line
    fb.sfx.append((0.1, "thud"))
    c = clip(narrator, text["intro"])
    fb.voices.append((1.0, c))
    intro_end = max(10.5, 1.0 + len(c) / SR + 1.4)
    fb.music.append((0, intro_end, score(f"film-{sid}-intro")))
    chapters.append((0, text["title"]))
    fb.t = intro_end

    film_parts = []
    for spec in specs:
        start = fb.t
        fb.sfx.append((start + 0.15, "whoosh"))
        pb, props, _ = diary.build(spec, series)
        off = start + GAP
        length = props["endAt"] / 30 + TAIL
        fb.voices += [(at + off, v) for at, v in pb.voices]
        fb.sfx += [(at + off, k) for at, k in pb.sfx if at < length]
        fb.music += [(s + off, min(e, length) + off, fn) for s, e, fn in pb.music]
        fb.mutes += [(a + off, z + off) for a, z in pb.mutes]
        chapters.append((start, f"Day {spec['episode']}: {spec['title']}"))
        props = dict(props, audio="", film=True, vote=None, voted=None)
        film_parts.append({"from": fb.f(start), "gap": fb.f(off) - fb.f(start), "duration": fb.f(off + length) - fb.f(start),
                           "day": spec["episode"], "title": spec["title"], "props": props})
        fb.t = off + length

    # the ending: THE END, the narrator's last line, and the story that runs now
    start = fb.t
    fb.sfx.append((start + 0.2, "thud"))
    c = clip(narrator, text["outro"])
    fb.voices.append((start + 1.2, c))
    end = start + max(11.0, 1.2 + len(c) / SR + 4.0)
    fb.music.append((start, end, score(f"film-{sid}-outro")))
    chapters.append((start, "The End"))
    fb.t = end
    nxt = next_story(series)

    audio = write_audio(mix(fb, work), sid, SR)
    props = {"durationInFrames": fb.f(fb.t), "audio": audio, "series": series["name"], "title": text["title"],
             "tagline": series.get("tagline"), "grade": series.get("grade"), "days": days,
             "intro": {"duration": fb.f(intro_end)}, "parts": film_parts,
             "outro": {"from": fb.f(start), "duration": fb.f(end) - fb.f(start),
                       "next": {"name": nxt["name"], "tagline": nxt.get("tagline")} if nxt else None}}
    first_of_next = day_one_url(nxt) if nxt else None
    meta = {
        "title": f"{text['title']} | The Full Zombie Story, All {days} Days"[:100],
        "description": "\n".join([
            f"{series['name']}: the whole story, all {days} days in one video. {series['about']}",
            "",
            "⏱ Chapters",
            *[f"{fmt(t)} {name}" for t, name in chapters],
            "",
            (f"A new Outbreak Diary story has begun: {nxt['name']}. Day 1: {first_of_next}" if nxt and first_of_next
             else f"A new Outbreak Diary story has begun: {nxt['name']}." if nxt else "A new Outbreak Diary story begins soon."),
            "This story was first told one day at a time in Shorts. Subscribe for the next one.",
            "An original animated story. All characters and events are fictional.",
            "",
            "#zombie #zombiestory #horrorstory #survivalstory #animation",
        ]),
        "tags": ["zombie story", "zombie apocalypse", "zombie survival", "full story", "survival story", "horror story",
                 "animated horror", "scary story", "outbreak diary", series["name"].lower()],
    }
    with open(os.path.join(work, "props.json"), "w") as fh:
        json.dump(props, fh)
    with open(os.path.join(work, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
    print(f"film {sid}: {len(specs)} days, {fb.t / 60:.1f} min")
    return work


def write_audio(data, sid, rate):
    """The film's sound as an mp3 in public/film/ (a wav of 15 minutes would make the Remotion bundle huge)."""
    import numpy as np

    folder = os.path.join(PUBLIC, "film")
    shutil.rmtree(folder, ignore_errors=True)
    os.makedirs(folder)
    wav = os.path.join(folder, f"{sid}.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes((np.clip(data, -1, 1) * 32767).astype(np.int16).tobytes())
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return f"film/{sid}.wav"
    subprocess.run([ffmpeg, "-loglevel", "error", "-y", "-i", wav, "-b:a", "192k", wav[:-4] + ".mp3"], check=True)
    os.remove(wav)
    return f"film/{sid}.mp3"


def make(sid, upload, limit=None):
    if logged(sid) and upload:
        print(f"film {sid} already uploaded")
        return
    work = build(sid, limit)
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    mp4, jpg = f"out/film-{sid}.mp4", f"out/film-{sid}.jpg"
    rel = os.path.relpath(work, ROOT)
    ci_diary.run("npx", "remotion", "render", "src/index.tsx", "Film", mp4, f"--props={rel}/props.json",
                 "--timeout=120000", "--log=error", tries=2)
    ci_diary.run("npx", "remotion", "still", "src/index.tsx", "FilmThumb", jpg, f"--props={rel}/props.json",
                 "--image-format=jpeg", "--timeout=120000", "--log=error", tries=2)
    shutil.rmtree(os.path.join(PUBLIC, "film"), ignore_errors=True)  # keep later bundles small
    if not upload:
        print(f"rendered {mp4} and {jpg} (not uploaded)")
        return
    token = ci_diary.TOKEN
    if not (os.path.exists(token) and os.path.getsize(token)):
        raise SystemExit("no channel token: add the OUTBREAK_YOUTUBE_TOKEN secret")
    today = dt.datetime.now(TZ)
    publish = dt.datetime.combine(today.date(), FILM_AT, TZ)
    args = [sys.executable, ci_diary.UPLOADER, "--video", mp4, "--meta", f"{rel}/meta.json", "--log", FILMS,
            "--general-audience", "--thumbnail", jpg, "--client", "secrets/client_secret.json", "--token", token,
            "--expect-channel", ci_diary.CHANNEL]
    if "https://www.googleapis.com/auth/youtube" in json.load(open(token)).get("scopes", []):
        args += ["--playlist", PLAYLIST, "--playlist-description",
                 "Every finished Outbreak Diary story, all its days in one video."]
    if publish - today > dt.timedelta(minutes=15):
        args += ["--publish-at", publish.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")]
    else:
        args += ["--privacy", "public"]
    ci_diary.run(*args)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("story", help="a story id, 'auto' (every film that is due) or 'due' (just list them)")
    p.add_argument("--no-upload", action="store_true")
    p.add_argument("--parts", type=int, help="only the first N days (a quick test; never uploaded)")
    p.add_argument("--date", default="")
    a = p.parse_args()
    date = a.date or dt.datetime.now(TZ).date().isoformat()
    if a.story == "due":
        print(" ".join(due(date)))
        return
    todo = due(date) if a.story == "auto" else [a.story]
    if a.story not in SERIES and a.story != "auto":
        raise SystemExit(f"unknown story {a.story!r}")
    for sid in todo:
        make(sid, not a.no_upload and not a.parts, a.parts)


if __name__ == "__main__":
    main()
