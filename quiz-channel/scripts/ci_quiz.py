"""Makes and uploads the day's two Brain Snack Quiz Shorts on a server (GitHub Actions).

  python3 scripts/ci_quiz.py q1|q2|auto [--date YYYY-MM-DD] [--no-upload]
  python3 scripts/ci_quiz.py due        prints the Shorts that are not uploaded yet ("q1 q2", or nothing)

Both Shorts are made in one morning run. YouTube publishes them at 19:00 and 23:30 Istanbul time (lunch and
afternoon in the US); if that time has already passed, the Short is published right away.
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
PUBLISH_AT = {"q1": dt.time(19, 0), "q2": dt.time(23, 30)}
LOG = os.path.join(ROOT, "logs", "uploaded.txt")
TOKEN = os.path.join(ROOT, "secrets", "token.json")


def uploaded(vid):
    return os.path.exists(LOG) and any(line.startswith(f"{vid}.mp4 ") for line in open(LOG))


def due(date):
    return [q for q in PUBLISH_AT if not uploaded(f"{date}-{q}")]


def run(*cmd, tries=1):
    for attempt in range(tries):
        if subprocess.run(cmd, cwd=ROOT).returncode == 0:
            return
        print(f"attempt {attempt + 1} failed: {' '.join(cmd[:4])}", flush=True)
    raise SystemExit(f"failed: {' '.join(cmd)}")


def make(q, date, upload):
    vid = f"{date}-{q}"
    if uploaded(vid):
        print(f"{vid} already uploaded")
        return
    if upload and not (os.path.exists(TOKEN) and os.path.getsize(TOKEN)):
        raise SystemExit("no channel token: add the QUIZ_YOUTUBE_TOKEN secret (see README)")
    py = sys.executable
    run(py, "scripts/quiz.py", "--date", date, "--slot", q[-1])
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    mp4 = f"out/{vid}.mp4"
    run("npx", "remotion", "render", "src/index.tsx", "Quiz", mp4, f"--props=build/{vid}/props.json", "--timeout=120000",
        "--log=error", tries=3)
    if not upload:
        print(f"rendered {mp4} (not uploaded)")
        return
    publish = dt.datetime.combine(dt.date.fromisoformat(date), PUBLISH_AT[q], TZ)
    args = [py, UPLOADER, "--video", mp4, "--meta", f"build/{vid}/meta.json", "--log", LOG, "--general-audience",
            "--client", "secrets/client_secret.json", "--token", TOKEN]
    if publish - dt.datetime.now(TZ) > dt.timedelta(minutes=15):
        args += ["--publish-at", publish.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")]
    else:
        args += ["--privacy", "public"]
    run(*args)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kind", choices=["q1", "q2", "auto", "due"])
    p.add_argument("--date", default="")
    p.add_argument("--no-upload", action="store_true")
    a = p.parse_args()
    date = a.date or dt.datetime.now(TZ).date().isoformat()
    if a.kind == "due":
        print(" ".join(due(date)))
        return
    for q in due(date) if a.kind == "auto" else [a.kind]:
        make(q, date, not a.no_upload)


if __name__ == "__main__":
    main()
