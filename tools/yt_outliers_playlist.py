#!/usr/bin/env python3
"""Outliers de tu playlist manual de guardados.

An outlier is a video whose views exceed N times its own channel's mean.
"""
from lib import base  # noqa: F401
from lib import cache, yt_data
from lib.contract import (EXIT_NO_DATA, SOURCE_DERIVED, ToolError, emit, main,
                          parser, envelope)

TOOL = "yt_outliers_playlist"


def run():
    p = parser(__doc__)
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--min-ratio", type=float, default=1.0)
    args = p.parse_args()

    cfg = yt_data.load_config()
    playlist = cfg.get("outlier_playlist_id", "")
    if not playlist or playlist.startswith("PL0000"):
        raise ToolError(
            "`outlier_playlist_id` is not set in config/config.json.",
            EXIT_NO_DATA,
            "Create a YouTube playlist where you save interesting videos "
            "and put its ID there.")

    def fetch():
        items = yt_data.playlist_items(playlist, args.days)
        if not items:
            return []
        stats = yt_data.video_stats([i["video_id"] for i in items])
        added = {i["video_id"]: i["added_at"] for i in items}
        medias: dict[str, float] = {}
        out = []
        for s in stats:
            cid = s["channel_id"]
            if cid not in medias:
                medias[cid] = yt_data.channel_mean_views(cid)
            mean = medias[cid]
            ratio = round(s["views"] / mean, 2) if mean else 0
            out.append({**s, "channel_mean": int(mean), "ratio": ratio,
                           "added_at": added.get(s["video_id"])})
        return sorted(out, key=lambda x: x["ratio"], reverse=True)

    payload_data, hit = cache.memo("other_channel", f"{TOOL}:{playlist}:{args.days}",
                            fetch, not args.no_cache)
    payload_data = [d for d in payload_data if d["ratio"] >= args.min_ratio]

    env = envelope(TOOL, SOURCE_DERIVED, payload_data,
                {"days": args.days, "min_ratio": args.min_ratio}, hit,
                notes=["`ratio` = views / mean of that channel's last 15 uploads.",
                       "`channel_context` vive en config/config.json."])
    emit(env, args, lambda e: base.md_header(e) + "\n" + base.md_table(
        e["data"], ["title", "channel_title", "views", "channel_mean", "ratio",
                    "engagement_rate", "duration"]))


if __name__ == "__main__":
    main(TOOL, run)
