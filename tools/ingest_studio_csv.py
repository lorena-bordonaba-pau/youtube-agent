#!/usr/bin/env python3
"""Ingiere un export CSV de YouTube Studio para tener CTR e impresiones.

CTR e impresiones NO existen en la API publica de YouTube: solo en Studio.
Este es el unico camino para validar la rubrica de titulos contra resultado real.

Como exportarlo:
  YouTube Studio > Estadisticas > Modo avanzado > pestana Videos >
  seleccionar metricas (Impresiones, CTR de impresiones) > Exportar > CSV.
"""
import csv
import json
import re
from pathlib import Path

from lib import base  # noqa: F401
from lib.contrato import (DATOS_DIR, EXIT_NO_DATA, SOURCE_API, ToolError, emitir,
                          main, parser, sobre)

TOOL = "ingest_studio_csv"
DESTINO = DATOS_DIR / "historico" / "studio_ctr.json"

# Studio exporta con los encabezados en el idioma de la cuenta.
ALIAS = {
    "video": ["contenido", "content", "video", "vídeo"],
    "titulo": ["título del vídeo", "titulo del video", "video title"],
    "impresiones": ["impresiones", "impressions"],
    "ctr": ["porcentaje de clics de las impresiones",
            "ctr de las impresiones (%)", "impressions click-through rate (%)",
            "impressions ctr (%)"],
    "vistas": ["visualizaciones", "views"],
    "duracion_media": ["duración media de las visualizaciones",
                       "average view duration"],
}


def localizar(campos: list[str], clave: str) -> str | None:
    norm = {c.strip().lower(): c for c in campos}
    for alias in ALIAS[clave]:
        if alias in norm:
            return norm[alias]
    for alias in ALIAS[clave]:  # coincidencia parcial como respaldo
        for k, original in norm.items():
            if alias in k:
                return original
    return None


def num(v: str) -> float:
    if v is None:
        return 0.0
    v = re.sub(r"[^\d,.\-]", "", str(v)).replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return 0.0


def run():
    p = parser(__doc__)
    p.add_argument("--csv", required=True, help="ruta al CSV exportado de Studio")
    args = p.parse_args()

    ruta = Path(args.csv).expanduser()
    if not ruta.exists():
        raise ToolError(f"No existe {ruta}", EXIT_NO_DATA, __doc__.strip())

    with open(ruta, encoding="utf-8-sig", newline="") as f:
        filas = list(csv.DictReader(f))
    if not filas:
        raise ToolError(f"{ruta} esta vacio.", EXIT_NO_DATA)

    campos = list(filas[0].keys())
    col_video = localizar(campos, "video")
    col_ctr = localizar(campos, "ctr")
    if not col_video or not col_ctr:
        raise ToolError(
            "El CSV no tiene columna de video o de CTR reconocible. "
            f"Columnas encontradas: {campos}", EXIT_NO_DATA,
            "Exporta incluyendo las metricas Impresiones y CTR de impresiones.")

    col_imp = localizar(campos, "impresiones")
    col_tit = localizar(campos, "titulo")
    col_vis = localizar(campos, "vistas")

    registros = []
    for fila in filas:
        vid = (fila.get(col_video) or "").strip()
        # Studio incluye una fila "Total" que no es un vídeo.
        if not vid or vid.lower() in ("total", "totales"):
            continue
        registros.append({
            "video_id": vid,
            "titulo": fila.get(col_tit, "").strip() if col_tit else None,
            "ctr_pct": num(fila.get(col_ctr)),
            "impresiones": int(num(fila.get(col_imp))) if col_imp else None,
            "vistas": int(num(fila.get(col_vis))) if col_vis else None,
        })

    if not registros:
        raise ToolError("No se encontro ninguna fila de video en el CSV.", EXIT_NO_DATA)

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    previo = {}
    if DESTINO.exists():
        previo = {r["video_id"]: r for r in json.loads(
            DESTINO.read_text(encoding="utf-8"))["videos"]}
    previo.update({r["video_id"]: r for r in registros})
    ordenados = sorted(previo.values(), key=lambda r: r["ctr_pct"], reverse=True)
    DESTINO.write_text(json.dumps(
        {"origen": str(ruta), "videos": ordenados}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    ctrs = [r["ctr_pct"] for r in ordenados if r["ctr_pct"]]
    env = sobre(TOOL, SOURCE_API, {
        "ingeridos": len(registros),
        "total_acumulado": len(ordenados),
        "ctr_medio": round(sum(ctrs) / len(ctrs), 2) if ctrs else None,
        "mejor": ordenados[0] if ordenados else None,
        "peor": ordenados[-1] if ordenados else None,
        "guardado_en": str(DESTINO),
    }, {"csv": str(ruta)}, False, notas=[
        "CTR e impresiones son dato real de Studio, no estimacion.",
        "Con esto ya se puede contrastar el score de score_titles.py contra el "
        "CTR real y marcar `validado_contra_ctr: true` en la rubrica.",
    ])
    emitir(env, args, lambda e: base.cabecera_md(e) + "\n" + base.tabla_md(
        [{"campo": k, "valor": v} for k, v in e["data"].items()
         if not isinstance(v, dict)]))


if __name__ == "__main__":
    main(TOOL, run)
