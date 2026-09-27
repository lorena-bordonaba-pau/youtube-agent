#!/usr/bin/env python3
"""TAM and expected views for a video topic, from the competitor board's data.

For each topic (a regex over titles) it measures, over the board's 6-month
window: how many videos and channels covered it, the views it moved (the
topic's TAM proxy), and how far above their own channel's median those videos
landed. Then it projects that multiplier onto YOUR channel's median to give a
floor, an expected and a ceiling. No API calls: run competitor_board.py first.
"""
from lib import base  # noqa: F401
from lib import yt_data
import json
import re
import statistics
from pathlib import Path

from lib.contract import (DATA_DIR, EXIT_NO_DATA, EXIT_USAGE, SOURCE_HEURISTIC,
                          ToolError, emit, envelope, main, parser)

TOOL = "topic_tam"
BOARD = DATA_DIR / "reports" / "competitor_board"

# How much a view in a bigger foreign market is worth in yours: views abroad
# are not reachable as-is. 1.0 means no penalty. Measure your own over time and
# set it as `discovery.market_factor` in config/config.json; --market-factor
# overrides it for one run.
MARKET_FACTOR = 1.0

# Rough language call on a title, per language: accents and function words.
# Good enough to split a market, not to label a video. A language missing here
# cannot be split, and every video counts as home.
_WORDS = {
    "es": r"[ñáéíóú¿¡]|\b(de|que|con|para|tu|tus|cómo|como|el|la|los|las|y|en|por|sin|mi)\b",
    "pt": r"[ãõçáéíóúâê]|\b(de|que|com|para|seu|sua|como|o|os|as|e|em|por|sem|meu|não)\b",
    "fr": r"[àâçéèêëîïôûù]|\b(de|que|avec|pour|ton|ta|tes|comment|le|la|les|et|en|par|sans|mon)\b",
    "de": r"[äöüß]|\b(der|die|das|und|mit|für|dein|deine|wie|ein|eine|ohne|mein|nicht)\b",
    "it": r"[àèéìòù]|\b(di|che|con|per|tuo|tua|come|il|lo|la|gli|le|e|in|senza|mio)\b",
}


def is_home(title: str, language: str | None) -> bool:
    """Is this title in the creator's language? English is the fallback market:
    for an English channel, or a language not listed, everything is home."""
    pattern = _WORDS.get((language or "en")[:2])
    if pattern is None:
        return True
    return len(re.findall(pattern, title, re.I)) >= 2


def _pct(values: list[float], q: float) -> float:
    if not values:
        return 0
    s = sorted(values)
    k = (len(s) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def matches(title: str, pattern: str) -> bool:
    """`a && b` means both regexes must match."""
    return all(re.search(p.strip(), title, re.I) for p in pattern.split("&&"))


def measure(videos: list[dict], pattern: str, own_median: float,
            market_factor: float, own_videos: list[dict] | None = None,
            language: str | None = "es") -> dict:
    hits = [v for v in videos if matches(v["title"], pattern)]
    ratios = [v["ratio"] for v in hits if v.get("ratio")]
    home = [v for v in hits if is_home(v["title"], language)]
    foreign = [v for v in hits if not is_home(v["title"], language)]
    home_views = sum(v["views"] for v in home)
    foreign_views = sum(v["views"] for v in foreign)
    out = {
        "videos": len(hits),
        "channels": len({v["ch"] for v in hits}),
        "videos_home": len(home),
        # TAM proxy: what the topic moved in 6 months, foreign views scaled
        # down to the creator's market.
        "tam_views_6m": int(home_views + foreign_views / market_factor),
        "views_home_6m": home_views,
        "views_foreign_6m": foreign_views,
        "median_views": int(statistics.median([v["views"] for v in hits])) if hits else 0,
        "median_ratio": round(statistics.median(ratios), 2) if ratios else None,
        "share_2x": round(sum(r >= 2 for r in ratios) / len(ratios), 2) if ratios else None,
        "top": [{"title": v["title"], "video_id": v["id"], "ratio": v["ratio"],
                 "views": v["views"]}
                for v in sorted(hits, key=lambda v: -(v.get("ratio") or 0))[:3]],
    }
    # Your own track record on the topic beats any market projection.
    mine = [v for v in (own_videos or []) if matches(v["title"], pattern)]
    out["own"] = {
        "videos": len(mine),
        "median_views": int(statistics.median([v["views"] for v in mine])) if mine else None,
        "best": max(({"title": v["title"], "video_id": v["id"], "views": v["views"]}
                     for v in mine), key=lambda x: x["views"], default=None),
    }
    if len(ratios) >= 5 and own_median:
        out["expected"] = {
            "floor": int(own_median * _pct(ratios, 0.25)),
            "mid": int(own_median * statistics.median(ratios)),
            "ceiling": int(own_median * _pct(ratios, 0.9)),
        }
    else:
        out["expected"] = None
    return out


def run():
    p = parser(__doc__)
    p.add_argument("--topic", action="append", required=True,
                   help='"Name::regex" (repeatable). Join regexes with && to '
                        'require all of them, e.g. "Hermes::hermes && agent"')
    p.add_argument("--market-factor", type=float,
                   help="overrides `discovery.market_factor` in config.json")
    p.add_argument("--board", default=str(BOARD))
    args = p.parse_args()

    cfg = yt_data.load_config()
    language = cfg.get("language")
    factor = args.market_factor or (cfg.get("discovery") or {}).get(
        "market_factor") or MARKET_FACTOR

    board = Path(args.board)
    if not (board / "index.json").exists():
        raise ToolError("No competitor board data.", EXIT_NO_DATA,
                        "Run tools/competitor_board.py first.")
    index = json.loads((board / "index.json").read_text())
    own = next((c for c in index["channels"] if c.get("own") and not c.get("error")), None)
    videos, own_videos = [], []
    for f in (board / "ch").glob("*.json"):
        for v in json.loads(f.read_text()):
            if own and v["ch"] == own["key"]:
                own_videos.append(v)
            elif not v.get("ad_suspect"):
                videos.append(v)

    topics = []
    for t in args.topic:
        if "::" not in t:
            raise ToolError(f"Bad --topic {t!r}.", EXIT_USAGE, 'Use "Name::regex".')
        name, pattern = t.split("::", 1)
        topics.append({"topic": name.strip(), "pattern": pattern.strip(),
                       **measure(videos, pattern, own["median_views"] if own else 0,
                                 factor, own_videos, language)})

    env = envelope(TOOL, SOURCE_HEURISTIC, {
        "board_generated_at": index["generated_at"],
        "window_days": index["window_days"],
        "own_median_views": own["median_views"] if own else None,
        "topics": topics,
    }, {"market_factor": factor, "language": language}, notes=[
        "`tam_views_6m` = views the topic moved in the window across the board's "
        "channels, foreign-language views divided by the market factor. A proxy "
        "of market size within the channels you track, not of all YouTube.",
        "`expected` = your channel's median × the topic's 25th / 50th / 90th "
        "percentile ratio. It assumes your channel responds to the topic like the "
        "average tracked channel: an ESTIMATE, not a prediction. Declare it so.",
        "The language split is a heuristic on the title's words.",
        "Fewer than 5 videos on the topic: no projection (not enough to say).",
        "`own` = your videos on the topic in the same window. When you have them, "
        "they beat the market projection: quote both.",
    ])

    def md(e):
        d = e["data"]
        rows = []
        for t in d["topics"]:
            x = t["expected"] or {}
            rows.append({"topic": t["topic"], "videos": t["videos"],
                         "channels": t["channels"], "home": t["videos_home"],
                         "tam_views_6m": t["tam_views_6m"],
                         "median_ratio": t["median_ratio"], "share_2x": t["share_2x"],
                         "floor": x.get("floor"), "mid": x.get("mid"),
                         "ceiling": x.get("ceiling"), "own_n": t["own"]["videos"],
                         "own_median": t["own"]["median_views"]})
        return "\n".join([base.md_header(e),
                          f"\nYour median: **{d['own_median_views']}** views\n",
                          base.md_table(rows)])

    emit(env, args, md)


if __name__ == "__main__":
    main(TOOL, run)
