#!/usr/bin/env python3
"""Full channel report, plus a snapshot appended to the history.

Every run appends a line to data/history/snapshots.jsonl, which is what
makes comparing across dates possible. Without that history, "is it going up?"
has no answer the tools can give.
"""
import json
from datetime import datetime
from pathlib import Path

from lib import base  # noqa: F401
from lib import cache, yt_data
from lib import yt_analytics as ya
from lib.contract import DATA_DIR, SOURCE_API, emit, main, parser, envelope
from yt_traffic import LABELS

TOOL = "yt_report"
SNAPSHOTS = DATA_DIR / "history" / "snapshots.jsonl"


def snapshot_previo() -> dict | None:
    if not SNAPSHOTS.exists():
        return None
    lines = [l for l in SNAPSHOTS.read_text(encoding="utf-8").splitlines() if l.strip()]
    return json.loads(lines[-1]) if lines else None


def run():
    p = parser(__doc__)
    p.add_argument("--days", type=int, default=28)
    p.add_argument("--top-days", type=int, default=90)
    p.add_argument("--no-snapshot", action="store_true",
                   help="do not append to the history")
    args = p.parse_args()

    use_cache = not args.no_cache

    def f(name, fn):
        return cache.memo("own_analytics", f"{TOOL}:{name}:{args.days}:{args.top_days}",
                          fn, use_cache)[0]

    info = f("info", lambda: yt_data.channel_info())
    days = f("days", lambda: ya.channel(args.days))
    top = f("top", lambda: ya.top_videos(args.top_days, 20))
    traffic = f("traffic", lambda: ya.traffic(args.days))
    demo = f("demo", lambda: ya.demographics(args.top_days))
    geo = f("geo", lambda: ya.geography(args.top_days, 10))

    titulos = {s["video_id"]: s["title"]
               for s in yt_data.video_stats([t["video_id"] for t in top])}
    for t in top:
        t["title"] = titulos.get(t["video_id"], "?")

    views = sum(d["views"] for d in days)
    minutes = sum(d["estimatedMinutesWatched"] for d in days)
    net_subs = sum(d["subscribersGained"] - d["subscribersLost"] for d in days)
    likes = sum(d["likes"] for d in days)
    comentarios = sum(d["comments"] for d in days)

    total_trafico = sum(t["views"] for t in traffic) or 1
    for t in traffic:
        t["fuente"] = LABELS.get(t["insightTrafficSourceType"],
                                    t["insightTrafficSourceType"])
        t["pct"] = round(t["views"] / total_trafico * 100, 1)

    # Concentration: how much of the traffic rests on the top two videos.
    top_vistas = sum(t["views"] for t in top) or 1
    dependencia = round(sum(t["views"] for t in top[:2]) / top_vistas * 100, 1)

    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "channel": info["title"],
        "subs": info["subscribers"],
        "total_videos": info["total_videos"],
        "window_days": args.days,
        "views": views,
        "minutes_watched": minutes,
        "net_subs": net_subs,
        "likes_pct": round(likes / views * 100, 2) if views else 0,
        "comments_pct": round(comentarios / views * 100, 2) if views else 0,
        "dependencia_top2_pct": dependencia,
        "top_mean_retention": round(
            sum(t.get("averageViewPercentage", 0) for t in top) / len(top), 1)
        if top else 0,
    }

    previo = snapshot_previo()
    delta = None
    if previo:
        delta = {k: round(summary[k] - previo[k], 2)
                 for k in ("subs", "views", "net_subs", "dependencia_top2_pct")
                 if isinstance(previo.get(k), (int, float))}
        delta["desde"] = previo["date"]

    if not args.no_snapshot:
        SNAPSHOTS.parent.mkdir(parents=True, exist_ok=True)
        with open(SNAPSHOTS, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(summary, ensure_ascii=False) + "\n")

    env = envelope(TOOL, SOURCE_API, {
        "summary": summary,
        "change_since_last_snapshot": delta,
        "top_videos": top,
        "exceptional_retention": [t for t in top
                                  if t.get("averageViewPercentage", 0) > 40],
        "traffic": traffic,
        "demographics": demo[:8],
        "geography": geo,
    }, {"days": args.days, "top_days": args.top_days}, False, notes=[
        "Aggregates (%, net, concentration) are computed (source: derived).",
        "Does NOT include CTR or impressions: they are not in the public API. "
        "For those you need ingest_studio_csv.py.",
    ])

    def md(e):
        d = e["data"]
        r = d["summary"]
        out = [base.md_header(e),
               f"\n# {r['channel']} — {r['date']}\n",
               f"{yt_data.fmt(r['subs'])} subs · {r['total_videos']} videos\n",
               "\n## Estado general\n",
               base.md_table([{"metric": k, "value": v} for k, v in r.items()]),
               ]
        if d["change_since_last_snapshot"]:
            out += ["\n## Change since the previous snapshot\n",
                    base.md_table([{"metric": k, "delta": v} for k, v in
                                   d["change_since_last_snapshot"].items()])]
        out += ["\n## Top videos\n",
                base.md_table(d["top_videos"][:10],
                              ["title", "views", "averageViewPercentage",
                               "subscribersGained"]),
                "\n## Trafico\n",
                base.md_table(d["traffic"], ["fuente", "views", "pct"]),
                "\n## Audiencia\n", base.md_table(d["demographics"]),
                "\n## Geografia\n",
                base.md_table(d["geography"], ["country", "views", "viewsPercent"])]
        return "\n".join(out)

    emit(env, args, md)


if __name__ == "__main__":
    main(TOOL, run)
