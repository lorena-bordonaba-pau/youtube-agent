"""On-disk cache with a TTL per kind of data.

The YouTube API gives you 10,000 units a day and `search.list` costs 100 per
call. Without a cache, one ideation session burns the quota repeating the same
searches.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from .contract import DATA_DIR

CACHE_DIR = DATA_DIR / "cache"

# TTL in seconds, per family of data.
TTL = {
    "own_analytics": 6 * 3600,           # changes daily, but not hourly
    "other_channel": 24 * 3600,          # third parties' public stats
    "search_query": 24 * 3600,           # search.list — the expensive call
    "transcript_cache": 30 * 24 * 3600,  # a video's content does not change
    "thumbnail_cache": 30 * 24 * 3600,
    "keywords": 7 * 24 * 3600,           # autocomplete: drifts slowly
}
TTL_DEFAULT = 6 * 3600


def _path(family: str, key: str) -> Path:
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return CACHE_DIR / family / f"{h}.json"


def read(family: str, key: str):
    """Return the cached value, or None if it is missing or expired."""
    path = _path(family, key)
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if age > TTL.get(family, TTL_DEFAULT):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)["value"]
    except Exception:  # noqa: BLE001 — a corrupt cache must not break the tool
        return None


def write(family: str, key: str, value) -> None:
    path = _path(family, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"key": key, "value": value}, f, ensure_ascii=False, default=str)


def memo(family: str, key: str, fn, use_cache: bool = True):
    """Return (value, cache_hit). Runs `fn` only when needed."""
    if use_cache:
        cached = read(family, key)
        if cached is not None:
            return cached, True
    value = fn()
    write(family, key, value)
    return value, False


def status() -> dict:
    """Summary for `tools/init.py`."""
    if not CACHE_DIR.exists():
        return {"entries": 0, "families": {}}
    families = {}
    total = 0
    for sub in sorted(CACHE_DIR.iterdir()):
        if sub.is_dir():
            n = len(list(sub.glob("*.json")))
            if n:
                families[sub.name] = n
                total += n
    return {"entries": total, "families": families}
