"""YouTube Data API v3 — any public channel.

Consolidates the helpers that tend to get copy-pasted across files
(`_fmt`, `_fmt_duration`, `_get_video_stats_batch`).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone

from . import auth
from .contract import CONFIG_DIR, EXIT_NO_DATA, ToolError

# --- Formatting ------------------------------------------------------------

def fmt(n) -> str:
    """1234567 -> '1.2M'"""
    n = int(n or 0)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


_DUR = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


def fmt_duration(iso: str) -> str:
    """'PT1H2M3S' -> '1:02:03'"""
    m = _DUR.match(iso or "")
    if not m:
        return "?"
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return f"{h}:{mi:02d}:{s:02d}" if h else f"{mi}:{s:02d}"


def seconds(iso: str) -> int:
    m = _DUR.match(iso or "")
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


# --- Channels --------------------------------------------------------------

def channel_info(channel_id: str | None = None) -> dict:
    """Info for one channel. With no argument, your own channel."""
    yt = auth.youtube(public_only=channel_id is not None)
    parts = "snippet,statistics,contentDetails"
    req = (yt.channels().list(part=parts, mine=True) if channel_id is None
           else yt.channels().list(part=parts, id=channel_id))
    items = req.execute().get("items", [])
    if not items:
        raise ToolError(f"Channel not found: {channel_id or 'own'}", EXIT_NO_DATA)
    c = items[0]
    st, sn = c["statistics"], c["snippet"]
    return {
        "channel_id": c["id"],
        "title": sn["title"],
        "description": sn.get("description", ""),
        "country": sn.get("country"),
        "created_at": sn.get("publishedAt"),
        "subscribers": int(st.get("subscriberCount", 0)),
        "total_views": int(st.get("viewCount", 0)),
        "total_videos": int(st.get("videoCount", 0)),
        "uploads_playlist": c["contentDetails"]["relatedPlaylists"]["uploads"],
    }


def channel_videos(channel_id: str | None = None, max_results: int = 50) -> list[dict]:
    """Recent videos from a channel, newest first."""
    yt = auth.youtube(public_only=channel_id is not None)
    uploads = channel_info(channel_id)["uploads_playlist"]
    videos, token = [], None
    while len(videos) < max_results:
        resp = yt.playlistItems().list(
            part="snippet", playlistId=uploads,
            maxResults=min(50, max_results - len(videos)), pageToken=token,
        ).execute()
        for it in resp.get("items", []):
            sn = it["snippet"]
            thumbs = sn.get("thumbnails", {})
            best = thumbs.get("maxres") or thumbs.get("high") or thumbs.get("default", {})
            videos.append({
                "video_id": sn["resourceId"]["videoId"],
                "title": sn["title"],
                "published_at": sn.get("publishedAt"),
                "description": sn.get("description", ""),
                "thumbnail": best.get("url"),
            })
        token = resp.get("nextPageToken")
        if not token:
            break
    return videos[:max_results]


# --- Videos ----------------------------------------------------------------

def video_stats(video_ids: list[str]) -> list[dict]:
    """Public stats, in batches of 50."""
    if not video_ids:
        return []
    yt = auth.youtube(public_only=True)
    out = []
    for i in range(0, len(video_ids), 50):
        lote = video_ids[i:i + 50]
        resp = yt.videos().list(
            part="snippet,statistics,contentDetails", id=",".join(lote)
        ).execute()
        for v in resp.get("items", []):
            st, sn, cd = v["statistics"], v["snippet"], v["contentDetails"]
            thumbs = sn.get("thumbnails", {})
            best = thumbs.get("maxres") or thumbs.get("high") or thumbs.get("default", {})
            views = int(st.get("viewCount", 0))
            likes = int(st.get("likeCount", 0))
            comentarios = int(st.get("commentCount", 0))
            out.append({
                "video_id": v["id"],
                "title": sn["title"],
                "channel_id": sn["channelId"],
                "channel_title": sn["channelTitle"],
                "published_at": sn.get("publishedAt"),
                "description": sn.get("description", ""),
                "tags": sn.get("tags", []),
                "thumbnail": best.get("url"),
                "duration": cd.get("duration"),
                "duration_s": seconds(cd.get("duration", "")),
                "views": views,
                "likes": likes,
                "comments": comentarios,
                "engagement_rate": round((likes + comentarios) / views * 100, 2)
                if views else 0,
            })
    return out


def channel_mean_views(channel_id: str, sample: int = 15) -> float:
    """Mean views over the last N uploads — the base of the outlier ratio."""
    vids = channel_videos(channel_id, max_results=sample)
    if not vids:
        return 0.0
    stats = video_stats([v["video_id"] for v in vids])
    if not stats:
        return 0.0
    return sum(s["views"] for s in stats) / len(stats)


def playlist_items(playlist_id: str, days: int | None = None) -> list[dict]:
    """Items in a playlist. With `days`, only recently added ones."""
    yt = auth.youtube(public_only=True)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)) if days else None
    items, token = [], None
    while True:
        resp = yt.playlistItems().list(
            part="snippet", playlistId=playlist_id, maxResults=50, pageToken=token
        ).execute()
        for it in resp.get("items", []):
            sn = it["snippet"]
            added_on = datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))
            if cutoff and added_on < cutoff:
                return items  # the playlist comes newest-first
            items.append({
                "video_id": sn["resourceId"]["videoId"],
                "title": sn["title"],
                "added_at": sn["publishedAt"],
            })
        token = resp.get("nextPageToken")
        if not token:
            return items


def search(query: str, max_results: int = 10, order: str = "viewCount",
           duration: str = "medium", days: int | None = None) -> list[dict]:
    """search.list — COSTS 100 QUOTA UNITS. Always cache it."""
    yt = auth.youtube(public_only=True)
    params = {
        "part": "snippet", "q": query, "type": "video", "order": order,
        "maxResults": max_results,
    }
    if duration and duration != "any":
        params["videoDuration"] = duration
    if days:
        desde = datetime.now(timezone.utc) - timedelta(days=days)
        params["publishedAfter"] = desde.strftime("%Y-%m-%dT%H:%M:%SZ")
    resp = yt.search().list(**params).execute()
    ids = [it["id"]["videoId"] for it in resp.get("items", [])]
    return video_stats(ids)


# --- Configuration ---------------------------------------------------------

def load_config() -> dict:
    path = CONFIG_DIR / "config.json"
    if not path.exists():
        raise ToolError(f"Missing {path}", EXIT_NO_DATA)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_channels(items: str | None = None) -> list[dict]:
    """Competitor and inspiration channels, with their `list_type` injected."""
    path = CONFIG_DIR / "channels_lists.json"
    if not path.exists():
        raise ToolError(f"Missing {path}", EXIT_NO_DATA)
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    if items and items not in cfg:
        raise ToolError(
            f"List {items!r} does not exist in {path.name}.", EXIT_NO_DATA,
            f"Listas disponibles: {', '.join(cfg)}")
    out = []
    for kind, entries in cfg.items():
        if items and kind != items:
            continue
        for e in entries:
            out.append({**e, "list_type": kind})
    return out
