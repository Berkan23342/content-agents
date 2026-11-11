"""Makes and uploads the day's Bubbly Kids TV videos on a server (GitHub Actions).

  python3 scripts/ci_video.py story|story-short|auto [--date YYYY-MM-DD] [--no-upload]
  python3 scripts/ci_video.py due        prints the videos that are due and not uploaded yet ("story story-short", or nothing)

Since 2026-11-08 a day is one new story (scripts/fun.py --daily) and a vertical Short cut from it (--short): fewer
videos, each one different, because YouTube does not monetise template-made look-alikes. On Sundays the week's stories
also go out together in one long video at 10:00 (--weekly), for watch time. YouTube publishes them at
17:00 and 20:00 Istanbul time; if that time has already passed, the video goes out right away. The old daily formats
(learn, fun, short1, short2) can still be made by hand.
"""
import argparse
import datetime as dt
import os
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TZ = ZoneInfo("Europe/Istanbul")
PUBLISH_HOUR = {"story": 17, "story-short": 20, "weekly": 10, "learn": 10, "short1": 13, "fun": 18, "short2": 21}
DAILY = ("story", "story-short")
LOG = os.path.join(ROOT, "logs", "uploaded.txt")


def uploaded(vid):
    return os.path.exists(LOG) and any(line.startswith(f"{vid}.mp4 ") for line in open(LOG))


def video_id(kind, date):
    return date if kind == "learn" else f"{date}-{kind}"


def due(date):
    """The day's story and its Short; on Sundays also the week's stories in one video (last, so the daily ones go first)."""
    todo = [k for k in DAILY if not uploaded(video_id(k, date))]
    if dt.date.fromisoformat(date).weekday() == 6 and not uploaded(video_id("weekly", date)):
        todo.append("weekly")
    return todo


def run(*cmd, tries=1):
    for attempt in range(tries):
        if subprocess.run(cmd, cwd=ROOT).returncode == 0:
            return
        print(f"attempt {attempt + 1} failed: {' '.join(cmd[:4])}", flush=True)
    raise SystemExit(f"failed: {' '.join(cmd)}")


def make(kind, date, upload):
    vid = video_id(kind, date)
    if uploaded(vid):
        print(f"{vid} already uploaded")
        return
    py = sys.executable
    short = kind.startswith("short") or kind == "story-short"
    if kind == "story":
        run(py, "scripts/fun.py", "--date", date, "--daily")
    elif kind == "weekly":
        run(py, "scripts/fun.py", "--date", date, "--weekly")
        if not os.path.exists(os.path.join(ROOT, "build", vid, "props.json")):
            print(f"{vid}: not enough stories this week, no video")
            return
    elif kind == "story-short":
        if not os.path.exists(os.path.join(ROOT, "build", f"{date}-story", "props.json")):  # a later run: rebuild the story
            run(py, "scripts/fun.py", "--date", date, "--daily")
        run(py, "scripts/fun.py", "--date", date, "--short")
    elif short:
        run(py, "scripts/short.py", "--date", date, "--slot", kind[-1])
    else:
        run(py, "scripts/episode.py" if kind == "learn" else "scripts/fun.py", "--date", date)
    os.makedirs(os.path.join(ROOT, "out", "episodes"), exist_ok=True)
    mp4, jpg, props = f"out/episodes/{vid}.mp4", f"out/episodes/{vid}.jpg", f"--props=build/{vid}/props.json"
    composition = "StoryShort" if kind == "story-short" else "Short" if short else "Episode"
    run("npx", "remotion", "render", "src/index.tsx", composition, mp4, props, "--timeout=120000", "--log=error", tries=3)
    if not short:  # YouTube shows no custom thumbnails in the Shorts feed
        run("npx", "remotion", "still", "src/index.tsx", "Thumbnail", jpg, props, "--image-format=jpeg", "--scale=0.6667",
            "--timeout=120000", "--log=error", tries=3)
    if not upload:
        print(f"rendered {mp4} (not uploaded)")
        return

    publish = dt.datetime.combine(dt.date.fromisoformat(date), dt.time(PUBLISH_HOUR[kind]), TZ)
    args = [py, "scripts/upload_youtube.py", "--video", mp4, "--meta", f"build/{vid}/meta.json", "--log", LOG]
    if not short:
        args += ["--thumbnail", jpg]
    if publish - dt.datetime.now(TZ) > dt.timedelta(minutes=15):
        args += ["--publish-at", publish.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")]
    else:
        args += ["--privacy", "public"]
    run(*args)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kind", choices=["story", "story-short", "weekly", "learn", "fun", "short1", "short2", "auto", "due"])
    p.add_argument("--date", default="")
    p.add_argument("--no-upload", action="store_true")
    a = p.parse_args()
    date = a.date or dt.datetime.now(TZ).date().isoformat()
    if a.kind == "due":
        print(" ".join(due(date)))
        return
    for kind in due(date) if a.kind == "auto" else [a.kind]:
        make(kind, date, not a.no_upload)


if __name__ == "__main__":
    main()
