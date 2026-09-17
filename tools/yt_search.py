#!/usr/bin/env python3
"""Busca vídeos en YouTube y detecta outliers dentro de los resultados.

CUESTA 100 UNIDADES DE CUOTA por consulta (la cuota diaria son 10.000).
Siempre cacheado 24h.

El script original tenía las consultas hardcodeadas, y por comas ausentes en el
array las tres últimas se concatenaban en una sola cadena con un typo incluido.
Aquí la consulta es un argumento.
"""
import statistics

from lib import base  # noqa: F401
from lib import cache, yt_data
from lib.contrato import SOURCE_DERIVED, emitir, main, parser, sobre

TOOL = "yt_search"


def run():
    p = parser(__doc__)
    p.add_argument("--query", required=True, help="consulta, o varias separadas por ';'")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--duration", default="medium",
                   choices=["any", "short", "medium", "long"])
    p.add_argument("--days", type=int, help="limita a vídeos publicados en N días")
    args = p.parse_args()

    consultas = [q.strip() for q in args.query.split(";") if q.strip()]
    resultados, hits = [], []
    for q in consultas:
        clave = f"{TOOL}:{q}:{args.limit}:{args.duration}:{args.days}"
        datos, hit = cache.memo(
            "busqueda", clave,
            lambda q=q: yt_data.buscar(q, args.limit, duracion=args.duration,
                                       dias=args.days),
            not args.no_cache)
        hits.append(hit)
        vistas = [d["views"] for d in datos] or [0]
        mediana = statistics.median(vistas)
        for d in datos:
            d["query"] = q
            d["ratio_vs_mediana"] = round(d["views"] / mediana, 2) if mediana else 0
        resultados.extend(datos)

    resultados.sort(key=lambda d: d["ratio_vs_mediana"], reverse=True)
    env = sobre(TOOL, SOURCE_DERIVED, resultados,
                {"query": consultas, "limit": args.limit, "duration": args.duration},
                all(hits),
                notas=["`ratio_vs_mediana` compara con la MEDIANA de los resultados "
                       "de esa busqueda, no con la media del canal de origen.",
                       "Cada consulta no cacheada cuesta 100 unidades de cuota."])
    emitir(env, args, lambda e: base.cabecera_md(e) + "\n" + base.tabla_md(
        e["data"], ["query", "title", "channel_title", "views", "ratio_vs_mediana",
                    "duration", "published_at"]))


if __name__ == "__main__":
    main(TOOL, run)
