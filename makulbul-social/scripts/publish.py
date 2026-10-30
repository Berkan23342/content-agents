"""Publishes one day's reel to Instagram (Reels, shared to feed) and TikTok with the official APIs.

  python3 scripts/publish.py content/2026-10-31 [--only instagram|tiktok] [--dry-run]

Needs secrets/instagram.json and/or secrets/tiktok.json (made by scripts/connect.py). A platform
without credentials is skipped; the result of every platform is written to content/<day>/published.json.
"""
import argparse
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS = os.path.join(ROOT, "secrets")
IG_API = "https://graph.instagram.com/v23.0"
TT_API = "https://open.tiktokapis.com/v2"


def http(method, url, data=None, headers=None, raw=None, timeout=120):
    body = raw
    headers = dict(headers or {})
    if data is not None and raw is None:
        if headers.get("Content-Type") == "application/json":
            body = json.dumps(data).encode()
        else:
            body = urllib.parse.urlencode(data).encode()
            headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                text = r.read().decode() or "{}"
                return json.loads(text)
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            if e.code >= 500 and attempt < 4:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"{method} {url.split('?')[0]} -> {e.code}: {detail[:500]}")
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt == 4:
                raise
            time.sleep(15 * (attempt + 1))  # flaky connection


def load(name):
    path = os.path.join(SECRETS, f"{name}.json")
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        return json.load(fh)


def save(name, data):
    path = os.path.join(SECRETS, f"{name}.json")
    with open(path, "w") as fh:
        json.dump(data, fh, indent=1)
    os.chmod(path, 0o600)


# ---------------------------------------------------------------- Instagram (Instagram API with Instagram Login)
def instagram(video, caption, dry):
    cfg = load("instagram")
    if not cfg:
        return {"status": "skipped", "reason": "secrets/instagram.json yok"}
    token = cfg["access_token"]
    # long-lived tokens last 60 days; refresh when less than 15 days are left
    if cfg.get("expires_at", 0) - time.time() < 15 * 86400:
        r = http("GET", f"https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token={token}")
        token = cfg["access_token"] = r["access_token"]
        cfg["expires_at"] = time.time() + r.get("expires_in", 5184000)
        save("instagram", cfg)
    if dry:
        me = http("GET", f"{IG_API}/me?fields=user_id,username&access_token={token}")
        return {"status": "dry-run", "account": me.get("username")}
    uid = cfg["user_id"]
    c = http("POST", f"{IG_API}/{uid}/media", {"media_type": "REELS", "upload_type": "resumable", "caption": caption,
                                               "share_to_feed": "true", "access_token": token})
    size = os.path.getsize(video)
    with open(video, "rb") as fh:
        http("POST", c["uri"], raw=fh.read(), headers={"Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size)}, timeout=600)
    for _ in range(60):  # Instagram processes the video before it can be published
        st = http("GET", f"{IG_API}/{c['id']}?fields=status_code,status&access_token={token}")
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"instagram processing failed: {st}")
        time.sleep(10)
    pub = http("POST", f"{IG_API}/{uid}/media_publish", {"creation_id": c["id"], "access_token": token})
    link = http("GET", f"{IG_API}/{pub['id']}?fields=permalink&access_token={token}").get("permalink")
    return {"status": "published", "id": pub["id"], "url": link}


# ---------------------------------------------------------------- TikTok (Content Posting API)
def tiktok_token(cfg):
    if cfg.get("expires_at", 0) - time.time() > 600:
        return cfg["access_token"]
    r = http("POST", f"{TT_API}/oauth/token/", {"client_key": cfg["client_key"], "client_secret": cfg["client_secret"],
                                                "grant_type": "refresh_token", "refresh_token": cfg["refresh_token"]})
    cfg.update(access_token=r["access_token"], refresh_token=r.get("refresh_token", cfg["refresh_token"]),
               expires_at=time.time() + r.get("expires_in", 86400))
    save("tiktok", cfg)
    return cfg["access_token"]


def tiktok(video, caption, dry):
    cfg = load("tiktok")
    if not cfg:
        return {"status": "skipped", "reason": "secrets/tiktok.json yok"}
    token = tiktok_token(cfg)
    auth = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    size = os.path.getsize(video)
    source = {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1}
    # until TikTok audits the app, direct posts may only be private, so send drafts to the TikTok inbox instead
    direct = cfg.get("audited", False)
    if dry:
        info = http("POST", f"{TT_API}/post/publish/creator_info/query/", {}, headers=auth)
        return {"status": "dry-run", "account": info.get("data", {}).get("creator_username"), "mode": "direct" if direct else "inbox"}
    if direct:
        info = http("POST", f"{TT_API}/post/publish/creator_info/query/", {}, headers=auth)["data"]
        privacy = "PUBLIC_TO_EVERYONE" if "PUBLIC_TO_EVERYONE" in info["privacy_level_options"] else info["privacy_level_options"][0]
        init = http("POST", f"{TT_API}/post/publish/video/init/", {
            "post_info": {"title": caption[:2200], "privacy_level": privacy, "disable_comment": False, "disable_duet": False,
                          "disable_stitch": False, "video_cover_timestamp_ms": 1500},
            "source_info": source}, headers=auth)["data"]
    else:
        init = http("POST", f"{TT_API}/post/publish/inbox/video/init/", {"source_info": source}, headers=auth)["data"]
    with open(video, "rb") as fh:
        http("PUT", init["upload_url"], raw=fh.read(), headers={"Content-Type": "video/mp4", "Content-Range": f"bytes 0-{size - 1}/{size}"}, timeout=600)
    for _ in range(60):
        st = http("POST", f"{TT_API}/post/publish/status/fetch/", {"publish_id": init["publish_id"]}, headers=auth)["data"]
        if st.get("status") in ("PUBLISH_COMPLETE", "SEND_TO_USER_INBOX"):
            return {"status": "published" if direct else "inbox", "id": init["publish_id"]}
        if st.get("status") == "FAILED":
            raise RuntimeError(f"tiktok failed: {st}")
        time.sleep(10)
    return {"status": "pending", "id": init["publish_id"]}


def notify(message):
    if shutil.which("osascript"):  # macOS only
        subprocess.run(["osascript", "-e", f'display notification "{message}" with title "Makulbul"'], check=False)
    else:
        print(message)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("day")
    p.add_argument("--only", choices=["instagram", "tiktok"])
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    day = os.path.abspath(a.day)
    video = os.path.join(day, "reel.mp4")
    with open(os.path.join(day, "caption.txt")) as fh:
        caption = fh.read().strip()
    out_path = os.path.join(day, "published.json")
    results = json.load(open(out_path)) if os.path.exists(out_path) else {}
    for name, fn in (("instagram", instagram), ("tiktok", tiktok)):
        if a.only and a.only != name:
            continue
        if results.get(name, {}).get("status") in ("published", "inbox") and not a.dry_run:
            print(f"{name}: already done")
            continue
        try:
            results[name] = fn(video, caption, a.dry_run)
        except Exception as e:  # keep going with the other platform
            results[name] = {"status": "error", "error": str(e)[:800]}
        print(f"{name}: {results[name]}")
    if not a.dry_run:
        with open(out_path, "w") as fh:
            json.dump(results, fh, indent=1, ensure_ascii=False)
        done = [k for k, v in results.items() if v.get("status") in ("published", "inbox")]
        notify(f"Bugünün reels'i: {', '.join(done) if done else 'elle paylaşılmayı bekliyor'}")


if __name__ == "__main__":
    main()
