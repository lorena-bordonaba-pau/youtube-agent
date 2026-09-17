#!/usr/bin/env python3
"""Day-by-day evolution of one of your videos."""
from lib import base  # noqa: F401
from lib import cache
from lib import yt_analytics as ya
from lib.contract import SOURCE_API, emit, main, parser, envelope

TOOL = "yt_video_analytics"


def run():
    p = parser(__doc__)
    p.add_argument("--video", required=True)
    p.add_argument("--days", type=int, default=90)
    args = p.parse_args()

    payload_data, hit = cache.memo("own_analytics", f"{TOOL}:{args.video}:{args.days}",
                            lambda: ya.video(args.video, args.days), not args.no_cache)
    env = envelope(TOOL, SOURCE_API, payload_data, {"video": args.video, "days": args.days}, hit)
    emit(env, args, lambda e: base.md_header(e) + "\n" + base.md_table(e["data"]))


if __name__ == "__main__":
    main(TOOL, run)
