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
import urllib.request

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
MANAGE = "https://www.googleapis.com/auth/youtube"  # playlists and titles; only in tokens made with --sign-in --manage
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
        if os.environ.get("CI"):  # a server cannot open a browser; waiting for one would hang the job for hours
            raise SystemExit(f"{token} is missing, expired or lacks a permission: sign in again on a Mac (--sign-in)")
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


def add_to_playlist(youtube, video_id, name, description=""):
    """Adds the video to the channel's public playlist called `name`, creating the playlist the first time."""
    found, page = None, None
    while not found:
        r = youtube.playlists().list(part="snippet", mine=True, maxResults=50, pageToken=page).execute()
        found = next((p["id"] for p in r["items"] if p["snippet"]["title"] == name), None)
        page = r.get("nextPageToken")
        if not page:
            break
    if not found:
        found = youtube.playlists().insert(part="snippet,status", body={
            "snippet": {"title": name, "description": description}, "status": {"privacyStatus": "public"}}).execute()["id"]
        print(f"created playlist {name!r}")
    youtube.playlistItems().insert(part="snippet", body={
        "snippet": {"playlistId": found, "resourceId": {"kind": "youtube#video", "videoId": video_id}}}).execute()
    print(f"added to playlist {name!r}")


def set_title(youtube, video_id, title):
    v = youtube.videos().list(part="snippet", id=video_id).execute()["items"][0]
    snippet = {k: v["snippet"][k] for k in ("title", "description", "tags", "categoryId", "defaultLanguage") if k in v["snippet"]}
    snippet["title"] = title[:100]
    youtube.videos().update(part="snippet", body={"id": video_id, "snippet": snippet}).execute()
    print(f"{video_id}: {title}")


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
    p.add_argument("--manage", action="store_true", help="with --sign-in: also allow playlists and title changes")
    p.add_argument("--playlist", help="add the video to this playlist (token made with --sign-in --manage)")
    p.add_argument("--playlist-description", default="")
    p.add_argument("--set-title", metavar="VIDEO_ID", help="change the title of an uploaded video to --title, then stop")
    a = p.parse_args()
    if a.sign_in:  # read-only access too, so the token can tell which channel it belongs to
        wanted = SCOPES + [READONLY] + ([MANAGE] if a.manage else [])
        if os.path.exists(a.token):
            os.remove(a.token)  # always a fresh consent, so every permission is asked for again
        creds = credentials(a.client, a.token, wanted)
        # Google lets people untick permissions: keep only what was really granted, so later runs ask for no more
        info = json.load(urllib.request.urlopen(f"https://oauth2.googleapis.com/tokeninfo?access_token={creds.token}"))
        granted = info.get("scope", "").split()
        data = json.loads(creds.to_json())
        data["scopes"] = granted
        with open(a.token, "w") as fh:
            json.dump(data, fh)
        me = build("youtube", "v3", credentials=creds).channels().list(part="snippet", mine=True).execute()["items"][0]
        print(f"saved {a.token} for channel {me['snippet']['title']} ({me['id']})")
        missing = [s.rsplit("/", 1)[-1] for s in wanted if s not in granted]
        if missing:
            print(f"not granted: {', '.join(missing)} (the box was unticked on Google's page)")
        return
    if a.meta:
        meta = json.load(open(a.meta))
        title, description, tags = meta["title"], meta["description"], meta["tags"]
    else:
        title = a.title
        description = open(a.description_file).read() if a.description_file else ""
        tags = [t.strip() for t in a.tags.split(",") if t.strip()]
    manage = bool(a.playlist or a.set_title)
    creds = credentials(a.client, a.token, SCOPES + ([READONLY] if a.expect_channel or manage else []) + ([MANAGE] if manage else []))
    if a.set_title:
        set_title(build("youtube", "v3", credentials=creds), a.set_title, title)
        return
    if a.expect_channel:
        mine = build("youtube", "v3", credentials=creds).channels().list(part="id", mine=True).execute()["items"][0]["id"]
        if mine != a.expect_channel:
            raise SystemExit(f"the token belongs to channel {mine}, not {a.expect_channel}: not uploading")
    video_id = upload(a.video, title, description, tags, a.thumbnail, a.privacy, a.publish_at, creds, not a.general_audience)
    if a.log:
        with open(a.log, "a") as fh:
            fh.write(f"{os.path.basename(a.video)} https://youtu.be/{video_id}\n")
    if a.playlist:  # the video is up either way: a playlist problem must not cause a second upload
        try:
            add_to_playlist(build("youtube", "v3", credentials=creds), video_id, a.playlist, a.playlist_description)
        except (HttpError, RefreshError) as e:
            print(f"playlist skipped: {getattr(e, 'reason', e)}")


if __name__ == "__main__":
    main()
