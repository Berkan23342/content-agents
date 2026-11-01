"""Makes and uploads the day's two Outbreak Diary parts on a server (GitHub Actions).

  python3 scripts/ci_diary.py e1|e2|auto [--date YYYY-MM-DD] [--no-upload]
  python3 scripts/ci_diary.py due        prints the parts that are not uploaded yet ("e1 e2", or nothing)

Both parts are made in one morning run. YouTube publishes them at 20:00 Istanbul time and at 03:00 the next night
(lunch and evening in the US); if that time has already passed, the part is published right away.
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
PUBLISH_AT = {"e1": (0, dt.time(20, 0)), "e2": (1, dt.time(3, 0))}  # (days after the date, time)
LOG = os.path.join(ROOT, "logs", "uploaded.txt")
TOKEN = os.path.join(ROOT, "secrets", "token.json")
CHANNEL = "UCtjcmQc9DV_sKh4_3UrToIQ"  # Outbreak Diary; the uploader refuses a token for any other channel


def uploaded(vid):
    return os.path.exists(LOG) and any(line.startswith(f"{vid}.mp4 ") for line in open(LOG))


def due(date):
    return [e for e in PUBLISH_AT if not uploaded(f"{date}-{e}")]


def run(*cmd, tries=1):
    for attempt in range(tries):
        if subprocess.run(cmd, cwd=ROOT).returncode == 0:
            return
        print(f"attempt {attempt + 1} failed: {' '.join(cmd[:4])}", flush=True)
    raise SystemExit(f"failed: {' '.join(cmd)}")


def make(e, date, upload):
    vid = f"{date}-{e}"
    if uploaded(vid):
        print(f"{vid} already uploaded")
        return
    if upload and not CHANNEL:
        raise SystemExit("set CHANNEL in scripts/ci_diary.py to the Outbreak Diary channel id first")
    if upload and not (os.path.exists(TOKEN) and os.path.getsize(TOKEN)):
        raise SystemExit("no channel token: add the OUTBREAK_YOUTUBE_TOKEN secret (see README)")
    py = sys.executable
    run(py, "scripts/diary.py", "--id", vid, *([] if upload else ["--keep"]))  # a test render leaves the story where it is
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    mp4 = f"out/{vid}.mp4"
    run("npx", "remotion", "render", "src/index.tsx", "Diary", mp4, f"--props=build/{vid}/props.json", "--timeout=120000",
        "--log=error", tries=3)
    if not upload:
        print(f"rendered {mp4} (not uploaded)")
        return
    days, at = PUBLISH_AT[e]
    publish = dt.datetime.combine(dt.date.fromisoformat(date) + dt.timedelta(days=days), at, TZ)
    args = [py, UPLOADER, "--video", mp4, "--meta", f"build/{vid}/meta.json", "--log", LOG, "--general-audience",
            "--client", "secrets/client_secret.json", "--token", TOKEN, "--expect-channel", CHANNEL]
    if publish - dt.datetime.now(TZ) > dt.timedelta(minutes=15):
        args += ["--publish-at", publish.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")]
    else:
        args += ["--privacy", "public"]
    run(*args)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kind", choices=["e1", "e2", "auto", "due"])
    p.add_argument("--date", default="")
    p.add_argument("--no-upload", action="store_true")
    a = p.parse_args()
    date = a.date or dt.datetime.now(TZ).date().isoformat()
    if a.kind == "due":
        print(" ".join(due(date)))
        return
    for e in due(date) if a.kind == "auto" else [a.kind]:
        make(e, date, not a.no_upload)


if __name__ == "__main__":
    main()
