#!/usr/bin/env python3
"""Vídeos recientes de un canal, con estadísticas públicas."""
from lib import base  # noqa: F401
from lib import cache, yt_data
from lib.contrato import SOURCE_API, emitir, main, parser, sobre

TOOL = "yt_recent_videos"


def run():
    p = parser(__doc__)
    p.add_argument("--channel", help="channel_id; omitir para el canal propio")
    p.add_argument("--limit", type=int, default=15)
    p.add_argument("--stats", action="store_true", help="incluye vistas/likes")
    args = p.parse_args()

    familia = "analitica_propia" if args.channel is None else "canal_ajeno"
    clave = f"{TOOL}:{args.channel or 'mine'}:{args.limit}:{args.stats}"

    def fetch():
        vids = yt_data.videos_de_canal(args.channel, args.limit)
        if not args.stats:
            return vids
        stats = {s["video_id"]: s for s in
                 yt_data.stats_videos([v["video_id"] for v in vids])}
        return [{**v, **stats.get(v["video_id"], {})} for v in vids]

    datos, hit = cache.memo(familia, clave, fetch, not args.no_cache)
    env = sobre(TOOL, SOURCE_API, datos,
                {"channel": args.channel or "mine", "limit": args.limit}, hit)
    cols = ["video_id", "title", "published_at"] + (["views", "likes"] if args.stats else [])
    emitir(env, args, lambda e: base.cabecera_md(e) + "\n" + base.tabla_md(e["data"], cols))


if __name__ == "__main__":
    main(TOOL, run)
