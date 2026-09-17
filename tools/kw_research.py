#!/usr/bin/env python3
"""Keyword research by PROXY. It does not give real search volume.

YouTube does not publish search volume for free. This combines three signals:
  1. DEMAND      — YouTube autocomplete: how many variants it suggests and
                   how early the keyword appears.
  2. COMPETITION — search.list: median views at the top, age, and the size of
                   the channels ranking there.
  3. FIELD       — cross-check with yt_search_terms: if a term already brings
                   you REAL traffic, that beats any estimate.

The result is a RELATIVE RANKING among the keywords compared, marked as
`heuristic`. It must never be presented as search volume.
"""
import json
import statistics
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from lib import base  # noqa: F401
from lib import cache, yt_data
from lib.contract import SOURCE_HEURISTIC, emit, main, parser, envelope

# Language/region for autocomplete and transcription. Set `language` and
# `region` in config/config.json; they default to English.
def _locale():
    try:
        import json as _j
        c = _j.loads((CONFIG_DIR / "config.json").read_text(encoding="utf-8"))
        return c.get("language", "en"), c.get("region", "us")
    except Exception:  # noqa: BLE001 — a missing config must not break the tool
        return "en", "us"


LANG, REGION = _locale()

TOOL = "kw_research"
ABC = "abcdefghijklmnopqrstuvwxyz"


def suggestions(q: str, hl: str = LANG, gl: str = REGION) -> list[str]:
    url = ("https://suggestqueries.google.com/complete/search"
           f"?client=firefox&ds=yt&hl={hl}&gl={gl}&q={urllib.parse.quote(q)}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))[1]
    except Exception:  # noqa: BLE001 — without suggestions, carry on with the other signalses
        return []


def demanda(kw: str, deep: bool) -> dict:
    """Demand signal: the variants YouTube suggests for the keyword."""
    base_sug = suggestions(kw)
    todas = list(base_sug)
    if deep:
        for letra in ABC:
            todas.extend(suggestions(f"{kw} {letra}"))
    unicas = sorted({s for s in todas if kw.lower() in s.lower()})
    # The exact keyword coming back first signals genuine search intent.
    exacta = bool(base_sug) and base_sug[0].strip().lower() == kw.strip().lower()
    return {
        "variants": len(unicas),
        "suggestions": unicas[:40],
        "is_exact_suggestion": exacta,
        "demand_score": min(100, round(len(unicas) * 2.5 + (20 if exacta else 0))),
    }


def competitors(kw: str, use_cache: bool) -> dict:
    """Competition signal: how hard the top of the results is."""
    payload_data, _ = cache.memo(
        "search_query", f"{TOOL}:comp:{kw}",
        lambda: yt_data.search(kw, 10, duration="any"), use_cache)
    if not payload_data:
        return {"results": 0, "competition_score": 0, "median_views": 0}

    views = [d["views"] for d in payload_data]
    median = statistics.median(views)
    ahora = datetime.now(timezone.utc)
    antiguedades = []
    for d in payload_data:
        try:
            pub = datetime.fromisoformat(d["published_at"].replace("Z", "+00:00"))
            antiguedades.append((ahora - pub).days)
        except Exception:  # noqa: BLE001
            pass
    median_age_days = statistics.median(antiguedades) if antiguedades else 0

    # High median views = hard. Old results = a gap worth refreshing.
    dureza = min(100, median / 1000)
    freshness = max(0, 40 - median_age_days / 18)  # older than ~2 years ⇒ 0
    return {
        "results": len(payload_data),
        "median_views": int(median),
        "max_views": max(views),
        "median_age_days": int(median_age_days),
        "top3": [{"title": d["title"], "channel_title": d["channel_title"],
                  "views": d["views"], "published_at": d["published_at"]}
                 for d in sorted(payload_data, key=lambda x: x["views"], reverse=True)[:3]],
        "competition_score": round(dureza),
        "age_gap_bonus": round(freshness),
    }


def run():
    p = parser(__doc__)
    p.add_argument("--kw", required=True, help="keyword, or several separated by ';'")
    p.add_argument("--deep", action="store_true",
                   help="expand with the alphabet (26 more autocomplete calls)")
    p.add_argument("--no-competition", action="store_true",
                   help="skip search.list and save 100 quota units per keyword")
    args = p.parse_args()

    keywords = [k.strip() for k in args.kw.split(";") if k.strip()]
    out = []
    for kw in keywords:
        d = demanda(kw, args.deep)
        c = ({} if args.no_competition
             else competitors(kw, not args.no_cache))
        # Opportunity = high demand, low competition, plus the age gap.
        oportunidad = (d["demand_score"] - c.get("competition_score", 0) * 0.6
                       + c.get("age_gap_bonus", 0))
        out.append({
            "keyword": kw,
            "opportunity_score": max(0, min(100, round(oportunidad))),
            **d, **c,
        })

    out.sort(key=lambda x: x["opportunity_score"], reverse=True)
    env = envelope(TOOL, SOURCE_HEURISTIC, out,
                {"kw": keywords, "deep": args.deep}, False,
                notes=[
                    "NOT search volume. It is a relative ranking among the keywords "
                    "compared within this same run.",
                    "Comparing two runs with different keywords is not valid.",
                    "For REAL, verified demand use `yt_search_terms.py`: those are "
                    "terms people actually reached the channel through.",
                ])
    emit(env, args, lambda e: base.md_header(e) + "\n" + base.md_table(
        e["data"], ["keyword", "opportunity_score", "demand_score", "variants",
                    "competition_score", "median_views", "median_age_days"]))


if __name__ == "__main__":
    main(TOOL, run)
