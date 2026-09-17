#!/usr/bin/env python3
"""Outliers de tu playlist manual de guardados.

Un outlier es un vídeo cuyas vistas superan N veces la media de su propio canal.
"""
from lib import base  # noqa: F401
from lib import cache, yt_data
from lib.contrato import (EXIT_NO_DATA, SOURCE_DERIVED, ToolError, emitir, main,
                          parser, sobre)

TOOL = "yt_outliers_playlist"


def run():
    p = parser(__doc__)
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--min-ratio", type=float, default=1.0)
    args = p.parse_args()

    cfg = yt_data.cargar_config()
    playlist = cfg.get("outlier_playlist_id", "")
    if not playlist or playlist.startswith("PL0000"):
        raise ToolError(
            "`outlier_playlist_id` no esta configurado en config/config.json.",
            EXIT_NO_DATA,
            "Crea una playlist de YouTube donde guardes videos interesantes y "
            "pon su ID ahi.")

    def fetch():
        items = yt_data.items_playlist(playlist, args.days)
        if not items:
            return []
        stats = yt_data.stats_videos([i["video_id"] for i in items])
        añadido = {i["video_id"]: i["added_at"] for i in items}
        medias: dict[str, float] = {}
        salida = []
        for s in stats:
            cid = s["channel_id"]
            if cid not in medias:
                medias[cid] = yt_data.media_vistas_canal(cid)
            media = medias[cid]
            ratio = round(s["views"] / media, 2) if media else 0
            salida.append({**s, "media_canal": int(media), "ratio": ratio,
                           "added_at": añadido.get(s["video_id"])})
        return sorted(salida, key=lambda x: x["ratio"], reverse=True)

    datos, hit = cache.memo("canal_ajeno", f"{TOOL}:{playlist}:{args.days}",
                            fetch, not args.no_cache)
    datos = [d for d in datos if d["ratio"] >= args.min_ratio]

    env = sobre(TOOL, SOURCE_DERIVED, datos,
                {"days": args.days, "min_ratio": args.min_ratio}, hit,
                notas=["`ratio` = vistas / media de las ultimas 15 subidas de su canal.",
                       "`channel_context` vive en config/config.json."])
    emitir(env, args, lambda e: base.cabecera_md(e) + "\n" + base.tabla_md(
        e["data"], ["title", "channel_title", "views", "media_canal", "ratio",
                    "engagement_rate", "duration"]))


if __name__ == "__main__":
    main(TOOL, run)
