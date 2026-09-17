#!/usr/bin/env python3
"""Estadísticas públicas de uno o varios vídeos (cualquier canal)."""
from lib import base  # noqa: F401
from lib import cache, yt_data
from lib.contrato import SOURCE_API, emitir, main, parser, sobre

TOOL = "yt_video_stats"


def run():
    p = parser(__doc__)
    p.add_argument("--video", required=True, help="video_id, o varios separados por coma")
    args = p.parse_args()

    ids = [v.strip() for v in args.video.split(",") if v.strip()]
    datos, hit = cache.memo("canal_ajeno", f"{TOOL}:{','.join(sorted(ids))}",
                            lambda: yt_data.stats_videos(ids), not args.no_cache)
    env = sobre(TOOL, SOURCE_API, datos, {"video": ids}, hit)
    emitir(env, args, lambda e: base.cabecera_md(e) + "\n" + base.tabla_md(
        e["data"], ["video_id", "title", "views", "likes", "comments", "duration"]))


if __name__ == "__main__":
    main(TOOL, run)
