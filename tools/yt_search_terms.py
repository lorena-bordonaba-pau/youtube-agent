#!/usr/bin/env python3
"""The REAL search terms bringing traffic to the channel.

Not an estimate: these are the queries people actually arrived through.
With --type RELATED_VIDEO, which specific videos are suggesting yours.
"""
from lib import base  # noqa: F401
from lib import cache, yt_data
from lib import yt_analytics as ya
from lib.contract import SOURCE_API, emit, main, parser, envelope

TOOL = "yt_search_terms"


def run():
    p = parser(__doc__)
    p.add_argument("--days", type=int, default=90)
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--type", dest="kind", default="YT_SEARCH",
                   choices=["YT_SEARCH", "RELATED_VIDEO", "EXT_URL", "SUBSCRIBER"])
    p.add_argument("--video", help="limit to one specific video")
    args = p.parse_args()

    key = f"{TOOL}:{args.kind}:{args.days}:{args.limit}:{args.video}"
    payload_data, hit = cache.memo(
        "own_analytics", key,
        lambda: ya.traffic_detail(args.days, args.kind, args.limit, args.video),
        not args.no_cache)

    total = sum(d["views"] for d in payload_data) or 1
    for d in payload_data:
        d["termino"] = d.pop("insightTrafficSourceDetail")
        d["pct"] = round(d["views"] / total * 100, 1)

    # With RELATED_VIDEO the "term" is a video_id: resolving its title helps.
    if args.kind == "RELATED_VIDEO" and payload_data:
        titulos = {s["video_id"]: f"{s['channel_title']} — {s['title']}"
                   for s in yt_data.video_stats([d["termino"] for d in payload_data])}
        for d in payload_data:
            d["title"] = titulos.get(d["termino"], "?")

    env = envelope(TOOL, SOURCE_API, payload_data,
                {"kind": args.kind, "days": args.days, "video": args.video}, hit,
                notes=["These are REAL traffic terms, not estimated search "
                       "volume. Only terms above YouTube's privacy threshold appear."
                       "privacidad de YouTube."])
    cols = (["termino", "title", "views", "pct"] if args.kind == "RELATED_VIDEO"
            else ["termino", "views", "pct", "estimatedMinutesWatched"])
    emit(env, args, lambda e: base.md_header(e) + "\n" + base.md_table(e["data"], cols))


if __name__ == "__main__":
    main(TOOL, run)
