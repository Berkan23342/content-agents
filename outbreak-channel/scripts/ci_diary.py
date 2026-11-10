"""Makes and uploads the day's Outbreak Diary parts on a server (GitHub Actions): one new day of every story.

  python3 scripts/ci_diary.py e1|e2|e3|auto [--date YYYY-MM-DD] [--no-upload]
  python3 scripts/ci_diary.py due        prints the parts that are not uploaded yet ("e1 e2 e3", or nothing)

story/series.json gives each story a slot and a publishing time (Istanbul time, possibly the next night). All parts are
made in one morning run and YouTube publishes them at those times; if a time has already passed, the part goes out
right away. A story with a "finale" hands its slot to the next story with the same slot (later in series.json) once
its last day has been published, so a fresh Day 1 comes along every week or two.
"""
import argparse
import datetime as dt
import glob
import json
import os
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADER = os.path.join(os.path.dirname(ROOT), "kids-channel", "scripts", "upload_youtube.py")
TZ = ZoneInfo("Europe/Istanbul")
ALL = json.load(open(os.path.join(ROOT, "story", "series.json")))
SLOTS = sorted({s["slot"] for s in ALL})
LOG = os.path.join(ROOT, "logs", "uploaded.txt")
TOKEN = os.path.join(ROOT, "secrets", "token.json")
CHANNEL = "UCtjcmQc9DV_sKh4_3UrToIQ"  # Outbreak Diary; the uploader refuses a token for any other channel


def uploaded(vid):
    return os.path.exists(LOG) and any(line.startswith(f"{vid}.mp4 ") for line in open(LOG))


def published_before(sid, date):
    """The highest part of a story published on an earlier day than `date` (0 if none)."""
    days = glob.glob(os.path.join(ROOT, "story", sid, "used", "*"))
    return max((json.load(open(p))["episode"] for d in days if os.path.basename(d) < date
                for p in glob.glob(os.path.join(d, "*.json"))), default=0)


def active(slot, date):
    """The story that owns a slot on `date`: the first one in series.json whose finale is not yet behind it. A re-run on
    the finale's own day still finds the finished story, so a failed upload is retried rather than skipped."""
    for s in ALL:
        if s["slot"] == slot and not (s.get("finale") and published_before(s["id"], date) >= s["finale"]):
            return s
    return None


def due(date):
    weekday = dt.date.fromisoformat(date).weekday()  # some stories (the specials) only run on certain days
    out = []
    for e in SLOTS:
        s = active(e, date)  # None: the story ended and no next one is ready; make() then says so loudly
        if not uploaded(f"{date}-{e}") and (s is None or weekday in s.get("weekdays", range(7))):
            out.append(e)
    return out


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
    series = active(e, date)
    if not series:
        raise SystemExit(f"no story owns slot {e}: add the next story to story/series.json")
    py = sys.executable
    run(py, "scripts/diary.py", "--series", series["id"], "--id", vid,
        *([] if upload else ["--keep"]))  # a test render leaves the story where it is
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    mp4 = f"out/{vid}.mp4"
    run("npx", "remotion", "render", "src/index.tsx", "Diary", mp4, f"--props=build/{vid}/props.json", "--timeout=120000",
        "--log=error", tries=3)
    if not upload:
        print(f"rendered {mp4} (not uploaded)")
        return
    days, at = series["publish"]
    publish = dt.datetime.combine(dt.date.fromisoformat(date) + dt.timedelta(days=days), dt.time.fromisoformat(at), TZ)
    args = [py, UPLOADER, "--video", mp4, "--meta", f"build/{vid}/meta.json", "--log", LOG, "--general-audience",
            "--client", "secrets/client_secret.json", "--token", TOKEN, "--expect-channel", CHANNEL]
    if "https://www.googleapis.com/auth/youtube" in json.load(open(TOKEN)).get("scopes", []):  # token made with --manage
        args += ["--playlist", f"{series['name']} | Outbreak Diary", "--playlist-description",
                 f"{series['about']} Every day of the story, in order."]
    if publish - dt.datetime.now(TZ) > dt.timedelta(minutes=15):
        args += ["--publish-at", publish.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")]
    else:
        args += ["--privacy", "public"]
    run(*args)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kind", choices=SLOTS + ["auto", "due"])
    p.add_argument("--date", default="")
    p.add_argument("--no-upload", action="store_true")
    a = p.parse_args()
    date = a.date or dt.datetime.now(TZ).date().isoformat()
    if a.kind == "due":
        print(" ".join(due(date)))
        return
    failed = []
    for e in due(date) if a.kind == "auto" else [a.kind]:
        try:  # one story without a script must not stop the others
            make(e, date, not a.no_upload)
        except SystemExit as err:
            print(f"{e} ({(active(e, date) or {}).get('id')}): {err}", flush=True)
            failed.append(e)
    if failed:
        raise SystemExit(f"not made: {' '.join(failed)}")


if __name__ == "__main__":
    main()
