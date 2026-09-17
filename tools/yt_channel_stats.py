#!/usr/bin/env python3
"""Stats for a channel. Without --channel, your own."""
from lib import base  # noqa: F401  (sys.path bootstrap)
from lib import cache, yt_data
from lib.contract import SOURCE_API, emit, main, parser, envelope

TOOL = "yt_channel_stats"


def run():
    p = parser(__doc__)
    p.add_argument("--channel", help="channel_id; omit for your own channel")
    args = p.parse_args()

    own = args.channel is None
    family = "own_analytics" if own else "other_channel"
    payload_data, hit = cache.memo(
        family, f"{TOOL}:{args.channel or 'mine'}",
        lambda: yt_data.channel_info(args.channel), not args.no_cache)

    env = envelope(TOOL, SOURCE_API, payload_data, {"channel": args.channel or "mine"}, hit)
    emit(env, args, lambda e: base.md_header(e) + "\n" + base.md_table(
        [{"field": k, "value": v} for k, v in e["data"].items()]))


if __name__ == "__main__":
    main(TOOL, run)
