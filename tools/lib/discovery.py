"""Channel discovery: from search results to candidate channels.

Pure logic, no API calls, so it can be tested offline. The tool that feeds it
lives in tools/yt_discover_channels.py.

A candidate is a channel that has at least one video clearing ALL the
thresholds: enough views, recent enough, long-form, and well above that
channel's own mean. One lucky video on a huge channel is not the same signal as
a small channel landing 3x its usual, and the ratio is what tells them apart.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

DEFAULTS = {
    "min_ratio": 3.0,        # views / the channel's own recent mean
    "min_views": 100_000,    # absolute floor; lower it for small-language niches
    "max_days": 180,         # older than this is history, not an opportunity
    "min_duration_s": 240,   # below this it is a Short or a clip
}

# Formats that are not one person carrying the video. Flagged, never dropped:
# the creator decides whether a panel format is a fair reference.
_NOT_SOLO = re.compile(
    r"\b(podcast|episodio|episode|ep\.?\s*\d+|entrevista|interview|"
    r"live|directo|en vivo|stream|clip)\b|#\d+", re.IGNORECASE)


def thresholds(cfg: dict | None, **overrides) -> dict:
    """Defaults, then config.json `discovery`, then CLI overrides."""
    out = dict(DEFAULTS)
    out.update({k: v for k, v in ((cfg or {}).get("discovery") or {}).items()
                if k in DEFAULTS and v is not None})
    out.update({k: v for k, v in overrides.items() if k in DEFAULTS and v is not None})
    return out


def age_days(published_at: str | None, now: datetime | None = None) -> int | None:
    if not published_at:
        return None
    now = now or datetime.now(timezone.utc)
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (now - dt).days


def prefilter(video: dict, th: dict, now: datetime | None = None) -> bool:
    """Checks that need no extra API call. Run before fetching channel means."""
    days = age_days(video.get("published_at"), now)
    return (video.get("views", 0) >= th["min_views"]
            and days is not None and days <= th["max_days"]
            and video.get("duration_s", 0) >= th["min_duration_s"])


def outliers(videos: list[dict], means: dict[str, float], th: dict,
             now: datetime | None = None) -> list[dict]:
    """Videos that clear every threshold, with their ratio and flags."""
    out = []
    for v in videos:
        if not prefilter(v, th, now):
            continue
        mean = means.get(v["channel_id"]) or 0
        if not mean:
            continue
        ratio = round(v["views"] / mean, 2)
        if ratio < th["min_ratio"]:
            continue
        out.append({**v, "ratio": ratio, "days": age_days(v.get("published_at"), now),
                    "not_solo": bool(_NOT_SOLO.search(v.get("title", "")))})
    return out


def group_by_channel(found: list[dict], existing: dict[str, str] | None = None) -> list[dict]:
    """One row per channel, strongest first.

    `existing` maps channel_id -> list name for channels already configured,
    so the creator is not asked twice about the same one.
    """
    existing = existing or {}
    rows: dict[str, dict] = {}
    for v in found:
        r = rows.setdefault(v["channel_id"], {
            "channel_id": v["channel_id"], "name": v["channel_title"],
            "outliers": 0, "terms": [], "best": None,
            "already_in": existing.get(v["channel_id"]), "not_solo": True,
            "languages": [],
        })
        if v.get("language") and v["language"] not in r["languages"]:
            r["languages"].append(v["language"])
        r["outliers"] += 1
        if v.get("term") and v["term"] not in r["terms"]:
            r["terms"].append(v["term"])
        # A channel counts as solo if ANY of its outliers is solo.
        r["not_solo"] = r["not_solo"] and v["not_solo"]
        if r["best"] is None or v["ratio"] > r["best"]["ratio"]:
            r["best"] = {k: v[k] for k in ("video_id", "title", "views", "ratio", "days")}
    return sorted(rows.values(),
                  key=lambda r: (r["outliers"], r["best"]["ratio"]), reverse=True)


# --- channels_lists.json editing --------------------------------------------

def add_channel(cfg: dict, list_name: str, entry: dict) -> dict:
    """Add or move a channel into a list. A channel lives in one list only."""
    if list_name.startswith("_"):
        raise ValueError(f"{list_name!r} is a documentation key, not a list")
    cfg = remove_channel(cfg, entry["channel_id"])
    cfg.setdefault(list_name, []).append(
        {"channel_id": entry["channel_id"], "name": entry.get("name", ""),
         "notes": entry.get("notes", ""), "origin": entry.get("origin", "curated")})
    return cfg


def remove_channel(cfg: dict, channel_id: str) -> dict:
    return {k: ([c for c in v if c.get("channel_id") != channel_id]
                if not k.startswith("_") and isinstance(v, list) else v)
            for k, v in cfg.items()}
