#!/usr/bin/env python3
"""The configured lists of competitor and inspiration channels.

With --add / --remove it also edits config/channels_lists.json. Only run those
after the creator has said yes to that specific channel: the lists are their
judgement, not the agent's.
"""
import json

from lib import base  # noqa: F401
from lib import discovery, yt_data
from lib.contract import (CONFIG_DIR, EXIT_NO_DATA, EXIT_USAGE, SOURCE_CONFIG,
                          ToolError, emit, envelope, main, parser)

TOOL = "yt_channels_list"
PATH = CONFIG_DIR / "channels_lists.json"


def _edit(args) -> dict:
    cfg = json.loads(PATH.read_text(encoding="utf-8"))
    if args.add:
        if not args.to:
            raise ToolError("--add needs --to LIST", EXIT_USAGE,
                            "competitors, inspiration or neighbourhood")
        cfg = discovery.add_channel(cfg, args.to, {
            "channel_id": args.add, "name": args.name or "",
            "notes": args.notes or "", "origin": args.origin})
        change = {"added": args.add, "to": args.to}
    else:
        def count(c):
            return sum(len(v) for k, v in c.items() if not k.startswith("_"))
        before = count(cfg)
        cfg = discovery.remove_channel(cfg, args.remove)
        if count(cfg) == before:
            raise ToolError(f"{args.remove} is not in any list.", EXIT_NO_DATA)
        change = {"removed": args.remove}
    PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return change


def run():
    p = parser(__doc__)
    p.add_argument("--list", dest="items",
                   help="name of a list in config/channels_lists.json "
                        "(competitors, inspiration, neighbourhood...)")
    p.add_argument("--add", metavar="CHANNEL_ID", help="add (or move) a channel")
    p.add_argument("--to", help="list to add it to")
    p.add_argument("--name", help="channel name, for the list")
    p.add_argument("--notes", help="why it is in the list")
    p.add_argument("--origin", default="discovered",
                   help="curated | discovered | related_video")
    p.add_argument("--remove", metavar="CHANNEL_ID")
    args = p.parse_args()

    params = {"list": args.items or "all"}
    if args.add or args.remove:
        params["change"] = _edit(args)

    payload_data = yt_data.load_channels(args.items)
    env = envelope(TOOL, SOURCE_CONFIG, payload_data, params)
    emit(env, args, lambda e: base.md_header(e) + "\n" + base.md_table(
        e["data"], ["list_type", "name", "channel_id", "notes"]))


if __name__ == "__main__":
    main(TOOL, run)
