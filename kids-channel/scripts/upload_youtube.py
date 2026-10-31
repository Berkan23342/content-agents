"""Uploads a video to the channel with the official YouTube Data API v3.

One-time setup: put the OAuth "Desktop app" client file at secrets/client_secret.json.
The first run opens a browser to sign in with the channel account; the token is
then cached in secrets/token.json so later (scheduled) runs need no interaction.

Example:
  .venv/bin/python scripts/upload_youtube.py --video out/x.mp4 --title "..." \
      --description-file out/x.txt --tags "kids,colors" --thumbnail out/x.jpg --privacy private
"""
import argparse
import json
import os
import shutil
import subprocess
import time

import httplib2

from google.auth.exceptions import RefreshError, TransportError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS = os.path.join(ROOT, "secrets")
CLIENT = os.path.join(SECRETS, "client_secret.json")
TOKEN = os.path.join(SECRETS, "token.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
READONLY = "https://www.googleapis.com/auth/youtube.readonly"  # only in tokens made with --sign-in
EDUCATION = "27"


def notify(message: str):
    if shutil.which("osascript"):  # macOS only
        subprocess.run(["osascript", "-e", f'display notification "{message}" with title "Bubbly Kids TV"'], check=False)
    else:
        print(message)


def credentials(client=CLIENT, token=TOKEN, scopes=SCOPES) -> Credentials:
    creds = Credentials.from_authorized_user_file(token, scopes) if os.path.exists(token) else None
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError:  # testing-mode tokens expire after 7 days
            creds = None
    if not creds or not creds.valid:
        notify("YouTube girişi gerekiyor: açılan tarayıcı sayfasında izin verin.")
        flow = InstalledAppFlow.from_client_secrets_file(client, scopes)
        creds = flow.run_local_server(port=0, timeout_seconds=3 * 3600)
        if not creds:
            raise SystemExit("sign-in timed out")
    with open(token, "w") as fh:
        fh.write(creds.to_json())
    return creds


def upload(video, title, description, tags, thumbnail=None, privacy="private", publish_at=None, creds=None, for_kids=True):
    youtube = build("youtube", "v3", credentials=creds or credentials())
    status = {"privacyStatus": privacy, "selfDeclaredMadeForKids": for_kids}
    if publish_at:  # scheduled publishing only works on private videos
        status.update(privacyStatus="private", publishAt=publish_at)
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": EDUCATION,
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": status,
    }
    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=MediaFileUpload(video, chunksize=8 * 1024 * 1024, resumable=True)
    )
    response = None
    failures = 0
    while response is None:
        try:
            progress, response = request.next_chunk()
        except (HttpError, OSError, httplib2.HttpLib2Error, TransportError) as e:
            # a flaky connection: the resumable upload continues from the last saved chunk
            if isinstance(e, HttpError) and e.resp.status not in (500, 502, 503, 504):
                raise
            failures += 1
            if failures > 20:  # about an hour without any progress
                raise
            wait = min(300, 5 * 2 ** failures)
            print(f"upload interrupted ({type(e).__name__}), retrying in {wait}s")
            time.sleep(wait)
            continue
        failures = 0
        if progress:
            print(f"uploading {int(progress.progress() * 100)}%")
    video_id = response["id"]
    print(f"uploaded https://youtu.be/{video_id} ({response['status']['privacyStatus']}, publishAt={response['status'].get('publishAt')})")

    if thumbnail:
        try:
            youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumbnail)).execute()
            print("thumbnail set")
        except (HttpError, OSError, httplib2.HttpLib2Error, TransportError) as e:  # custom thumbnails need a phone-verified channel
            print(f"thumbnail skipped: {getattr(e, 'reason', e)}")
    return video_id


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--video")
    p.add_argument("--meta", help="JSON with title, description and tags (from scripts/episode.py)")
    p.add_argument("--title")
    p.add_argument("--description-file")
    p.add_argument("--tags", default="")
    p.add_argument("--thumbnail")
    p.add_argument("--privacy", choices=["private", "unlisted", "public"], default="private")
    p.add_argument("--publish-at", help="RFC 3339 time, e.g. 2026-11-01T16:00:00Z")
    p.add_argument("--log", help="append '<video> <url>' to this file after uploading")
    p.add_argument("--client", default=CLIENT, help="OAuth client file (default secrets/client_secret.json)")
    p.add_argument("--token", default=TOKEN, help="token of the channel to upload to (default secrets/token.json)")
    p.add_argument("--general-audience", action="store_true", help="not made for kids (other channels)")
    p.add_argument("--sign-in", action="store_true", help="only sign in and save --token, then stop")
    p.add_argument("--expect-channel", help="upload only if the token belongs to this channel id (token made with --sign-in)")
    a = p.parse_args()
    if a.sign_in:  # read-only access too, so the token can tell which channel it belongs to
        creds = credentials(a.client, a.token, SCOPES + [READONLY])
        me = build("youtube", "v3", credentials=creds).channels().list(part="snippet", mine=True).execute()["items"][0]
        print(f"saved {a.token} for channel {me['snippet']['title']} ({me['id']})")
        return
    if a.meta:
        meta = json.load(open(a.meta))
        title, description, tags = meta["title"], meta["description"], meta["tags"]
    else:
        title = a.title
        description = open(a.description_file).read() if a.description_file else ""
        tags = [t.strip() for t in a.tags.split(",") if t.strip()]
    creds = credentials(a.client, a.token, SCOPES + [READONLY] if a.expect_channel else SCOPES)
    if a.expect_channel:
        mine = build("youtube", "v3", credentials=creds).channels().list(part="id", mine=True).execute()["items"][0]["id"]
        if mine != a.expect_channel:
            raise SystemExit(f"the token belongs to channel {mine}, not {a.expect_channel}: not uploading")
    video_id = upload(a.video, title, description, tags, a.thumbnail, a.privacy, a.publish_at, creds, not a.general_audience)
    if a.log:
        with open(a.log, "a") as fh:
            fh.write(f"{os.path.basename(a.video)} https://youtu.be/{video_id}\n")


if __name__ == "__main__":
    main()
