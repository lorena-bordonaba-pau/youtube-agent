#!/usr/bin/env python3
"""Ingest a YouTube Studio CSV export to get CTR and impressions.

CTR and impressions are NOT in YouTube's public API: only in Studio. This is
the only way to validate the title rubric against real outcomes.

How to export it:
  YouTube Studio > Analytics > Advanced mode > Videos tab >
  select metrics (Impressions, Impressions click-through rate) > Export > CSV.
"""
import csv
import json
import re
from pathlib import Path

from lib import base  # noqa: F401
from lib.contract import (DATA_DIR, EXIT_NO_DATA, SOURCE_API, ToolError, emit,
                          main, parser, envelope)

TOOL = "ingest_studio_csv"
DESTINO = DATA_DIR / "history" / "studio_ctr.json"

# Studio exports its headers in the account language, so each field lists the
# spellings we have seen. Add yours if your export is in another language:
# matching is case-insensitive and partial.
ALIAS = {
    "video": ["content", "video", "contenido", "vídeo"],
    "title": ["video title", "título del vídeo", "titulo del video"],
    "impressions": ["impressions", "impresiones"],
    "ctr": ["impressions click-through rate (%)", "impressions ctr (%)",
            "porcentaje de clics de las impresiones",
            "ctr de las impresiones (%)"],
    "views": ["views", "visualizaciones"],
    "mean_duration": ["average view duration",
                      "duración media de las visualizaciones"],
}


def find_column(fields: list[str], key: str) -> str | None:
    norm = {c.strip().lower(): c for c in fields}
    for alias in ALIAS[key]:
        if alias in norm:
            return norm[alias]
    for alias in ALIAS[key]:  # partial match as a fallback
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
    p.add_argument("--csv", required=True, help="path to the CSV exported from Studio")
    args = p.parse_args()

    path = Path(args.csv).expanduser()
    if not path.exists():
        raise ToolError(f"No exists {path}", EXIT_NO_DATA, __doc__.strip())

    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ToolError(f"{path} is empty.", EXIT_NO_DATA)

    fields = list(rows[0].keys())
    col_video = find_column(fields, "video")
    col_ctr = find_column(fields, "ctr")
    if not col_video or not col_ctr:
        raise ToolError(
            "The CSV has no recognisable video or CTR column. "
            f"Columnas encontradas: {fields}", EXIT_NO_DATA,
            "Export including the Impressions and CTR metrics.")

    col_imp = find_column(fields, "impressions")
    col_tit = find_column(fields, "title")
    col_vis = find_column(fields, "views")

    registros = []
    for row in rows:
        vid = (row.get(col_video) or "").strip()
        # Studio includes a "Total" row that is not a video.
        if not vid or vid.lower() in ("total", "totals"):
            continue
        registros.append({
            "video_id": vid,
            "title": row.get(col_tit, "").strip() if col_tit else None,
            "ctr_pct": num(row.get(col_ctr)),
            "impressions": int(num(row.get(col_imp))) if col_imp else None,
            "views": int(num(row.get(col_vis))) if col_vis else None,
        })

    if not registros:
        raise ToolError("No video row found in the CSV.", EXIT_NO_DATA)

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    previo = {}
    if DESTINO.exists():
        previo = {r["video_id"]: r for r in json.loads(
            DESTINO.read_text(encoding="utf-8"))["videos"]}
    previo.update({r["video_id"]: r for r in registros})
    ordenados = sorted(previo.values(), key=lambda r: r["ctr_pct"], reverse=True)
    DESTINO.write_text(json.dumps(
        {"origin": str(path), "videos": ordenados}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    ctrs = [r["ctr_pct"] for r in ordenados if r["ctr_pct"]]
    env = envelope(TOOL, SOURCE_API, {
        "ingested": len(registros),
        "running_total": len(ordenados),
        "mean_ctr": round(sum(ctrs) / len(ctrs), 2) if ctrs else None,
        "best": ordenados[0] if ordenados else None,
        "worst": ordenados[-1] if ordenados else None,
        "saved_to": str(DESTINO),
    }, {"csv": str(path)}, False, notes=[
        "CTR and impressions are real Studio data, not estimates.",
        "With this you can now check score_titles.py against real CTR and "
        "set `validated_against_ctr: true` in the rubric.",
    ])
    emit(env, args, lambda e: base.md_header(e) + "\n" + base.md_table(
        [{"field": k, "value": v} for k, v in e["data"].items()
         if not isinstance(v, dict)]))


if __name__ == "__main__":
    main(TOOL, run)
