#!/usr/bin/env python3
"""Audience by country."""
from lib import base  # noqa: F401
from lib import cache
from lib import yt_analytics as ya
from lib.contract import SOURCE_API, emit, main, parser, envelope

TOOL = "yt_geography"


def run():
    p = parser(__doc__)
    p.add_argument("--days", type=int, default=90)
    p.add_argument("--limit", type=int, default=20)
    args = p.parse_args()

    payload_data, hit = cache.memo("own_analytics", f"{TOOL}:{args.days}:{args.limit}",
                            lambda: ya.geography(args.days, args.limit), not args.no_cache)
    env = envelope(TOOL, SOURCE_API, payload_data, {"days": args.days, "limit": args.limit}, hit,
                notes=["`viewsPercent` is computed (source: derived)."])
    emit(env, args, lambda e: base.md_header(e) + "\n" + base.md_table(e["data"]))


if __name__ == "__main__":
    main(TOOL, run)
