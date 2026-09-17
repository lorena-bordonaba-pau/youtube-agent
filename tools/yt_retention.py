#!/usr/bin/env python3
"""Curva de retención real de un vídeo propio: dónde abandona la gente.

Hasta ahora solo existía `averageViewPercentage`, que dice CUANTO retienes pero
no DONDE se van. Esto convierte los re-hooks de min 3 y min 6 del SOP de guion
en algo verificable.
"""
from lib import base  # noqa: F401
from lib import cache, yt_data
from lib import yt_analytics as ya
from lib.contrato import (EXIT_NO_DATA, SOURCE_API, ToolError, emitir, main,
                          parser, sobre)

TOOL = "yt_retention"

# Una caída de más de este % de audiencia entre dos puntos consecutivos de la
# curva (cada punto = 1% del vídeo) se marca como abandono concentrado.
UMBRAL_CAIDA = 1.5


def run():
    p = parser(__doc__)
    p.add_argument("--video", required=True)
    p.add_argument("--days", type=int, default=365)
    p.add_argument("--umbral", type=float, default=UMBRAL_CAIDA)
    args = p.parse_args()

    def fetch():
        curva = ya.retencion(args.video, args.days)
        meta = yt_data.stats_videos([args.video])
        return {"curva": curva, "meta": meta[0] if meta else None}

    datos, hit = cache.memo("analitica_propia", f"{TOOL}:{args.video}:{args.days}",
                            fetch, not args.no_cache)
    curva = datos["curva"]
    if not curva:
        raise ToolError(
            f"Sin datos de retencion para {args.video}.", EXIT_NO_DATA,
            "Puede ser un video demasiado nuevo, con pocas vistas, o que no "
            "pertenezca al canal autorizado.")

    dur_s = (datos["meta"] or {}).get("duration_s", 0)

    # Anotar cada punto con su momento real del vídeo y la caída respecto al anterior
    puntos, previo = [], None
    for fila in curva:
        ratio = fila["elapsedVideoTimeRatio"]
        watch = round(fila["audienceWatchRatio"] * 100, 2)
        seg = int(ratio * dur_s) if dur_s else None
        punto = {
            "pct_video": round(ratio * 100, 1),
            "momento": f"{seg // 60}:{seg % 60:02d}" if seg is not None else None,
            "audiencia_pct": watch,
            "vs_similares": round(fila.get("relativeRetentionPerformance", 0), 3),
            "caida": round(previo - watch, 2) if previo is not None else 0,
        }
        puntos.append(punto)
        previo = watch

    caidas = sorted((p for p in puntos if p["caida"] >= args.umbral),
                    key=lambda p: p["caida"], reverse=True)

    # Hitos que interesan al SOP de guion
    def en(pct):
        return min(puntos, key=lambda p: abs(p["pct_video"] - pct))

    hitos = {}
    if dur_s:
        for etiqueta, segundo in (("intro_30s", 30), ("re_hook_min3", 180),
                                  ("re_hook_min6", 360)):
            if segundo < dur_s:
                hitos[etiqueta] = en(segundo / dur_s * 100)
    hitos["mitad"] = en(50)
    hitos["final"] = puntos[-1]

    env = sobre(TOOL, SOURCE_API,
                {"video": args.video,
                 "titulo": (datos["meta"] or {}).get("title"),
                 "duracion": (datos["meta"] or {}).get("duration"),
                 "puntos": puntos,
                 "caidas_detectadas": caidas[:10],
                 "hitos": hitos},
                {"video": args.video, "days": args.days, "umbral": args.umbral}, hit,
                notas=[
                    "`audiencia_pct` es dato de la API (audienceWatchRatio).",
                    "`vs_similares` compara con videos de duracion parecida en "
                    "YouTube: 0.5 es la mediana.",
                    "`caida` y `momento` son calculados (source: derived).",
                ])

    def md(e):
        d = e["data"]
        out = [base.cabecera_md(e), f"\n**{d['titulo']}** ({d['duracion']})\n",
               "\n## Hitos\n",
               base.tabla_md([{"hito": k, **v} for k, v in d["hitos"].items()],
                             ["hito", "momento", "pct_video", "audiencia_pct",
                              "vs_similares"]),
               f"\n## Caidas concentradas (>= {args.umbral} puntos)\n",
               base.tabla_md(d["caidas_detectadas"],
                             ["momento", "pct_video", "audiencia_pct", "caida"])]
        return "\n".join(out)

    emitir(env, args, md)


if __name__ == "__main__":
    main(TOOL, run)
