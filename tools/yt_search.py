#!/usr/bin/env python3
"""Search YouTube and flag outliers within the results.

COSTS 100 QUOTA UNITS per query (the daily quota is 10,000).
Always cached for 24h.
Here the query is an argument.
"""
import statistics

from lib import base  # noqa: F401
from lib import cache, yt_data
from lib.contract import SOURCE_DERIVED, emit, main, parser, envelope

TOOL = "yt_search"


def run():
    p = parser(__doc__)
    p.add_argument("--query", required=True, help="query, or several separated by ';'")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--duration", default="medium",
                   choices=["any", "short", "medium", "long"])
    p.add_argument("--days", type=int, help="limit to videos published in the last N days")
    args = p.parse_args()

    consultas = [q.strip() for q in args.query.split(";") if q.strip()]
    results, hits = [], []
    for q in consultas:
        key = f"{TOOL}:{q}:{args.limit}:{args.duration}:{args.days}"
        payload_data, hit = cache.memo(
            "search_query", key,
            lambda q=q: yt_data.search(q, args.limit, duration=args.duration,
                                       days=args.days),
            not args.no_cache)
        hits.append(hit)
        views = [d["views"] for d in payload_data] or [0]
        median = statistics.median(views)
        for d in payload_data:
            d["query"] = q
            d["ratio_vs_mediana"] = round(d["views"] / median, 2) if median else 0
        results.extend(payload_data)

    results.sort(key=lambda d: d["ratio_vs_mediana"], reverse=True)
    env = envelope(TOOL, SOURCE_DERIVED, results,
                {"query": consultas, "limit": args.limit, "duration": args.duration},
                all(hits),
                notes=["`ratio_vs_median` compares against the MEDIAN of that query's "
                       "results, not the source channel's mean.",
                       "Each uncached query costs 100 quota units."])
    emit(env, args, lambda e: base.md_header(e) + "\n" + base.md_table(
        e["data"], ["query", "title", "channel_title", "views", "ratio_vs_mediana",
                    "duration", "published_at"]))


if __name__ == "__main__":
    main(TOOL, run)
