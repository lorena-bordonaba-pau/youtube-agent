#!/usr/bin/env python3
"""Términos de búsqueda REALES que traen tráfico al canal.

No es una estimación: son las consultas con las que la gente llegó de verdad.
Con --tipo RELATED_VIDEO, qué vídeos concretos están sugiriendo el tuyo.
"""
from lib import base  # noqa: F401
from lib import cache, yt_data
from lib import yt_analytics as ya
from lib.contrato import SOURCE_API, emitir, main, parser, sobre

TOOL = "yt_search_terms"


def run():
    p = parser(__doc__)
    p.add_argument("--days", type=int, default=90)
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--tipo", default="YT_SEARCH",
                   choices=["YT_SEARCH", "RELATED_VIDEO", "EXT_URL", "SUBSCRIBER"])
    p.add_argument("--video", help="limita a un vídeo concreto")
    args = p.parse_args()

    clave = f"{TOOL}:{args.tipo}:{args.days}:{args.limit}:{args.video}"
    datos, hit = cache.memo(
        "analitica_propia", clave,
        lambda: ya.trafico_detalle(args.days, args.tipo, args.limit, args.video),
        not args.no_cache)

    total = sum(d["views"] for d in datos) or 1
    for d in datos:
        d["termino"] = d.pop("insightTrafficSourceDetail")
        d["pct"] = round(d["views"] / total * 100, 1)

    # Con RELATED_VIDEO el "término" es un video_id: resolver su título ayuda.
    if args.tipo == "RELATED_VIDEO" and datos:
        titulos = {s["video_id"]: f"{s['channel_title']} — {s['title']}"
                   for s in yt_data.stats_videos([d["termino"] for d in datos])}
        for d in datos:
            d["titulo"] = titulos.get(d["termino"], "?")

    env = sobre(TOOL, SOURCE_API, datos,
                {"tipo": args.tipo, "days": args.days, "video": args.video}, hit,
                notas=["Estos son terminos de trafico REAL, no volumen de busqueda "
                       "estimado. Solo aparecen los que superan el umbral de "
                       "privacidad de YouTube."])
    cols = (["termino", "titulo", "views", "pct"] if args.tipo == "RELATED_VIDEO"
            else ["termino", "views", "pct", "estimatedMinutesWatched"])
    emitir(env, args, lambda e: base.cabecera_md(e) + "\n" + base.tabla_md(e["data"], cols))


if __name__ == "__main__":
    main(TOOL, run)
