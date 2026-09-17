#!/usr/bin/env python3
"""Demografía de la audiencia: edad y género."""
from lib import base  # noqa: F401
from lib import cache
from lib import yt_analytics as ya
from lib.contrato import SOURCE_API, emitir, main, parser, sobre

TOOL = "yt_demographics"


def run():
    p = parser(__doc__)
    p.add_argument("--days", type=int, default=90)
    args = p.parse_args()

    datos, hit = cache.memo("analitica_propia", f"{TOOL}:{args.days}",
                            lambda: ya.demografia(args.days), not args.no_cache)
    por_genero = {}
    for d in datos:
        por_genero[d["gender"]] = round(
            por_genero.get(d["gender"], 0) + d["viewerPercentage"], 1)

    env = sobre(TOOL, SOURCE_API, {"detalle": datos, "por_genero": por_genero},
                {"days": args.days}, hit)
    emitir(env, args, lambda e: base.cabecera_md(e) + "\n" + base.tabla_md(e["data"]["detalle"]))


if __name__ == "__main__":
    main(TOOL, run)
