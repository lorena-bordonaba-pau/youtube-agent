"""Google authentication — never blocking.

Two ways in, and the cheap one comes first:

**API key** (`YOUTUBE_API_KEY`). Enough for everything public: any channel's
stats, a video's data, search, thumbnails, transcripts. No OAuth, no consent
screen, no browser. This is what lets someone try the harness sixty seconds
after cloning it.

**OAuth** (`data/auth/client_secrets.json` + a token). Only needed for *your
own* channel's analytics: retention, traffic sources, demographics, search
terms. Those endpoints are private and a key cannot reach them.

This layer NEVER calls `run_local_server` during a normal run: if the token is
missing or will not refresh, it exits with EXIT_AUTH and tells the agent which
command to run. A browser opening mid-session hangs the agent indefinitely.
"""
from __future__ import annotations

import os
import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from . import base  # noqa: F401 — importing it loads .env
from .contract import DATA_DIR, EXIT_AUTH, ToolError

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
]

AUTH_DIR = DATA_DIR / "auth"
SECRETS_FILE = AUTH_DIR / "client_secrets.json"
TOKEN_FILE = AUTH_DIR / "token.pickle"
API_KEY_ENV = "YOUTUBE_API_KEY"

_HINT = (
    "Run `python3 tools/auth_setup.py` once to authorise. That command DOES "
    "open a browser, on purpose."
)
_HINT_PUBLIC = (
    "This tool only reads public data, so an API key is enough: put "
    f"{API_KEY_ENV}=... in your .env (create the key at "
    "console.cloud.google.com, APIs & Services > Credentials). OAuth is only "
    "needed for your own channel's private analytics."
)


def api_key() -> str | None:
    """The API key, if there is one. Public data needs nothing else."""
    return os.environ.get(API_KEY_ENV, "").strip() or None


def get_credentials(interactive: bool = False):
    creds = None
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:  # noqa: BLE001
            # A dead refresh is exactly what auth_setup exists to fix: in
            # interactive mode fall through to the browser flow instead of
            # aborting.
            if not interactive:
                raise ToolError(
                    f"The token expired and could not be refreshed: {e}",
                    EXIT_AUTH, _HINT,
                ) from e
            creds = None
        else:
            _save(creds)
            return creds

    if not interactive:
        missing = "token.pickle" if not TOKEN_FILE.exists() else "a valid token"
        raise ToolError(
            f"No usable credentials: {missing} is missing from {AUTH_DIR}.",
            EXIT_AUTH,
            _HINT,
        )

    # Only reached from auth_setup.py, which passes interactive=True.
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not SECRETS_FILE.exists():
        raise ToolError(
            f"client_secrets.json not found at {SECRETS_FILE}.",
            EXIT_AUTH,
            "Follow step 3 of the README: create a Google Cloud project, "
            "enable YouTube Data API v3 and YouTube Analytics API, create an "
            "OAuth client ID of type Desktop app, and save the downloaded "
            "JSON under that exact name.",
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(SECRETS_FILE), SCOPES)
    creds = flow.run_local_server(port=8080)
    _save(creds)
    return creds


def _save(creds) -> None:
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(creds, f)
    TOKEN_FILE.chmod(0o600)


def youtube(public_only: bool = False):
    """YouTube Data API v3 client.

    With `public_only=True` an API key is preferred, so the tool works with no
    OAuth at all. It still falls back to OAuth credentials when there is no
    key, because a token also reads public data.
    """
    if public_only:
        key = api_key()
        if key:
            return build("youtube", "v3", developerKey=key, cache_discovery=False)
        if not TOKEN_FILE.exists():
            raise ToolError(
                f"No {API_KEY_ENV} and no OAuth token.", EXIT_AUTH, _HINT_PUBLIC)
    return build("youtube", "v3", credentials=get_credentials(),
                 cache_discovery=False)


def analytics():
    """YouTube Analytics API v2 client. OAuth only: this data is private."""
    return build("youtubeAnalytics", "v2", credentials=get_credentials(),
                 cache_discovery=False)


def status() -> dict:
    """Credential status for `tools/init.py`. Never raises.

    Reports both routes, because they unlock different things: an API key is
    enough for public data, OAuth is required for your own analytics.
    """
    has_key = bool(api_key())
    if not TOKEN_FILE.exists():
        return {
            "ok": has_key,
            "reason": ("API key only: public data works, your own analytics "
                       "does not" if has_key else "no token.pickle and no "
                       f"{API_KEY_ENV}"),
            "hint": "" if has_key else (
                f"Quickest path: put {API_KEY_ENV} in your .env and public-data "
                "tools work straight away. For your own channel's analytics, "
                "run `python3 tools/auth_setup.py`."),
        }
    try:
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    except Exception as e:  # noqa: BLE001
        return {"ok": has_key, "reason": f"unreadable token ({e})", "hint": _HINT}

    if creds and creds.valid:
        return {"ok": True, "reason": "valid token", "hint": ""}
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:  # noqa: BLE001
            return {"ok": has_key, "reason": "expired token, refresh failed",
                    "hint": _HINT}
        _save(creds)
        return {"ok": True, "reason": "token refreshed", "hint": ""}
    return {"ok": has_key, "reason": "token not usable", "hint": _HINT}
