"""Makes and uploads one Bubbly Kids TV video on a server (GitHub Actions); the Mac version is scripts/daily.sh.

  python3 scripts/ci_video.py learn|fun [--date YYYY-MM-DD] [--no-upload]

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


def run(*cmd, tries=1):
    for attempt in range(tries):
        if subprocess.run(cmd, cwd=ROOT).returncode == 0:
            return
        print(f"attempt {attempt + 1} failed: {' '.join(cmd[:4])}", flush=True)
    raise SystemExit(f"failed: {' '.join(cmd)}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kind", choices=["learn", "fun"])
    p.add_argument("--date", default="")
    p.add_argument("--no-upload", action="store_true")
    a = p.parse_args()
    date = a.date or dt.datetime.now(TZ).date().isoformat()
    vid = date if a.kind == "learn" else f"{date}-fun"
    log = os.path.join(ROOT, "logs", "uploaded.txt")
    if os.path.exists(log) and any(line.startswith(f"{vid}.mp4 ") for line in open(log)):
        print(f"{vid} already uploaded")
        return

    py = sys.executable
    run(py, "scripts/episode.py" if a.kind == "learn" else "scripts/fun.py", "--date", date)
    os.makedirs(os.path.join(ROOT, "out", "episodes"), exist_ok=True)
    mp4, jpg, props = f"out/episodes/{vid}.mp4", f"out/episodes/{vid}.jpg", f"--props=build/{vid}/props.json"
    run("npx", "remotion", "render", "src/index.tsx", "Episode", mp4, props, "--timeout=120000", "--log=error", tries=3)
    run("npx", "remotion", "still", "src/index.tsx", "Thumbnail", jpg, props, "--image-format=jpeg", "--scale=0.6667",
        "--timeout=120000", "--log=error", tries=3)
    if a.no_upload:
        print(f"rendered {mp4} (not uploaded)")
        return

    publish = dt.datetime.combine(dt.date.fromisoformat(date), dt.time(PUBLISH_HOUR[a.kind]), TZ)
    args = [py, "scripts/upload_youtube.py", "--video", mp4, "--meta", f"build/{vid}/meta.json", "--thumbnail", jpg, "--log", log]
    if publish - dt.datetime.now(TZ) > dt.timedelta(minutes=15):
        args += ["--publish-at", publish.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")]
    else:
        args += ["--privacy", "public"]
    run(*args)


if __name__ == "__main__":
    main()
