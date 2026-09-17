#!/usr/bin/env python3
"""Download a channel's avatar and banner and measure their pixels.

This is the step before generating new packaging: without seeing the current
brand, whatever gets generated will be generic or will break an identity that
already works.

The metrics are objective. Reading the brand — what it conveys, what fails —
is done by the agent opening the files with vision.
"""
from pathlib import Path

from lib import auth, base  # noqa: F401
from lib import cache
from lib.contract import (DATA_DIR, EXIT_NO_DATA, SOURCE_DERIVED, ToolError,
                          emit, main, parser, envelope)
from lib.imagegen import download
from yt_thumbnails import metrics

TOOL = "view_channel_packaging"
DIR = DATA_DIR / "packaging"


def paquete(channel_id: str | None) -> dict:
    yt = auth.youtube()
    parts = "snippet,brandingSettings"
    req = (yt.channels().list(part=parts, mine=True) if channel_id is None
           else yt.channels().list(part=parts, id=channel_id))
    items = req.execute().get("items", [])
    if not items:
        raise ToolError(f"Canal no encontrado: {channel_id or 'own'}", EXIT_NO_DATA)
    c = items[0]
    thumbs = c["snippet"].get("thumbnails", {})
    best = thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}
    return {
        "channel_id": c["id"],
        "title": c["snippet"]["title"],
        "avatar_url": best.get("url"),
        "banner_url": (c.get("brandingSettings", {})
                       .get("image", {}).get("bannerExternalUrl")),
        "keywords": c.get("brandingSettings", {}).get("channel", {}).get("keywords"),
    }


def run():
    p = parser(__doc__)
    p.add_argument("--channel", help="channel_id; omit for your own channel")
    p.add_argument("--only", choices=["avatar", "banner", "both"], default="both")
    args = p.parse_args()

    own = args.channel is None
    family = "own_analytics" if own else "other_channel"
    info, hit = cache.memo(family, f"{TOOL}:{args.channel or 'mine'}",
                           lambda: paquete(args.channel), not args.no_cache)

    DIR.mkdir(parents=True, exist_ok=True)
    cid = info["channel_id"]
    pieces = []
    target = {"avatar": ["avatar"], "banner": ["banner"],
                "both": ["avatar", "banner"]}[args.only]

    for piece in target:
        url = info.get(f"{piece}_url")
        if not url:
            pieces.append({"piece": piece, "status": "the channel has none"})
            continue
        # The banner is served cropped by default; =w2560 asks for the original.
        if piece == "banner":
            url = f"{url}=w2560-fcrop64=1,00000000ffffffff-k-c0xffffffff-no-nd-rj"
        dest = DIR / f"{cid}_{piece}.jpg"
        try:
            if not dest.exists():
                download(url, dest)
            pieces.append({"piece": piece, "status": "ok", **metrics(dest)})
        except Exception as e:  # noqa: BLE001 — one broken piece must not take down the other
            pieces.append({"piece": piece, "status": f"no descargada: {e}"})

    env = envelope(TOOL, SOURCE_DERIVED,
                {**info, "pieces": pieces}, {"channel": args.channel or "mine"}, hit,
                notes=[
                    "Pixel metrics, not a brand judgement.",
                    "To read the visual identity, OPEN the paths in `file` with the "
                    "image reading tool.",
                    "Judge the banner by its centre band: on mobile the top and "
                    "bottom thirds are cropped away.",
                ])
    emit(env, args, lambda e: base.md_header(e) +
           f"\n\n**{e['data']['title']}** — `{e['data']['channel_id']}`\n\n" +
           base.md_table(e["data"]["pieces"],
                         ["piece", "status", "resolution", "global_contrast",
                          "mean_saturation", "file"]))


if __name__ == "__main__":
    main(TOOL, run)
