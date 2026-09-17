#!/usr/bin/env python3
"""Analítica diaria del canal propio: vistas, retención media, subs, engagement."""
from lib import base  # noqa: F401
from lib import cache
from lib import yt_analytics as ya
from lib.contrato import SOURCE_API, emitir, main, parser, sobre

TOOL = "yt_analytics"


def run():
    p = parser(__doc__)
    p.add_argument("--days", type=int, default=28)
    args = p.parse_args()

    datos, hit = cache.memo("analitica_propia", f"{TOOL}:{args.days}",
                            lambda: ya.canal(args.days), not args.no_cache)

    totales = {
        "views": sum(d["views"] for d in datos),
        "estimatedMinutesWatched": sum(d["estimatedMinutesWatched"] for d in datos),
        "subscribersNet": sum(d["subscribersGained"] - d["subscribersLost"] for d in datos),
        "likes": sum(d["likes"] for d in datos),
        "comments": sum(d["comments"] for d in datos),
    }
    env = sobre(TOOL, SOURCE_API, {"dias": datos, "totales": totales},
                {"days": args.days}, hit,
                notas=["`totales` es una suma sobre datos de la API (source: derived)."])
    emitir(env, args, lambda e: base.cabecera_md(e) + "\n" + base.tabla_md(e["data"]["dias"]))


if __name__ == "__main__":
    main(TOOL, run)
