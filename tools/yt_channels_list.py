#!/usr/bin/env python3
"""The configured lists of competitor and inspiration channels."""
from lib import base  # noqa: F401
from lib import yt_data
from lib.contract import SOURCE_CONFIG, emit, main, parser, envelope

TOOL = "yt_channels_list"


def run():
    p = parser(__doc__)
    p.add_argument("--list", dest="items",
                   help="name of a list in config/channels_lists.json "
                        "(competitors, inspiration, neighbourhood...)")
    args = p.parse_args()

    payload_data = yt_data.load_channels(args.items)
    env = envelope(TOOL, SOURCE_CONFIG, payload_data, {"list": args.items or "todas"})
    emit(env, args, lambda e: base.md_header(e) + "\n" + base.md_table(
        e["data"], ["list_type", "name", "channel_id", "notes"]))


if __name__ == "__main__":
    main(TOOL, run)
