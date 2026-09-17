#!/usr/bin/env python3
"""Descarga miniaturas y calcula métricas visuales deterministas.

El toolkit anterior capturaba la URL de la miniatura y nunca la usaba.
Las métricas de aquí son objetivas (contraste, luminancia, saturación).
La lectura semántica — qué se ve, si el texto compite con el título — la hace
el agente abriendo el fichero descargado con visión.
"""
import urllib.request
from pathlib import Path

from PIL import Image

from lib import base  # noqa: F401
from lib import yt_data
from lib.contrato import (DATOS_DIR, EXIT_NO_DATA, SOURCE_DERIVED, ToolError,
                          emitir, main, parser, sobre)

TOOL = "yt_thumbnails"
DIR = DATOS_DIR / "miniaturas"


def descargar(video_id: str, url: str) -> Path:
    DIR.mkdir(parents=True, exist_ok=True)
    destino = DIR / f"{video_id}.jpg"
    if destino.exists():
        return destino
    # maxres no siempre existe; se degrada a hqdefault.
    candidatas = [f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg", url,
                  f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"]
    for cand in [c for c in candidatas if c]:
        try:
            req = urllib.request.Request(cand, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                if r.status == 200:
                    destino.write_bytes(r.read())
                    return destino
        except Exception:  # noqa: BLE001 — se prueba la siguiente candidata
            continue
    raise ToolError(f"No se pudo descargar la miniatura de {video_id}", EXIT_NO_DATA)


def metricas(ruta: Path) -> dict:
    img = Image.open(ruta).convert("RGB")
    ancho, alto = img.size
    peq = img.resize((160, 90))          # tamaño real percibido en el feed móvil
    pixeles = list(peq.getdata())

    lum = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in pixeles]
    media_lum = sum(lum) / len(lum)
    desv = (sum((x - media_lum) ** 2 for x in lum) / len(lum)) ** 0.5

    sat = []
    for r, g, b in pixeles:
        mx, mn = max(r, g, b), min(r, g, b)
        sat.append((mx - mn) / mx if mx else 0)

    # Contraste del tercio central: donde suele ir el sujeto y el texto grande
    centro = peq.crop((40, 22, 120, 68)).convert("L")
    cpx = list(centro.getdata())
    c_media = sum(cpx) / len(cpx)
    c_desv = (sum((x - c_media) ** 2 for x in cpx) / len(cpx)) ** 0.5

    return {
        "fichero": str(ruta),
        "resolucion": f"{ancho}x{alto}",
        "es_maxres": ancho >= 1280,
        "luminancia_media": round(media_lum, 1),
        "contraste_global": round(desv, 1),
        "contraste_centro": round(c_desv, 1),
        "saturacion_media": round(sum(sat) / len(sat), 3),
        "pct_pixeles_oscuros": round(sum(1 for x in lum if x < 60) / len(lum) * 100, 1),
        "pct_pixeles_claros": round(sum(1 for x in lum if x > 200) / len(lum) * 100, 1),
    }


def run():
    p = parser(__doc__)
    p.add_argument("--video", required=True, help="video_id, o varios separados por coma")
    args = p.parse_args()

    ids = [v.strip() for v in args.video.split(",") if v.strip()]
    stats = {s["video_id"]: s for s in yt_data.stats_videos(ids)}

    salida = []
    for vid in ids:
        info = stats.get(vid, {})
        ruta = descargar(vid, info.get("thumbnail"))
        salida.append({"video_id": vid, "title": info.get("title"),
                       "views": info.get("views"), **metricas(ruta)})

    env = sobre(TOOL, SOURCE_DERIVED, salida, {"video": ids},
                notas=[
                    "Metricas objetivas calculadas sobre el pixel, no opiniones.",
                    "NO miden si la miniatura es buena ni predicen CTR.",
                    "Para juzgar composicion, sujeto o texto, abre el fichero de "
                    "`fichero` con la herramienta de lectura de imagenes.",
                ])
    emitir(env, args, lambda e: base.cabecera_md(e) + "\n" + base.tabla_md(
        e["data"], ["video_id", "title", "resolucion", "contraste_global",
                    "contraste_centro", "luminancia_media", "saturacion_media"]))


if __name__ == "__main__":
    main(TOOL, run)
