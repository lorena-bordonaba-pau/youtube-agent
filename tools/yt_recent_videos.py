#!/usr/bin/env python3
"""Recent videos from a channel, with public stats."""
from lib import base  # noqa: F401
from lib import cache, yt_data
from lib.contract import SOURCE_API, emit, main, parser, envelope

TOOL = "yt_recent_videos"


def run():
    p = parser(__doc__)
    p.add_argument("--channel", help="channel_id; omit for your own channel")
    p.add_argument("--limit", type=int, default=15)
    p.add_argument("--stats", action="store_true", help="include views/likes")
    args = p.parse_args()

    family = "own_analytics" if args.channel is None else "other_channel"
    key = f"{TOOL}:{args.channel or 'mine'}:{args.limit}:{args.stats}"

    def fetch():
        vids = yt_data.channel_videos(args.channel, args.limit)
        if not args.stats:
            return vids
        stats = {s["video_id"]: s for s in
                 yt_data.video_stats([v["video_id"] for v in vids])}
        return [{**v, **stats.get(v["video_id"], {})} for v in vids]

    payload_data, hit = cache.memo(family, key, fetch, not args.no_cache)
    env = envelope(TOOL, SOURCE_API, payload_data,
                {"channel": args.channel or "mine", "limit": args.limit}, hit)
    cols = ["video_id", "title", "published_at"] + (["views", "likes"] if args.stats else [])
    emit(env, args, lambda e: base.md_header(e) + "\n" + base.md_table(e["data"], cols))


if __name__ == "__main__":
    main(TOOL, run)
