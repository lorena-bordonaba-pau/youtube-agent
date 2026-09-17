#!/usr/bin/env python3
"""Evolución diaria de un vídeo propio."""
from lib import base  # noqa: F401
from lib import cache
from lib import yt_analytics as ya
from lib.contrato import SOURCE_API, emitir, main, parser, sobre

TOOL = "yt_video_analytics"


def run():
    p = parser(__doc__)
    p.add_argument("--video", required=True)
    p.add_argument("--days", type=int, default=90)
    args = p.parse_args()

    datos, hit = cache.memo("analitica_propia", f"{TOOL}:{args.video}:{args.days}",
                            lambda: ya.video(args.video, args.days), not args.no_cache)
    env = sobre(TOOL, SOURCE_API, datos, {"video": args.video, "days": args.days}, hit)
    emitir(env, args, lambda e: base.cabecera_md(e) + "\n" + base.tabla_md(e["data"]))


if __name__ == "__main__":
    main(TOOL, run)
