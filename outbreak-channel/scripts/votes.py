"""Counts the viewers' votes on Outbreak Diary parts that ask a question ("vote" in the script), into story/votes.json.

A part on Day N can end with a question and two one-word options ("BRIDGE or STAIRS?"); viewers answer in the
comments, and the writer follows the majority when writing Day N+3 (AGENT.md, "Viewers decide"). This runs every
morning before the writer (.github/workflows/feedback.yml), with the channel's own read-only sign-in.

  python3 scripts/votes.py --token secrets/token.json --client secrets/client_secret.json

A comment counts once per person, for the one option it names (a comment naming both counts for neither). The
channel's own comments do not count. A vote stops being counted once the part it decides has been published.

Reading comments needs the token's youtube.force-ssl permission (upload_youtube.py --sign-in --manage --comments).
votes.json "_reader" says whether it works; until it does, the checker lets no part ask the viewers, so the channel
never promises a vote it cannot count.
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "kids-channel", "scripts"))

STORY = os.path.join(ROOT, "story")
VOTES = os.path.join(STORY, "votes.json")
LOG = os.path.join(ROOT, "logs", "uploaded.txt")
CHANNEL = "UCtjcmQc9DV_sKh4_3UrToIQ"
MAX_PAGES = 10  # 100 comments a page


def links():
    """'<date>-<slot>' -> YouTube link, from the uploaded list."""
    out = {}
    for line in open(LOG) if os.path.exists(LOG) else []:
        parts = line.split()
        if len(parts) >= 2 and parts[0].endswith(".mp4"):
            out[parts[0][:-4]] = parts[1]
    return out


def asking():
    """Every published part that asks a vote: (story id, part, vote, video key, decided already?)."""
    out = []
    for sid in sorted(os.listdir(STORY)):
        used = glob.glob(os.path.join(STORY, sid, "used", "*", "*.json"))
        published = {json.load(open(p))["episode"] for p in used}
        for path in used:
            spec = json.load(open(path))
            if spec.get("vote"):
                date = os.path.basename(os.path.dirname(path))
                slot = os.path.basename(path).split("-")[0]
                out.append((sid, spec["episode"], spec["vote"], f"{date}-{slot}", spec["vote"]["decides"] in published))
    return out


def count(comments, options):
    """{option: votes}: one vote per person, for the single option the comment names."""
    seen, votes = set(), {o: 0 for o in options}
    for who, text in comments:  # oldest first: a person's first clear answer counts
        if who in seen or who == CHANNEL:
            continue
        named = [o for o in options if re.search(rf"\b{o}\b", text.upper())]
        if len(named) == 1:
            votes[named[0]] += 1
            seen.add(who)
    return votes


def fetch(yt, video_id):
    """(author channel id, text) of the video's top-level comments, oldest first."""
    out, page = [], None
    for _ in range(MAX_PAGES):
        r = yt.commentThreads().list(part="snippet", videoId=video_id, maxResults=100, textFormat="plainText",
                                     pageToken=page).execute()
        for item in r.get("items", []):
            c = item["snippet"]["topLevelComment"]["snippet"]
            out.append((c.get("publishedAt", ""), (c.get("authorChannelId") or {}).get("value", ""), c.get("textDisplay", "")))
        page = r.get("nextPageToken")
        if not page:
            break
    return [(who, text) for _, who, text in sorted(out)]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--token", required=True)
    p.add_argument("--client", required=True)
    a = p.parse_args()
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from upload_youtube import credentials

    todo = [x for x in asking() if not x[4]]
    tally = json.load(open(VOTES)) if os.path.exists(VOTES) else {}
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    scopes = json.load(open(a.token)).get("scopes") or ["https://www.googleapis.com/auth/youtube.readonly"]
    yt = build("youtube", "v3", credentials=credentials(a.client, a.token, scopes))
    url = links()
    # can we read comments at all? (try the newest upload)
    probe = next(reversed(url.values()), None)
    try:
        if probe:
            yt.commentThreads().list(part="id", videoId=probe.rsplit("/", 1)[-1], maxResults=1).execute()
        tally["_reader"] = {"ok": bool(probe), "checked": now}
    except HttpError as e:
        tally["_reader"] = {"ok": False, "checked": now, "why": str(getattr(e, "reason", e))[:120]}
    print(f"comments readable: {tally['_reader']['ok']}")
    if not todo:
        print("no open votes")
    for sid, n, vote, key, _ in todo if tally["_reader"]["ok"] else []:
        link = url.get(key)
        if not link:
            print(f"{sid} day {n}: not uploaded yet")
            continue
        try:
            comments = fetch(yt, link.rsplit("/", 1)[-1])
        except HttpError as e:  # comments turned off, or the video is not public yet
            print(f"{sid} day {n}: comments not readable ({getattr(e, 'reason', e)})")
            comments = []
        votes = count(comments, vote["options"])
        tally.setdefault(sid, {})[str(n)] = {"question": vote["question"], "options": vote["options"],
                                              "decides": vote["decides"], "video": link, "votes": votes,
                                              "comments": len(comments), "counted": now}
        print(f"{sid} day {n} {vote['question']!r}: {votes} from {len(comments)} comments")
    with open(VOTES, "w") as fh:
        json.dump(tally, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


if __name__ == "__main__":
    main()
