#!/usr/bin/env python3
"""Informe completo del canal y snapshot en el histórico.

Cada ejecución anexa una línea a datos/historico/snapshots.jsonl, lo que permite
comparar entre fechas. El toolkit anterior generaba Markdown suelto y la
comparación entre snapshots la hacía una persona a mano.
"""
import json
from datetime import datetime
from pathlib import Path

from lib import base  # noqa: F401
from lib import cache, yt_data
from lib import yt_analytics as ya
from lib.contrato import DATOS_DIR, SOURCE_API, emitir, main, parser, sobre
from yt_traffic import ETIQUETAS

TOOL = "yt_report"
SNAPSHOTS = DATOS_DIR / "historico" / "snapshots.jsonl"


def snapshot_previo() -> dict | None:
    if not SNAPSHOTS.exists():
        return None
    lineas = [l for l in SNAPSHOTS.read_text(encoding="utf-8").splitlines() if l.strip()]
    return json.loads(lineas[-1]) if lineas else None


def run():
    p = parser(__doc__)
    p.add_argument("--days", type=int, default=28)
    p.add_argument("--top-days", type=int, default=90)
    p.add_argument("--no-snapshot", action="store_true",
                   help="no anexa al histórico")
    args = p.parse_args()

    usar_cache = not args.no_cache

    def f(nombre, fn):
        return cache.memo("analitica_propia", f"{TOOL}:{nombre}:{args.days}:{args.top_days}",
                          fn, usar_cache)[0]

    info = f("info", lambda: yt_data.canal_info())
    dias = f("dias", lambda: ya.canal(args.days))
    top = f("top", lambda: ya.top_videos(args.top_days, 20))
    trafico = f("trafico", lambda: ya.trafico(args.days))
    demo = f("demo", lambda: ya.demografia(args.top_days))
    geo = f("geo", lambda: ya.geografia(args.top_days, 10))

    titulos = {s["video_id"]: s["title"]
               for s in yt_data.stats_videos([t["video"] for t in top])}
    for t in top:
        t["title"] = titulos.get(t["video"], "?")

    vistas = sum(d["views"] for d in dias)
    minutos = sum(d["estimatedMinutesWatched"] for d in dias)
    subs_netos = sum(d["subscribersGained"] - d["subscribersLost"] for d in dias)
    likes = sum(d["likes"] for d in dias)
    comentarios = sum(d["comments"] for d in dias)

    total_trafico = sum(t["views"] for t in trafico) or 1
    for t in trafico:
        t["fuente"] = ETIQUETAS.get(t["insightTrafficSourceType"],
                                    t["insightTrafficSourceType"])
        t["pct"] = round(t["views"] / total_trafico * 100, 1)

    # Concentración: cuánto del tráfico depende de los dos vídeos principales.
    top_vistas = sum(t["views"] for t in top) or 1
    dependencia = round(sum(t["views"] for t in top[:2]) / top_vistas * 100, 1)

    resumen = {
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "canal": info["title"],
        "subs": info["subscribers"],
        "total_videos": info["total_videos"],
        "ventana_dias": args.days,
        "vistas": vistas,
        "minutos_vistos": minutos,
        "subs_netos": subs_netos,
        "likes_pct": round(likes / vistas * 100, 2) if vistas else 0,
        "comentarios_pct": round(comentarios / vistas * 100, 2) if vistas else 0,
        "dependencia_top2_pct": dependencia,
        "retencion_media_top": round(
            sum(t.get("averageViewPercentage", 0) for t in top) / len(top), 1)
        if top else 0,
    }

    previo = snapshot_previo()
    delta = None
    if previo:
        delta = {k: round(resumen[k] - previo[k], 2)
                 for k in ("subs", "vistas", "subs_netos", "dependencia_top2_pct")
                 if isinstance(previo.get(k), (int, float))}
        delta["desde"] = previo["fecha"]

    if not args.no_snapshot:
        SNAPSHOTS.parent.mkdir(parents=True, exist_ok=True)
        with open(SNAPSHOTS, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(resumen, ensure_ascii=False) + "\n")

    env = sobre(TOOL, SOURCE_API, {
        "resumen": resumen,
        "cambio_desde_ultimo_snapshot": delta,
        "top_videos": top,
        "retencion_excepcional": [t for t in top
                                  if t.get("averageViewPercentage", 0) > 40],
        "trafico": trafico,
        "demografia": demo[:8],
        "geografia": geo,
    }, {"days": args.days, "top_days": args.top_days}, False, notas=[
        "Los agregados (%, netos, dependencia) son calculados (source: derived).",
        "NO incluye CTR ni impresiones: no existen en la API publica. "
        "Para eso hace falta ingest_studio_csv.py.",
    ])

    def md(e):
        d = e["data"]
        r = d["resumen"]
        out = [base.cabecera_md(e),
               f"\n# {r['canal']} — {r['fecha']}\n",
               f"{yt_data.fmt(r['subs'])} subs · {r['total_videos']} videos\n",
               "\n## Estado general\n",
               base.tabla_md([{"metrica": k, "valor": v} for k, v in r.items()]),
               ]
        if d["cambio_desde_ultimo_snapshot"]:
            out += ["\n## Cambio desde el snapshot anterior\n",
                    base.tabla_md([{"metrica": k, "delta": v} for k, v in
                                   d["cambio_desde_ultimo_snapshot"].items()])]
        out += ["\n## Top videos\n",
                base.tabla_md(d["top_videos"][:10],
                              ["title", "views", "averageViewPercentage",
                               "subscribersGained"]),
                "\n## Trafico\n",
                base.tabla_md(d["trafico"], ["fuente", "views", "pct"]),
                "\n## Audiencia\n", base.tabla_md(d["demografia"]),
                "\n## Geografia\n",
                base.tabla_md(d["geografia"], ["country", "views", "viewsPercent"])]
        return "\n".join(out)

    emitir(env, args, md)


if __name__ == "__main__":
    main(TOOL, run)
