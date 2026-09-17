#!/usr/bin/env python3
"""Puntúa una miniatura con la rúbrica calibrada del canal.

NO PREDICE CTR, y no puntúa sola: solo el 40% de la rúbrica es automático
(contraste, resolución, saturación). El 60% restante son ejes de JUICIO que
requieren mirar la imagen. La herramienta devuelve esas preguntas abiertas para
que el agente las responda abriendo el fichero, en vez de inventar un número.
"""
from pathlib import Path

import yaml

from lib import base  # noqa: F401
from lib.contrato import (CONFIG_DIR, EXIT_NO_DATA, EXIT_USO, SOURCE_HEURISTIC,
                          ToolError, emitir, main, parser, sobre)
from yt_thumbnails import descargar, metricas

TOOL = "score_thumbnail"
RUBRICA = CONFIG_DIR / "rubricas" / "miniaturas.yaml"


def por_rango(valor: float, eje: dict) -> tuple[int, str]:
    for r in eje.get("rangos", []):
        if valor >= r.get("min", 0):
            return r["puntos"], r["motivo"]
    return 0, "Fuera de rango"


def run():
    p = parser(__doc__)
    p.add_argument("--video", help="video_id de una miniatura ya publicada")
    p.add_argument("--image", help="ruta a una imagen local, p. ej. recién generada")
    p.add_argument("--titulo", help="título del vídeo, para el eje de redundancia")
    args = p.parse_args()

    if bool(args.video) == bool(args.image):
        raise ToolError("Hace falta --video o --image, y solo uno de los dos",
                        EXIT_USO,
                        "--video ID para una miniatura publicada; --image RUTA "
                        "para un fichero local (una imagen recien generada).")

    if not RUBRICA.exists():
        raise ToolError(f"Falta la rubrica en {RUBRICA}", EXIT_NO_DATA)
    with open(RUBRICA, encoding="utf-8") as f:
        rubrica = yaml.safe_load(f)

    meta = {}
    if args.image:
        ruta = Path(args.image)
        if not ruta.exists():
            raise ToolError(f"No existe {ruta}", EXIT_NO_DATA)
    else:
        from lib import yt_data
        try:
            info = yt_data.stats_videos([args.video])
            meta = info[0] if info else {}
        except Exception:  # noqa: BLE001 — sin API se sigue con solo el pixel
            meta = {}
        ruta = descargar(args.video, meta.get("thumbnail"))
    m = metricas(ruta)

    automaticos, total_auto, peso_auto = [], 0, 0
    for eje in rubrica["ejes_automaticos"]:
        peso = eje["peso"]
        peso_auto += peso
        if eje["id"] == "contraste_centro":
            pts, motivo = por_rango(m["contraste_centro"], eje)
            valor = m["contraste_centro"]
        elif eje["id"] == "saturacion":
            pts, motivo = por_rango(m["saturacion_media"], eje)
            valor = m["saturacion_media"]
        elif eje["id"] == "resolucion":
            pts = peso if m["es_maxres"] else round(peso * 0.3)
            motivo = ("maxres" if m["es_maxres"]
                      else "Por debajo de 1280x720: se vera blanda")
            valor = m["resolucion"]
        else:
            continue
        pts = min(pts, peso)
        total_auto += pts
        automaticos.append({"eje": eje["id"], "valor": valor, "puntos": pts,
                            "peso": peso, "motivo": motivo})

    juicio = [{"eje": e["id"], "peso": e["peso"], "memoria": e.get("memoria"),
               "pregunta": e["pregunta"].strip(), "puntos": None}
              for e in rubrica["ejes_de_juicio"]]

    env = sobre(TOOL, SOURCE_HEURISTIC, {
        "video": args.video,
        "image": args.image,
        "titulo": args.titulo or meta.get("title"),
        "fichero": m["fichero"],
        "metricas": m,
        "parcial_automatico": f"{total_auto}/{peso_auto}",
        "ejes_automaticos": automaticos,
        "ejes_de_juicio_pendientes": juicio,
        "score_total": None,
    }, {"video": args.video, "image": args.image}, False, notas=[
        "SCORE INCOMPLETO A PROPOSITO: solo se ha puntuado el 40% automatico.",
        f"Para completarlo, abre {m['fichero']} con la herramienta de lectura de "
        "imagenes y responde los `ejes_de_juicio_pendientes`.",
        "NO es una prediccion de CTR. La rubrica no esta validada contra CTR real.",
    ] + ([
        "Imagen local, probablemente generada: puntuarla NO la convierte en un "
        "dato. Un score alto sobre una imagen generada sigue siendo una rubrica "
        "propia sin validar aplicada a un artefacto.",
    ] if args.image else []))

    def md(e):
        d = e["data"]
        out = [base.cabecera_md(e),
               f"\n**{d['titulo'] or '(sin titulo)'}**  \n`{d['fichero']}`\n",
               f"\n## Automatico: {d['parcial_automatico']}\n",
               base.tabla_md(d["ejes_automaticos"],
                             ["eje", "valor", "puntos", "peso", "motivo"]),
               "\n## Pendiente de juicio visual (60 puntos)\n"]
        for j in d["ejes_de_juicio_pendientes"]:
            mem = f" _(memoria: {j['memoria']})_" if j["memoria"] else ""
            out.append(f"- **{j['eje']}** ({j['peso']} pts){mem}: {j['pregunta']}")
        return "\n".join(out)

    emitir(env, args, md)


if __name__ == "__main__":
    main(TOOL, run)
