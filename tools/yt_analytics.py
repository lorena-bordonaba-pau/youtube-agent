#!/usr/bin/env python3
"""Daily analytics for your own channel: views, mean retention, subs, engagement."""
from lib import base  # noqa: F401
from lib import cache
from lib import yt_analytics as ya
from lib.contract import SOURCE_API, emit, main, parser, envelope

TOOL = "yt_analytics"


def run():
    p = parser(__doc__)
    p.add_argument("--days", type=int, default=28)
    args = p.parse_args()

    payload_data, hit = cache.memo("own_analytics", f"{TOOL}:{args.days}",
                            lambda: ya.channel(args.days), not args.no_cache)

    totals = {
        "views": sum(d["views"] for d in payload_data),
        "estimatedMinutesWatched": sum(d["estimatedMinutesWatched"] for d in payload_data),
        "subscribersNet": sum(d["subscribersGained"] - d["subscribersLost"] for d in payload_data),
        "likes": sum(d["likes"] for d in payload_data),
        "comments": sum(d["comments"] for d in payload_data),
    }
    env = envelope(TOOL, SOURCE_API, {"days": payload_data, "totals": totals},
                {"days": args.days}, hit,
                notes=["`totals` is a sum over API data (source: derived)."])
    emit(env, args, lambda e: base.md_header(e) + "\n" + base.md_table(e["data"]["days"]))


if __name__ == "__main__":
    main(TOOL, run)
