"""Makes and uploads one Bubbly Kids TV video on a server (GitHub Actions); the Mac version is scripts/daily.sh.

  python3 scripts/ci_video.py learn|fun|auto [--date YYYY-MM-DD] [--no-upload]
  python3 scripts/ci_video.py due        prints the videos that are due and not uploaded yet ("learn fun", or nothing)

`auto` makes whatever is due: the learning video any time of day, the fun video from 16:00 Istanbul time.
The video is uploaded as soon as it is ready and YouTube publishes it at 10:00 (learn) or 18:00 (fun)
Istanbul time. If that time has already passed, it is published right away.
"""
import argparse
import datetime as dt
import os
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TZ = ZoneInfo("Europe/Istanbul")
PUBLISH_HOUR = {"learn": 10, "fun": 18}
FUN_FROM_HOUR = 16  # the fun video is made in the 2 hours before it is published
LOG = os.path.join(ROOT, "logs", "uploaded.txt")


def uploaded(vid):
    return os.path.exists(LOG) and any(line.startswith(f"{vid}.mp4 ") for line in open(LOG))


def due(date):
    now = dt.datetime.now(TZ)
    out = []
    if not uploaded(date):
        out.append("learn")
    if not uploaded(f"{date}-fun") and (date < now.date().isoformat() or now.hour >= FUN_FROM_HOUR):
        out.append("fun")
    return out


def run(*cmd, tries=1):
    for attempt in range(tries):
        if subprocess.run(cmd, cwd=ROOT).returncode == 0:
            return
        print(f"attempt {attempt + 1} failed: {' '.join(cmd[:4])}", flush=True)
    raise SystemExit(f"failed: {' '.join(cmd)}")


def make(kind, date, upload):
    vid = date if kind == "learn" else f"{date}-fun"
    if uploaded(vid):
        print(f"{vid} already uploaded")
        return
    py = sys.executable
    run(py, "scripts/episode.py" if kind == "learn" else "scripts/fun.py", "--date", date)
    os.makedirs(os.path.join(ROOT, "out", "episodes"), exist_ok=True)
    mp4, jpg, props = f"out/episodes/{vid}.mp4", f"out/episodes/{vid}.jpg", f"--props=build/{vid}/props.json"
    run("npx", "remotion", "render", "src/index.tsx", "Episode", mp4, props, "--timeout=120000", "--log=error", tries=3)
    run("npx", "remotion", "still", "src/index.tsx", "Thumbnail", jpg, props, "--image-format=jpeg", "--scale=0.6667",
        "--timeout=120000", "--log=error", tries=3)
    if not upload:
        print(f"rendered {mp4} (not uploaded)")
        return

    publish = dt.datetime.combine(dt.date.fromisoformat(date), dt.time(PUBLISH_HOUR[kind]), TZ)
    args = [py, "scripts/upload_youtube.py", "--video", mp4, "--meta", f"build/{vid}/meta.json", "--thumbnail", jpg, "--log", LOG]
    if publish - dt.datetime.now(TZ) > dt.timedelta(minutes=15):
        args += ["--publish-at", publish.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")]
    else:
        args += ["--privacy", "public"]
    run(*args)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kind", choices=["learn", "fun", "auto", "due"])
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
