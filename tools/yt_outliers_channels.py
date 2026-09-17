#!/usr/bin/env python3
"""Outliers across the configured competitor and inspiration channels."""
from lib import base  # noqa: F401
from lib import cache, yt_data
from lib.contract import (EXIT_NO_DATA, SOURCE_DERIVED, ToolError, emit, main,
                          parser, envelope)

TOOL = "yt_outliers_channels"


def _dias(iso: str) -> int:
    from datetime import datetime, timezone
    return (datetime.now(timezone.utc)
            - datetime.fromisoformat(iso.replace("Z", "+00:00"))).days


def analizar(entry: dict, min_ratio: float, sample_size: int) -> dict:
    info = yt_data.channel_info(entry["channel_id"])
    vids = yt_data.channel_videos(entry["channel_id"], sample_size)
    stats = yt_data.video_stats([v["video_id"] for v in vids])
    if not stats:
        return {**entry, "subs": info["subscribers"], "mean": 0, "outliers": []}
    mean = sum(s["views"] for s in stats) / len(stats)
    outliers = []
    for s in stats:
        ratio = round(s["views"] / mean, 2) if mean else 0
        if ratio >= min_ratio:
            days = _dias(s["published_at"])
            outliers.append({
                "title": s["title"], "video_id": s["video_id"], "views": s["views"],
                "ratio": ratio, "engagement_rate": s["engagement_rate"],
                "duration": s["duration"], "published_at": s["published_at"],
                "days": days,
                # A year-old outlier is not an opportunity: it is history.
                "freshness": ("caliente" if days <= 30 else "tibio" if days <= 90
                             else "frio"),
                "description_preview": (s["description"] or "")[:200],
            })
    return {
        **entry, "subs": info["subscribers"], "mean": int(mean),
        "outliers": sorted(outliers, key=lambda o: o["ratio"], reverse=True),
    }


def run():
    p = parser(__doc__)
    p.add_argument("--min-ratio", type=float, default=2.0)
    p.add_argument("--sample", type=int, default=30)
    p.add_argument("--max-days", type=int, default=90,
                   help="drop outliers older than N days (default 90). "
                        "Use 9999 to disable the filter.")
    p.add_argument("--list", dest="items",
                   help="name of a list in config/channels_lists.json "
                        "(competitors, inspiration, neighbourhood...)")
    args = p.parse_args()

    channels = yt_data.load_channels(args.items)
    if not channels:
        which = f"`{args.items}`" if args.items else "any list"
        raise ToolError(
            f"No channels configured in {which}.", EXIT_NO_DATA,
            "Add competitors, inspirations and neighbours to "
            "config/channels_lists.json, or ask the agent to propose them "
            "after analysing your channel. Zero outliers here means zero "
            "channels to look at, not a quiet niche.")

    def fetch():
        return [analizar(c, args.min_ratio, args.sample) for c in channels]

    def filtrar_por_edad(payload_data):
        for c in payload_data:
            c["outliers"] = [o for o in c["outliers"]
                             if o.get("days", 0) <= args.max_days]
        return payload_data

    key = f"{TOOL}:{args.items or 'todas'}:{args.min_ratio}:{args.sample}"
    payload_data, hit = cache.memo("other_channel", key, fetch, not args.no_cache)
    payload_data = filtrar_por_edad(payload_data)

    total = sum(len(c["outliers"]) for c in payload_data)
    env = envelope(TOOL, SOURCE_DERIVED,
                {"channels": payload_data, "total_outliers": total},
                {"list": args.items or "todas", "min_ratio": args.min_ratio,
                 "sample": args.sample}, hit,
                notes=["`ratio` = views / mean of THAT channel's last N uploads.",
                       f"Filtrado a outliers de <= {args.max_days} days. Un outlier "
                       "An old one is not an opportunity, it is history.",
                       "Comparing views across lists in different languages is NOT "
                       "direct: adjust for market size."])

    def md(e):
        out = [base.md_header(e), f"\n**{e['data']['total_outliers']} outliers** "
               f"(threshold {args.min_ratio}x, sampling {args.sample} videos/channel)\n"]
        for c in e["data"]["channels"]:
            if not c["outliers"]:
                continue
            out.append(f"\n### {c['list_type'].upper()} — {c['name']} "
                       f"({yt_data.fmt(c['subs'])} subs, mean {yt_data.fmt(c['mean'])})\n")
            out.append(base.md_table(c["outliers"],
                                     ["title", "views", "ratio", "days", "freshness",
                                      "engagement_rate", "duration"]))
        return "\n".join(out)

    emit(env, args, md)


if __name__ == "__main__":
    main(TOOL, run)
