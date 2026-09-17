#!/usr/bin/env python3
"""Public stats for one or more videos (any channel)."""
from lib import base  # noqa: F401
from lib import cache, yt_data
from lib.contract import SOURCE_API, emit, main, parser, envelope

TOOL = "yt_video_stats"


def run():
    p = parser(__doc__)
    p.add_argument("--video", required=True, help="video_id, or several separated by commas")
    args = p.parse_args()

    ids = [v.strip() for v in args.video.split(",") if v.strip()]
    payload_data, hit = cache.memo("other_channel", f"{TOOL}:{','.join(sorted(ids))}",
                            lambda: yt_data.video_stats(ids), not args.no_cache)
    env = envelope(TOOL, SOURCE_API, payload_data, {"video": ids}, hit)
    emit(env, args, lambda e: base.md_header(e) + "\n" + base.md_table(
        e["data"], ["video_id", "title", "views", "likes", "comments", "duration"]))


if __name__ == "__main__":
    main(TOOL, run)
