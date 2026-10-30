"""One-time account connection for Instagram and TikTok. Secrets are read from the clipboard (pbpaste), never printed.

Instagram (token from Meta developer dashboard > Instagram > API setup with Instagram login > Generate token):
  pbpaste | python3 scripts/connect.py instagram

TikTok (app from developers.tiktok.com with Login Kit + Content Posting API, redirect URI https://makulbul.com/):
  python3 scripts/connect.py tiktok-app <client_key>     then copy the client secret and:
  pbpaste | python3 scripts/connect.py tiktok-secret
  python3 scripts/connect.py tiktok-url                  open the printed URL, approve, copy the address you land on
  pbpaste | python3 scripts/connect.py tiktok-code

Each step saves secrets/<platform>.json (chmod 600). Copy them to GitHub with
  gh secret set INSTAGRAM_JSON < secrets/instagram.json   /   gh secret set TIKTOK_JSON < secrets/tiktok.json
"""
import json
import os
import secrets as rnd
import sys
import time
import urllib.parse

from publish import SECRETS, http, load, save

REDIRECT = "https://makulbul.com/"
SCOPES = "user.info.basic,video.upload,video.publish"


def stdin_secret():
    value = sys.stdin.read().strip()
    if not value:
        raise SystemExit("clipboard is empty")
    return value


def main():
    os.makedirs(SECRETS, exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "instagram":
        token = stdin_secret()
        me = http("GET", f"https://graph.instagram.com/v23.0/me?fields=user_id,username&access_token={token}")
        save("instagram", {"user_id": me["user_id"], "username": me["username"], "access_token": token,
                           "expires_at": time.time() + 55 * 86400})
        print(f"Instagram connected: @{me['username']}")
    elif cmd == "tiktok-app":
        save("tiktok_app", {"client_key": sys.argv[2]})
        print("client key saved")
    elif cmd == "tiktok-secret":
        app = load("tiktok_app")
        app["client_secret"] = stdin_secret()
        save("tiktok_app", app)
        print("client secret saved")
    elif cmd == "tiktok-url":
        app = load("tiktok_app")
        app["state"] = rnd.token_urlsafe(16)
        save("tiktok_app", app)
        q = urllib.parse.urlencode({"client_key": app["client_key"], "scope": SCOPES, "response_type": "code",
                                    "redirect_uri": REDIRECT, "state": app["state"]})
        print(f"https://www.tiktok.com/v2/auth/authorize/?{q}")
    elif cmd == "tiktok-code":
        app = load("tiktok_app")
        params = urllib.parse.parse_qs(urllib.parse.urlparse(stdin_secret()).query)
        if params.get("state", [""])[0] != app.get("state"):
            raise SystemExit("state does not match; open a fresh tiktok-url")
        r = http("POST", "https://open.tiktokapis.com/v2/oauth/token/", {
            "client_key": app["client_key"], "client_secret": app["client_secret"], "code": params["code"][0],
            "grant_type": "authorization_code", "redirect_uri": REDIRECT})
        if "access_token" not in r:
            raise SystemExit(f"TikTok refused: {r.get('error')} {r.get('error_description')}")
        save("tiktok", {"client_key": app["client_key"], "client_secret": app["client_secret"], "open_id": r["open_id"],
                        "access_token": r["access_token"], "refresh_token": r["refresh_token"],
                        "expires_at": time.time() + r["expires_in"], "scope": r.get("scope"), "audited": False})
        print(f"TikTok connected (scopes: {r.get('scope')})")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
