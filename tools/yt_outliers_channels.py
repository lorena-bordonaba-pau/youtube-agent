#!/usr/bin/env python3
"""Outliers en los canales de competencia e inspiración configurados."""
from lib import base  # noqa: F401
from lib import cache, yt_data
from lib.contrato import SOURCE_DERIVED, emitir, main, parser, sobre

TOOL = "yt_outliers_channels"


def _dias(iso: str) -> int:
    from datetime import datetime, timezone
    return (datetime.now(timezone.utc)
            - datetime.fromisoformat(iso.replace("Z", "+00:00"))).days


def analizar(entrada: dict, min_ratio: float, muestra: int) -> dict:
    info = yt_data.canal_info(entrada["channel_id"])
    vids = yt_data.videos_de_canal(entrada["channel_id"], muestra)
    stats = yt_data.stats_videos([v["video_id"] for v in vids])
    if not stats:
        return {**entrada, "subs": info["subscribers"], "media": 0, "outliers": []}
    media = sum(s["views"] for s in stats) / len(stats)
    outliers = []
    for s in stats:
        ratio = round(s["views"] / media, 2) if media else 0
        if ratio >= min_ratio:
            dias = _dias(s["published_at"])
            outliers.append({
                "title": s["title"], "video_id": s["video_id"], "views": s["views"],
                "ratio": ratio, "engagement_rate": s["engagement_rate"],
                "duration": s["duration"], "published_at": s["published_at"],
                "dias": dias,
                # Un outlier de hace un año no es una oportunidad: es historia.
                "frescura": ("caliente" if dias <= 30 else "tibio" if dias <= 90
                             else "frio"),
                "description_preview": (s["description"] or "")[:200],
            })
    return {
        **entrada, "subs": info["subscribers"], "media": int(media),
        "outliers": sorted(outliers, key=lambda o: o["ratio"], reverse=True),
    }


def run():
    p = parser(__doc__)
    p.add_argument("--min-ratio", type=float, default=2.0)
    p.add_argument("--sample", type=int, default=30)
    p.add_argument("--max-dias", type=int, default=90,
                   help="descarta outliers mas antiguos que N dias (def. 90). "
                        "Usa 9999 para no filtrar.")
    p.add_argument("--list", dest="lista",
                   help="nombre de una lista de config/channels_lists.json "
                        "(competencia, inspiracion, vecindario...)")
    args = p.parse_args()

    canales = yt_data.cargar_canales(args.lista)

    def fetch():
        return [analizar(c, args.min_ratio, args.sample) for c in canales]

    def filtrar_por_edad(datos):
        for c in datos:
            c["outliers"] = [o for o in c["outliers"]
                             if o.get("dias", 0) <= args.max_dias]
        return datos

    clave = f"{TOOL}:{args.lista or 'todas'}:{args.min_ratio}:{args.sample}"
    datos, hit = cache.memo("canal_ajeno", clave, fetch, not args.no_cache)
    datos = filtrar_por_edad(datos)

    total = sum(len(c["outliers"]) for c in datos)
    env = sobre(TOOL, SOURCE_DERIVED,
                {"canales": datos, "total_outliers": total},
                {"list": args.lista or "todas", "min_ratio": args.min_ratio,
                 "sample": args.sample}, hit,
                notas=["`ratio` = vistas / media de las ultimas N subidas de ESE canal.",
                       f"Filtrado a outliers de <= {args.max_dias} dias. Un outlier "
                       "viejo no es una oportunidad, es historia.",
                       "Comparar vistas entre listas de idiomas distintos NO es "
                       "directo: ver el factor de TAM en memoria/."])

    def md(e):
        out = [base.cabecera_md(e), f"\n**{e['data']['total_outliers']} outliers** "
               f"(umbral {args.min_ratio}x, muestra {args.sample} videos/canal)\n"]
        for c in e["data"]["canales"]:
            if not c["outliers"]:
                continue
            out.append(f"\n### {c['list_type'].upper()} — {c['name']} "
                       f"({yt_data.fmt(c['subs'])} subs, media {yt_data.fmt(c['media'])})\n")
            out.append(base.tabla_md(c["outliers"],
                                     ["title", "views", "ratio", "dias", "frescura",
                                      "engagement_rate", "duration"]))
        return "\n".join(out)

    emitir(env, args, md)


if __name__ == "__main__":
    main(TOOL, run)
