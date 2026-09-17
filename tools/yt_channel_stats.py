#!/usr/bin/env python3
"""Estadísticas de un canal. Sin --channel, el canal propio."""
from lib import base  # noqa: F401  (bootstrap de sys.path)
from lib import cache, yt_data
from lib.contrato import SOURCE_API, emitir, main, parser, sobre

TOOL = "yt_channel_stats"


def run():
    p = parser(__doc__)
    p.add_argument("--channel", help="channel_id; omitir para el canal propio")
    args = p.parse_args()

    propio = args.channel is None
    familia = "analitica_propia" if propio else "canal_ajeno"
    datos, hit = cache.memo(
        familia, f"{TOOL}:{args.channel or 'mine'}",
        lambda: yt_data.canal_info(args.channel), not args.no_cache)

    env = sobre(TOOL, SOURCE_API, datos, {"channel": args.channel or "mine"}, hit)
    emitir(env, args, lambda e: base.cabecera_md(e) + "\n" + base.tabla_md(
        [{"campo": k, "valor": v} for k, v in e["data"].items()]))


if __name__ == "__main__":
    main(TOOL, run)
