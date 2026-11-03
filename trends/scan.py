"""Finds what is working right now in our three niches, for the writer agents (twice a week, .github/workflows/trends.yml).

For each niche in queries.json it searches YouTube for the most-viewed videos of the last 30 days, ranks them by views
per day (how fast they grow) and writes trends/latest.md plus trends/history/<date>.json. The writers read latest.md to
borrow topics, premises, hooks and title patterns. They never copy anyone's script, characters, pictures or music.

  python3 trends/scan.py --token quiz-channel/secrets/token.json --client kids-channel/secrets/client_secret.json
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "kids-channel", "scripts"))

from googleapiclient.discovery import build  # noqa: E402
from upload_youtube import READONLY, credentials  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DAYS = 30
TOP = 12


def seconds(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    h, mi, s = (int(x or 0) for x in m.groups()) if m else (0, 0, 0)
    return h * 3600 + mi * 60 + s


def scan(yt, niche, now):
    after = (now - dt.timedelta(days=DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ids = {}
    for q in niche["queries"]:
        r = yt.search().list(part="id", q=q, type="video", order="viewCount", publishedAfter=after, maxResults=15,
                             relevanceLanguage="en", videoDuration="short" if niche["short"] else "any").execute()
        for item in r.get("items", []):
            ids.setdefault(item["id"]["videoId"], q)
    videos = []
    keys = list(ids)
    for i in range(0, len(keys), 50):
        r = yt.videos().list(part="snippet,statistics,contentDetails", id=",".join(keys[i:i + 50])).execute()
        for v in r["items"]:
            published = dt.datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
            age = max(1.0, (now - published).total_seconds() / 86400)
            views = int(v["statistics"].get("viewCount", 0))
            videos.append({
                "id": v["id"], "title": v["snippet"]["title"], "channel": v["snippet"]["channelTitle"],
                "views": views, "per_day": round(views / age), "age_days": round(age),
                "seconds": seconds(v["contentDetails"].get("duration")), "query": ids[v["id"]],
                "tags": v["snippet"].get("tags", [])[:8],
            })
    return sorted(videos, key=lambda v: v["per_day"], reverse=True)[:TOP]


def report(results, now):
    out = [f"# Trends, {now:%Y-%m-%d}", "",
           f"The fastest-growing videos of the last {DAYS} days in our niches, by views per day. Borrow the topic, the",
           "premise, the hook or the title pattern; never copy a script, characters, pictures or music.", ""]
    for key, (niche, videos) in results.items():
        out += [f"## {key}: {niche['name']}", "", "| views/day | views | length | title | channel |", "|---|---|---|---|---|"]
        for v in videos:
            title = v["title"].replace("|", "/")
            out.append(f"| {v['per_day']:,} | {v['views']:,} | {v['seconds']}s | [{title}](https://youtu.be/{v['id']}) | {v['channel']} |")
        out.append("")
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--token", required=True)
    p.add_argument("--client", required=True)
    a = p.parse_args()
    yt = build("youtube", "v3", credentials=credentials(a.client, a.token, ["https://www.googleapis.com/auth/youtube.upload", READONLY]))
    niches = json.load(open(os.path.join(HERE, "queries.json")))
    now = dt.datetime.now(dt.timezone.utc)
    results = {key: (niche, scan(yt, niche, now)) for key, niche in niches.items()}
    with open(os.path.join(HERE, "history", f"{now:%Y-%m-%d}.json"), "w") as fh:
        json.dump({k: v for k, (_, v) in results.items()}, fh, indent=1, ensure_ascii=False)
    with open(os.path.join(HERE, "latest.md"), "w") as fh:
        fh.write(report(results, now))
    print(f"trends: {sum(len(v) for _, v in results.values())} videos -> trends/latest.md")


if __name__ == "__main__":
    main()
