#!/usr/bin/env python3
"""Fuentes de tráfico del canal propio, con etiquetas en español."""
from lib import base  # noqa: F401
from lib import cache
from lib import yt_analytics as ya
from lib.contrato import SOURCE_API, emitir, main, parser, sobre

TOOL = "yt_traffic"

# El toolkit original dejaba sin traducir SHORTS, HASHTAGS, YT_CHANNEL y otras,
# que salían crudas en los informes.
ETIQUETAS = {
    "SUBSCRIBER": "Suscriptores (feed/campana)",
    "YT_SEARCH": "Busqueda de YouTube",
    "RELATED_VIDEO": "Videos sugeridos",
    "EXT_URL": "Webs externas",
    "CHANNEL": "Pagina de canal",
    "YT_CHANNEL": "Pagina de canal",
    "NO_LINK_OTHER": "Directo / desconocido",
    "NO_LINK_EMBEDDED": "Reproductor embebido",
    "NOTIFICATION": "Notificaciones",
    "PLAYLIST": "Listas de reproduccion",
    "YT_PLAYLIST_PAGE": "Pagina de lista",
    "END_SCREEN": "Pantalla final",
    "ADVERTISING": "Publicidad",
    "SHORTS": "Feed de Shorts",
    "SHORTS_CONTENT_LINKS": "Enlaces desde Shorts",
    "ANNOTATION": "Anotaciones / tarjetas",
    "HASHTAGS": "Hashtags",
    "YT_OTHER_PAGE": "Otras paginas de YouTube",
    "SOUND_PAGE": "Pagina de sonido",
    "VIDEO_REMIXES": "Remezclas",
    "LIVE_REDIRECT": "Redireccion de directo",
    "PRODUCT_PAGE": "Pagina de producto",
    "IMMERSIVE": "Formato inmersivo",
}


def run():
    p = parser(__doc__)
    p.add_argument("--days", type=int, default=28)
    args = p.parse_args()

    datos, hit = cache.memo("analitica_propia", f"{TOOL}:{args.days}",
                            lambda: ya.trafico(args.days), not args.no_cache)
    total = sum(d["views"] for d in datos) or 1
    for d in datos:
        crudo = d["insightTrafficSourceType"]
        d["fuente"] = ETIQUETAS.get(crudo, crudo)
        d["pct"] = round(d["views"] / total * 100, 1)

    env = sobre(TOOL, SOURCE_API, datos, {"days": args.days}, hit,
                notas=["`pct` es calculado sobre el total (source: derived)."])
    emitir(env, args, lambda e: base.cabecera_md(e) + "\n" + base.tabla_md(
        e["data"], ["fuente", "views", "pct", "estimatedMinutesWatched"]))


if __name__ == "__main__":
    main(TOOL, run)
