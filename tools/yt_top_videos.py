#!/usr/bin/env python3
"""Your videos ranked by views, with real mean retention."""
from lib import base  # noqa: F401
from lib import cache, yt_data
from lib import yt_analytics as ya
from lib.contract import SOURCE_API, emit, main, parser, envelope

TOOL = "yt_top_videos"


def run():
    p = parser(__doc__)
    p.add_argument("--days", type=int, default=90)
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--by-retention", action="store_true",
                   help="rank by averageViewPercentage instead of views")
    args = p.parse_args()

    def fetch():
        rows = ya.top_videos(args.days, args.limit)
        titulos = {s["video_id"]: s["title"]
                   for s in yt_data.video_stats([f["video"] for f in rows])}
        for f in rows:
            f["title"] = titulos.get(f["video"], "?")
        return rows

    payload_data, hit = cache.memo("own_analytics", f"{TOOL}:{args.days}:{args.limit}",
                            fetch, not args.no_cache)
    if args.by_retention:
        payload_data = sorted(payload_data, key=lambda d: d.get("averageViewPercentage", 0), reverse=True)

    env = envelope(TOOL, SOURCE_API, payload_data,
                {"days": args.days, "limit": args.limit,
                 "order": "retention" if args.by_retention else "views"}, hit)
    emit(env, args, lambda e: base.md_header(e) + "\n" + base.md_table(
        e["data"], ["video", "title", "views", "averageViewPercentage",
                    "averageViewDuration", "subscribersGained"]))


if __name__ == "__main__":
    main(TOOL, run)
