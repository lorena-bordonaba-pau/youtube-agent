#!/usr/bin/env python3
"""Vídeos propios ordenados por vistas, con retención media real."""
from lib import base  # noqa: F401
from lib import cache, yt_data
from lib import yt_analytics as ya
from lib.contrato import SOURCE_API, emitir, main, parser, sobre

TOOL = "yt_top_videos"


def run():
    p = parser(__doc__)
    p.add_argument("--days", type=int, default=90)
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--by-retention", action="store_true",
                   help="reordena por averageViewPercentage en vez de vistas")
    args = p.parse_args()

    def fetch():
        filas = ya.top_videos(args.days, args.limit)
        titulos = {s["video_id"]: s["title"]
                   for s in yt_data.stats_videos([f["video"] for f in filas])}
        for f in filas:
            f["title"] = titulos.get(f["video"], "?")
        return filas

    datos, hit = cache.memo("analitica_propia", f"{TOOL}:{args.days}:{args.limit}",
                            fetch, not args.no_cache)
    if args.by_retention:
        datos = sorted(datos, key=lambda d: d.get("averageViewPercentage", 0), reverse=True)

    env = sobre(TOOL, SOURCE_API, datos,
                {"days": args.days, "limit": args.limit,
                 "orden": "retencion" if args.by_retention else "vistas"}, hit)
    emitir(env, args, lambda e: base.cabecera_md(e) + "\n" + base.tabla_md(
        e["data"], ["video", "title", "views", "averageViewPercentage",
                    "averageViewDuration", "subscribersGained"]))


if __name__ == "__main__":
    main(TOOL, run)
