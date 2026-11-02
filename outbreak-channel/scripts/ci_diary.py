"""Makes and uploads the day's Outbreak Diary parts on a server (GitHub Actions): one new day of every story.

  python3 scripts/ci_diary.py e1|e2|e3|auto [--date YYYY-MM-DD] [--no-upload]
  python3 scripts/ci_diary.py due        prints the parts that are not uploaded yet ("e1 e2 e3", or nothing)

story/series.json gives each story a slot and a publishing time (Istanbul time, possibly the next night). All parts are
made in one morning run and YouTube publishes them at those times; if a time has already passed, the part goes out
right away.
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADER = os.path.join(os.path.dirname(ROOT), "kids-channel", "scripts", "upload_youtube.py")
TZ = ZoneInfo("Europe/Istanbul")
SERIES = {s["slot"]: s for s in json.load(open(os.path.join(ROOT, "story", "series.json")))}
LOG = os.path.join(ROOT, "logs", "uploaded.txt")
TOKEN = os.path.join(ROOT, "secrets", "token.json")
CHANNEL = "UCtjcmQc9DV_sKh4_3UrToIQ"  # Outbreak Diary; the uploader refuses a token for any other channel


def uploaded(vid):
    return os.path.exists(LOG) and any(line.startswith(f"{vid}.mp4 ") for line in open(LOG))


def due(date):
    return [e for e in sorted(SERIES) if not uploaded(f"{date}-{e}")]


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
    run(py, "scripts/diary.py", "--series", SERIES[e]["id"], "--id", vid,
        *([] if upload else ["--keep"]))  # a test render leaves the story where it is
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    mp4 = f"out/{vid}.mp4"
    run("npx", "remotion", "render", "src/index.tsx", "Diary", mp4, f"--props=build/{vid}/props.json", "--timeout=120000",
        "--log=error", tries=3)
    if not upload:
        print(f"rendered {mp4} (not uploaded)")
        return
    days, at = SERIES[e]["publish"]
    publish = dt.datetime.combine(dt.date.fromisoformat(date) + dt.timedelta(days=days), dt.time.fromisoformat(at), TZ)
    args = [py, UPLOADER, "--video", mp4, "--meta", f"build/{vid}/meta.json", "--log", LOG, "--general-audience",
            "--client", "secrets/client_secret.json", "--token", TOKEN, "--expect-channel", CHANNEL]
    if publish - dt.datetime.now(TZ) > dt.timedelta(minutes=15):
        args += ["--publish-at", publish.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")]
    else:
        args += ["--privacy", "public"]
    run(*args)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kind", choices=sorted(SERIES) + ["auto", "due"])
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
