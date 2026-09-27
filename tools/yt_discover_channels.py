#!/usr/bin/env python3
"""Discover candidate channels from search terms: who already wins with your audience.

For each term it searches recent long-form videos, keeps the ones clearing the
thresholds (views, age, duration, ratio against THEIR channel's own mean) and
groups them by channel. The result is a list of CANDIDATES for the creator to
validate one by one — nothing is written to config/channels_lists.json here.

COSTS 100 QUOTA UNITS per term (search.list), plus ~3 per new channel for its
mean. Everything is cached. Thresholds come from `discovery` in
config/config.json, and any flag overrides them.
"""
from lib import base  # noqa: F401
from lib import cache, discovery, yt_data
from lib.contract import (EXIT_NO_DATA, SOURCE_DERIVED, ToolError, emit, envelope,
                          main, parser)

TOOL = "yt_discover_channels"


def run():
    p = parser(__doc__)
    p.add_argument("--terms", required=True,
                   help="search terms separated by ';' — the niche plus the "
                        "adjacent interests of the audience")
    p.add_argument("--per-term", type=int, default=25,
                   help="results fetched per term (max 50, same cost)")
    p.add_argument("--min-ratio", type=float)
    p.add_argument("--min-views", type=int)
    p.add_argument("--max-days", type=int)
    p.add_argument("--min-duration-s", type=int)
    p.add_argument("--bias-language", action="store_true",
                   help="rank results toward config.json language/region. Off by "
                        "default: other markets are where untaken topics come from")
    args = p.parse_args()

    terms = [t.strip() for t in args.terms.split(";") if t.strip()]
    cfg = yt_data.load_config()
    th = discovery.thresholds(cfg, min_ratio=args.min_ratio,
                              min_views=args.min_views, max_days=args.max_days,
                              min_duration_s=args.min_duration_s)

    bias = bool(args.bias_language)
    videos, hits = [], []
    for term in terms:
        found, hit = cache.memo(
            "search_query",
            f"{TOOL}:{term}:{args.per_term}:{th['max_days']}:{bias}",
            lambda term=term: yt_data.search(
                term, min(args.per_term, 50), duration="any", days=th["max_days"],
                language=bias and cfg.get("language"),
                region=bias and cfg.get("region")),
            not args.no_cache)
        hits.append(hit)
        videos.extend({**v, "term": term} for v in found)

    # Only channels with a video that already clears views/age/duration are
    # worth the extra calls for their mean.
    means = {}
    for cid in {v["channel_id"] for v in videos if discovery.prefilter(v, th)}:
        means[cid], hit = cache.memo(
            "other_channel", f"channel_mean:{cid}",
            lambda cid=cid: yt_data.channel_mean_views(cid), not args.no_cache)
        hits.append(hit)

    try:
        existing = {c["channel_id"]: c["list_type"] for c in yt_data.load_channels()}
    except ToolError:
        existing = {}

    # Your own channel wins with your audience by definition; it is not a
    # candidate. Knowable only with OAuth — with just an API key it may show.
    try:
        own, _ = cache.memo("own_analytics", "own_channel_id",
                            lambda: yt_data.channel_info()["channel_id"],
                            not args.no_cache)
    except Exception:  # noqa: BLE001 — API-key mode has no "mine"
        own = None
    videos = [v for v in videos if v["channel_id"] != own]

    found = discovery.outliers(videos, means, th)
    channels = discovery.group_by_channel(found, existing)
    if not videos:
        raise ToolError("The searches returned no videos.", EXIT_NO_DATA,
                        "Check the terms are in the audience's language.")

    notes = [
        "`ratio` = views / mean of THAT channel's last 15 uploads.",
        "`not_solo` flags titles that look like a podcast, interview, live or "
        "clip. Flagged, not removed: the creator decides.",
        "`languages` is what uploaders declared (often empty). A channel in "
        f"another language than yours ({cfg.get('language')}) is an "
        "inspiration: the question is whether its topic exists in your market "
        "yet.",
        f"Cost: {100 * sum(1 for h in hits[:len(terms)] if not h)} units in "
        "searches plus channel means, cached from now on.",
    ]
    if len(channels) < 5:
        notes.append(
            f"Only {len(channels)} candidates. In a small or non-English niche "
            f"min_views={th['min_views']} is probably too high: lower it "
            "(`--min-views` or `discovery` in config.json) before concluding "
            "the market is empty.")

    env = envelope(TOOL, SOURCE_DERIVED,
                   {"thresholds": th, "terms": terms, "candidates": channels,
                    "outliers": sorted(found, key=lambda v: v["ratio"], reverse=True)},
                   {"terms": terms, "per_term": args.per_term}, all(hits), notes=notes)

    def md(e):
        rows = [{"name": c["name"], "channel_id": c["channel_id"],
                 "outliers": c["outliers"], "best_ratio": c["best"]["ratio"],
                 "best_video": c["best"]["title"][:60],
                 "languages": ",".join(c["languages"]),
                 "already_in": c["already_in"] or "",
                 "not_solo": "yes" if c["not_solo"] else ""}
                for c in e["data"]["candidates"]]
        return (base.md_header(e) + f"\n**{len(rows)} candidates** — thresholds "
                f"{th}\n\n" + base.md_table(rows, list(rows[0]) if rows else ["name"]))

    emit(env, args, md)


if __name__ == "__main__":
    main(TOOL, run)
