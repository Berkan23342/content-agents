"""Makes and uploads the day's Brain Snack on a server (GitHub Actions).

  python3 scripts/ci_quiz.py snack|auto [--date YYYY-MM-DD] [--no-upload]
  python3 scripts/ci_quiz.py due        prints "snack" when today's Brain Snack is not uploaded yet, else nothing

Since 2026-11-08 the channel posts one video a day. Since 2026-11-20 the days take turns between a five-question
quiz (scripts/quiz.py: a trivia pack or a flags quiz) and a Brain Snack (scripts/snack.py, its own turn of formats):
scripts/snackcheck.py DAY_PLAN. The video is made in the morning and YouTube publishes it at 19:00
Istanbul time (lunch in the US); if that time has passed, right away.
A test render (--no-upload) leaves the script waiting in snacks/new.
"""
import argparse
import datetime as dt
import os
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADER = os.path.join(os.path.dirname(ROOT), "kids-channel", "scripts", "upload_youtube.py")
TZ = ZoneInfo("Europe/Istanbul")
PUBLISH_AT = dt.time(19, 0)
LOG = os.path.join(ROOT, "logs", "uploaded.txt")
TOKEN = os.path.join(ROOT, "secrets", "token.json")
START = "2026-11-09"  # the first Brain Snack day (the rotation in scripts/snackcheck.py starts here)
CHANNEL = "UCyuNuzwYO9UgNt5GP0UqePg"  # Brain Snack Quiz; the uploader refuses a token for any other channel


def uploaded(vid):
    return os.path.exists(LOG) and any(line.startswith(f"{vid}.mp4 ") for line in open(LOG))


sys.path.insert(0, os.path.join(ROOT, "scripts"))
from snackcheck import kind_of_day  # noqa: E402  (standard library only)


def video_id(date):
    return f"{date}-snack" if kind_of_day(date) == "snack" else f"{date}-q1"


def due(date):
    if date < START:
        return []
    return [] if uploaded(video_id(date)) else [kind_of_day(date)]


def run(*cmd, tries=1):
    for attempt in range(tries):
        if subprocess.run(cmd, cwd=ROOT).returncode == 0:
            return
        print(f"attempt {attempt + 1} failed: {' '.join(cmd[:4])}", flush=True)
    raise SystemExit(f"failed: {' '.join(cmd)}")


def make(date, upload):
    vid = video_id(date)
    kind = kind_of_day(date)
    if uploaded(vid):
        print(f"{vid} already uploaded")
        return
    if upload and not (os.path.exists(TOKEN) and os.path.getsize(TOKEN)):
        raise SystemExit("no channel token: add the QUIZ_YOUTUBE_TOKEN secret (see README)")
    py = sys.executable
    if kind == "snack":
        run(py, "scripts/snack.py", "--date", date, *([] if upload else ["--keep"]))
        composition = "Snack"
    else:  # a five-question quiz: a trivia pack (falls back to flags when none is waiting) or a flags quiz
        run(py, "scripts/quiz.py", "--date", date, "--slot", "1", "--format", kind, *([] if upload else ["--keep"]))
        composition = "Quiz"
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    mp4 = f"out/{vid}.mp4"
    run("npx", "remotion", "render", "src/index.tsx", composition, mp4, f"--props=build/{vid}/props.json",
        "--timeout=120000", "--log=error", tries=3)
    if not upload:
        print(f"rendered {mp4} (not uploaded)")
        return
    publish = dt.datetime.combine(dt.date.fromisoformat(date), PUBLISH_AT, TZ)
    args = [py, UPLOADER, "--video", mp4, "--meta", f"build/{vid}/meta.json", "--log", LOG, "--general-audience",
            "--client", "secrets/client_secret.json", "--token", TOKEN, "--expect-channel", CHANNEL]
    if publish - dt.datetime.now(TZ) > dt.timedelta(minutes=15):
        args += ["--publish-at", publish.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")]
    else:
        args += ["--privacy", "public"]
    run(*args)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kind", choices=["snack", "auto", "due"], help="auto/snack: make the day's video, whatever its kind")
    p.add_argument("--date", default="")
    p.add_argument("--no-upload", action="store_true")
    a = p.parse_args()
    date = a.date or dt.datetime.now(TZ).date().isoformat()
    if a.kind == "due":
        print(" ".join(due(date)))
        return
    for _ in due(date) if a.kind == "auto" else [kind_of_day(date)]:
        make(date, not a.no_upload)


if __name__ == "__main__":
    main()
