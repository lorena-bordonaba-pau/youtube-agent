#!/usr/bin/env python3
"""Audience demographics: age and gender."""
from lib import base  # noqa: F401
from lib import cache
from lib import yt_analytics as ya
from lib.contract import SOURCE_API, emit, main, parser, envelope

TOOL = "yt_demographics"


def run():
    p = parser(__doc__)
    p.add_argument("--days", type=int, default=90)
    args = p.parse_args()

    payload_data, hit = cache.memo("own_analytics", f"{TOOL}:{args.days}",
                            lambda: ya.demographics(args.days), not args.no_cache)
    by_gender = {}
    for d in payload_data:
        by_gender[d["gender"]] = round(
            by_gender.get(d["gender"], 0) + d["viewerPercentage"], 1)

    env = envelope(TOOL, SOURCE_API, {"detail": payload_data, "by_gender": by_gender},
                {"days": args.days}, hit)
    emit(env, args, lambda e: base.md_header(e) + "\n" + base.md_table(e["data"]["detail"]))


if __name__ == "__main__":
    main(TOOL, run)
