#!/usr/bin/env python3
"""Traffic sources for your own channel, with readable labels."""
from lib import base  # noqa: F401
from lib import cache
from lib import yt_analytics as ya
from lib.contract import SOURCE_API, emit, main, parser, envelope

TOOL = "yt_traffic"

# The raw API returns codes like SHORTS, HASHTAGS and YT_CHANNEL, which are
# unreadable in a report. This maps them to plain labels.
LABELS = {
    "SUBSCRIBER": "Subscribers (feed/bell)",
    "YT_SEARCH": "YouTube search",
    "RELATED_VIDEO": "Suggested videos",
    "EXT_URL": "External websites",
    "CHANNEL": "Channel page",
    "YT_CHANNEL": "Channel page",
    "NO_LINK_OTHER": "Direct / unknown",
    "NO_LINK_EMBEDDED": "Embedded player",
    "NOTIFICATION": "Notifications",
    "PLAYLIST": "Playlists",
    "YT_PLAYLIST_PAGE": "Playlist page",
    "END_SCREEN": "End screen",
    "ADVERTISING": "Advertising",
    "SHORTS": "Shorts feed",
    "SHORTS_CONTENT_LINKS": "Links from Shorts",
    "ANNOTATION": "Annotations / cards",
    "HASHTAGS": "Hashtags",
    "YT_OTHER_PAGE": "Other YouTube pages",
    "SOUND_PAGE": "Sound page",
    "VIDEO_REMIXES": "Remixes",
    "LIVE_REDIRECT": "Live redirect",
    "PRODUCT_PAGE": "Product page",
    "IMMERSIVE": "Immersive format",
}


def run():
    p = parser(__doc__)
    p.add_argument("--days", type=int, default=28)
    args = p.parse_args()

    payload_data, hit = cache.memo("own_analytics", f"{TOOL}:{args.days}",
                            lambda: ya.traffic(args.days), not args.no_cache)
    total = sum(d["views"] for d in payload_data) or 1
    for d in payload_data:
        crudo = d["insightTrafficSourceType"]
        d["fuente"] = LABELS.get(crudo, crudo)
        d["pct"] = round(d["views"] / total * 100, 1)

    env = envelope(TOOL, SOURCE_API, payload_data, {"days": args.days}, hit,
                notes=["`pct` is computed over the total (source: derived)."])
    emit(env, args, lambda e: base.md_header(e) + "\n" + base.md_table(
        e["data"], ["fuente", "views", "pct", "estimatedMinutesWatched"]))


if __name__ == "__main__":
    main(TOOL, run)
