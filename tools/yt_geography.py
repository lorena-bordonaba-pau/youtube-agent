#!/usr/bin/env python3
"""Audiencia por país."""
from lib import base  # noqa: F401
from lib import cache
from lib import yt_analytics as ya
from lib.contrato import SOURCE_API, emitir, main, parser, sobre

TOOL = "yt_geography"


def run():
    p = parser(__doc__)
    p.add_argument("--days", type=int, default=90)
    p.add_argument("--limit", type=int, default=20)
    args = p.parse_args()

    datos, hit = cache.memo("analitica_propia", f"{TOOL}:{args.days}:{args.limit}",
                            lambda: ya.geografia(args.days, args.limit), not args.no_cache)
    env = sobre(TOOL, SOURCE_API, datos, {"days": args.days, "limit": args.limit}, hit,
                notas=["`viewsPercent` es calculado (source: derived)."])
    emitir(env, args, lambda e: base.cabecera_md(e) + "\n" + base.tabla_md(e["data"]))


if __name__ == "__main__":
    main(TOOL, run)
