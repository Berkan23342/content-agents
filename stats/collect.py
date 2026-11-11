"""Our own channels' numbers, for the writer agents: what worked last week, so they do more of it.

Every day (.github/workflows/feedback.yml) it saves the public numbers of every video of the three channels
(views, likes, comments) to stats/history/<date>.json. On Mondays (or with --report) it writes stats/latest.md: each
channel's subscribers and views this week, and every recent video with what it was (story and day, quiz format, kids
story kind...) and its views two days after publishing, the fair way to compare a new video with an older one. The
writers read it before writing (their AGENT.md files) and the weekly idea proposals use it.

Only public numbers: watch time and how many viewers swiped away need YouTube Analytics, which these sign-ins lack.

  python3 stats/collect.py --token quiz-channel/secrets/token.json --client kids-channel/secrets/client_secret.json [--report]
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(ROOT, "stats")
HISTORY = os.path.join(HERE, "history")
VIDEOS = os.path.join(HERE, "videos.json")
REPORT = os.path.join(HERE, "latest.md")
sys.path.insert(0, os.path.join(ROOT, "kids-channel", "scripts"))

CHANNELS = {  # key: (channel id, name, folder)
    "outbreak": ("UCtjcmQc9DV_sKh4_3UrToIQ", "Outbreak Diary", "outbreak-channel"),
    "quiz": ("UCyuNuzwYO9UgNt5GP0UqePg", "Brain Snack Quiz", "quiz-channel"),
    "kids": ("UCyesOPfDF24GF904c_mk71w", "Bubbly Kids TV", "kids-channel"),
}
RECENT_DAYS = 14
MAX_VIDEOS = 200  # per channel


# ---------------------------------------------------------------- collecting
def collect(yt, now):
    snap = {"taken": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "channels": {}, "videos": {}}
    known = json.load(open(VIDEOS)) if os.path.exists(VIDEOS) else {}
    r = yt.channels().list(part="statistics,contentDetails", id=",".join(c[0] for c in CHANNELS.values())).execute()
    by_id = {c["id"]: c for c in r["items"]}
    for key, (cid, _, _) in CHANNELS.items():
        c = by_id[cid]
        st = c["statistics"]
        snap["channels"][key] = {"subs": int(st.get("subscriberCount", 0)), "views": int(st.get("viewCount", 0)),
                                 "videos": int(st.get("videoCount", 0))}
        ids, page = [], None
        while len(ids) < MAX_VIDEOS:
            r = yt.playlistItems().list(part="contentDetails", playlistId=c["contentDetails"]["relatedPlaylists"]["uploads"],
                                        maxResults=50, pageToken=page).execute()
            ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
            page = r.get("nextPageToken")
            if not page:
                break
        for i in range(0, len(ids), 50):
            r = yt.videos().list(part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50])).execute()
            for v in r["items"]:
                s = v["statistics"]
                snap["videos"][v["id"]] = [int(s.get("viewCount", 0)), int(s.get("likeCount", 0)), int(s.get("commentCount", 0))]
                known[v["id"]] = {"channel": key, "title": v["snippet"]["title"], "published": v["snippet"]["publishedAt"],
                                  "seconds": seconds(v["contentDetails"].get("duration"))}
    os.makedirs(HISTORY, exist_ok=True)
    with open(os.path.join(HISTORY, f"{now:%Y-%m-%d}.json"), "w") as fh:
        json.dump(snap, fh, separators=(",", ":"))
    with open(VIDEOS, "w") as fh:
        json.dump(known, fh, indent=1, ensure_ascii=False)
    return snap, known


def seconds(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    h, mi, s = (int(x or 0) for x in m.groups()) if m else (0, 0, 0)
    return h * 3600 + mi * 60 + s


# ---------------------------------------------------------------- what each video was
def uploaded(folder, log="uploaded.txt"):
    """YouTube id -> our name for the video ('2026-11-10-e1'), from the channel's upload log."""
    out = {}
    path = os.path.join(ROOT, folder, "logs", log)
    for line in open(path) if os.path.exists(path) else []:
        parts = line.split()
        if len(parts) >= 2 and parts[0].endswith(".mp4"):
            out[parts[1].rsplit("/", 1)[-1]] = parts[0][:-4]
    return out


def load(path):
    try:
        return json.load(open(path))
    except (OSError, ValueError):
        return {}


def what_outbreak(name):
    if name.startswith("film-"):
        return "full-story film", "full-story films"
    date, _, slot = name.rpartition("-")
    found = glob.glob(os.path.join(ROOT, "outbreak-channel", "story", "*", "used", date, f"{slot}-*.json"))
    if not found:
        return "?", "?"
    spec, sid = load(found[0]), found[0].split(os.sep)[-4]
    if sid == "specials":
        return f"special ({spec.get('kind', 'story')}): {spec.get('title')}", "specials"
    extra = [spec.get("event", "")] + (["asks a vote"] if spec.get("vote") else []) + (
        ["viewers' choice"] if spec.get("voted") else [])
    extra = ", ".join(e for e in extra if e)
    return f"{sid} day {spec['episode']}" + (f" ({extra})" if extra else ""), sid + (" day 1" if spec["episode"] == 1 else "")


def what_quiz(name):
    date, _, kind = name.rpartition("-")
    if kind != "snack":
        return "old template quiz", "old template quizzes"
    found = glob.glob(os.path.join(ROOT, "quiz-channel", "snacks", "used", date, "*.json"))
    spec = load(found[0]) if found else {}
    return f"{spec.get('format', '?')} snack, topic {spec.get('topic', '?')}", f"format: {spec.get('format', '?')}"


def what_kids(name):
    m = re.match(r"(\d{4}-\d{2}-\d{2})(?:-(.+))?$", name)
    date, kind = (m.group(1), m.group(2) or "learn") if m else ("", name)
    if kind == "weekly":
        return "the week's stories in one video", "weekly compilations"
    if kind in ("story", "story-short"):
        specs = [load(p) for p in sorted(glob.glob(os.path.join(ROOT, "kids-channel", "stories", "used", date, "*.json")))]
        kinds = sorted({s.get("kind", "?") for s in specs})
        if kind == "story-short":
            return f"Short from the {'/'.join(kinds)} story", "story Shorts"
        return f"{'/'.join(kinds)} story ({len(specs)} {'story' if len(specs) == 1 else 'stories'})", f"story: {'/'.join(kinds)}"
    return f"old format ({kind})", "old formats"


WHAT = {"outbreak": what_outbreak, "quiz": what_quiz, "kids": what_kids}


# ---------------------------------------------------------------- the report
def snapshots():
    out = []
    for path in sorted(glob.glob(os.path.join(HISTORY, "*.json"))):
        s = load(path)
        if s:
            s["at"] = dt.datetime.fromisoformat(s["taken"].replace("Z", "+00:00"))
            out.append(s)
    return out


def at_two_days(vid, published, snaps):
    """Views 48-72 hours after publishing, from the first snapshot in that window (None if there is none)."""
    for s in snaps:
        hours = (s["at"] - published).total_seconds() / 3600
        if 48 <= hours <= 72 and vid in s["videos"]:
            return s["videos"][vid][0]
    return None


def num(n):
    return "-" if n is None else f"{n:,}"


def report(known, now):
    snaps = snapshots()
    last = snaps[-1]
    week_ago = next((s for s in reversed(snaps) if (now - s["at"]).days >= 7), snaps[0])
    out = [f"# Our channels, {now:%Y-%m-%d}", "",
           "Public numbers of our own videos, collected every day by stats/collect.py. **2 days** = views 48-72 hours",
           "after publishing, the fair way to compare a new video with an older one (`-` = not measured: the history",
           f"starts on {snaps[0]['at']:%Y-%m-%d}). Watch time and how many viewers swiped away are not included.", "",
           "**For the writers.** Look for patterns across several videos, not one lucky video. Lean towards the groups",
           "and kinds of video at the top, away from the bottom ones, always within your variety and repeat rules.", ""]
    for key, (_, name, folder) in CHANNELS.items():
        ours = uploaded(folder)
        ours.update(uploaded(folder, "films.txt"))
        c, c0 = last["channels"][key], week_ago["channels"].get(key, last["channels"][key])
        days = round((last["at"] - week_ago["at"]).total_seconds() / 86400)
        change = (f" ({c['subs'] - c0['subs']:+,} in {days} days)", f" ({c['views'] - c0['views']:+,})") if days else ("", "")
        out += [f"## {name}", "",
                f"Subscribers **{c['subs']:,}**{change[0]} · views **{c['views']:,}**{change[1]} · {c['videos']} videos", ""]
        rows = []
        for vid, info in known.items():
            if info["channel"] != key or vid not in last["videos"]:
                continue
            published = dt.datetime.fromisoformat(info["published"].replace("Z", "+00:00"))
            age = (now - published).total_seconds() / 86400
            views, likes, comments = last["videos"][vid]
            what, group = WHAT[key](ours[vid]) if vid in ours else ("not made by our pipeline", "other")
            rows.append({"title": info["title"], "what": what, "group": group, "age": age, "views": views,
                         "two": at_two_days(vid, published, snaps), "likes": likes, "comments": comments,
                         "date": published.date().isoformat()})
        groups = {}
        for r in rows:
            if r["age"] >= 2:
                groups.setdefault(r["group"], []).append(r)
        if groups:
            out += ["| Group | Videos | Avg views at 2 days | Avg views now | Likes per 100 views | Comments |",
                    "|---|---|---|---|---|---|"]
            def avg(xs):
                xs = [x for x in xs if x is not None]
                return round(sum(xs) / len(xs)) if xs else None
            table = []
            for g, rs in groups.items():
                views = sum(r["views"] for r in rs)
                table.append((avg([r["two"] for r in rs]), avg([r["views"] for r in rs]), g, len(rs),
                              round(100 * sum(r["likes"] for r in rs) / views, 1) if views else 0,
                              sum(r["comments"] for r in rs)))
            for two, now_avg, g, n, lk, cm in sorted(table, key=lambda t: (t[0] or -1, t[1] or 0), reverse=True):
                out.append(f"| {g} | {n} | {num(two)} | {num(now_avg)} | {lk} | {cm} |")
            out.append("")
        recent = sorted((r for r in rows if r["age"] <= RECENT_DAYS), key=lambda r: r["date"], reverse=True)
        if recent:
            out += [f"Videos of the last {RECENT_DAYS} days, newest first:", "",
                    "| Date | Title | What | Views at 2 days | Views now | Likes | Comments |", "|---|---|---|---|---|---|---|"]
            for r in recent:
                title = r["title"].replace("|", "/")[:70]
                out.append(f"| {r['date']} | {title} | {r['what']} | {num(r['two'])} | {r['views']:,} | {r['likes']} | {r['comments']} |")
            out.append("")
    with open(REPORT, "w") as fh:
        fh.write("\n".join(out))
    print(f"wrote {os.path.relpath(REPORT, ROOT)}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--token", required=True)
    p.add_argument("--client", required=True)
    p.add_argument("--report", action="store_true", help="also write stats/latest.md (the workflow does it on Mondays)")
    a = p.parse_args()
    from googleapiclient.discovery import build
    from upload_youtube import READONLY, credentials

    now = dt.datetime.now(dt.timezone.utc)
    yt = build("youtube", "v3", credentials=credentials(a.client, a.token, [READONLY]))
    snap, known = collect(yt, now)
    print(f"saved numbers of {len(snap['videos'])} videos")
    if a.report or not os.path.exists(REPORT):
        report(known, now)


if __name__ == "__main__":
    main()
