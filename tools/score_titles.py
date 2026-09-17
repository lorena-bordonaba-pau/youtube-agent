#!/usr/bin/env python3
"""Puntúa títulos 0-100 con la rúbrica calibrada del canal.

NO PREDICE CTR. Es una lista de comprobación ponderada que codifica las
lecciones ya aprendidas en vídeos reales (config/rubricas/titulos.yaml).
Cada punto sumado o restado cita la memoria que lo justifica.
"""
import re

import yaml

from lib import base  # noqa: F401
from lib.contrato import (CONFIG_DIR, EXIT_NO_DATA, SOURCE_HEURISTIC, ToolError,
                          emitir, main, parser, sobre)

TOOL = "score_titles"
RUBRICA = CONFIG_DIR / "rubricas" / "titulos.yaml"


def cargar_rubrica() -> dict:
    if not RUBRICA.exists():
        raise ToolError(f"Falta la rubrica en {RUBRICA}", EXIT_NO_DATA)
    with open(RUBRICA, encoding="utf-8") as f:
        return yaml.safe_load(f)


def evaluar_eje(titulo: str, eje: dict) -> dict:
    peso = eje["peso"]
    puntos, razones = 0, []

    for b in eje.get("bonus", []):
        if re.search(b["patron"], titulo, re.IGNORECASE):
            puntos += b["puntos"]
            razones.append(f"+{b['puntos']} {b['motivo']}")
            break  # el bonus de un eje no se acumula consigo mismo

    for p in eje.get("penalizaciones", []):
        if re.search(p["patron"], titulo, re.IGNORECASE):
            puntos += p["puntos"]
            razones.append(f"{p['puntos']} {p['motivo']}")

    if "rangos" in eje:
        n = len(titulo)
        for r in eje["rangos"]:
            if n <= r.get("max", 10 ** 9):
                puntos += r["puntos"]
                razones.append(f"+{r['puntos']} {r['motivo']} ({n} caracteres)")
                break

    # Los ejes sin señal detectada parten de la mitad del peso: la ausencia de
    # una marca no es prueba de que el título sea malo en ese eje.
    if not razones:
        puntos = round(peso * 0.5)
        razones.append(f"+{puntos} Sin senal detectada en este eje (neutro)")

    return {
        "eje": eje["id"],
        "peso": peso,
        "puntos": max(0, min(peso, puntos)),
        "memoria": eje.get("memoria"),
        "razones": razones,
    }


def puntuar(titulo: str, rubrica: dict) -> dict:
    ejes = [evaluar_eje(titulo, e) for e in rubrica["ejes"]]
    return {
        "titulo": titulo,
        "caracteres": len(titulo),
        "score": sum(e["puntos"] for e in ejes),
        "desglose": ejes,
    }


def run():
    p = parser(__doc__)
    p.add_argument("--title", required=True,
                   help="título, o varios separados por ' || '")
    args = p.parse_args()

    rubrica = cargar_rubrica()
    titulos = [t.strip() for t in args.title.split("||") if t.strip()]
    resultados = sorted((puntuar(t, rubrica) for t in titulos),
                        key=lambda r: r["score"], reverse=True)

    env = sobre(TOOL, SOURCE_HEURISTIC,
                {"rubrica_version": rubrica["version"],
                 "calibrado_con": rubrica["calibrado_con"],
                 "validado_contra_ctr": rubrica["validado_contra_ctr"],
                 "resultados": resultados},
                {"n_titulos": len(titulos)}, False,
                notas=[
                    "NO es una prediccion de CTR. Es una lista de comprobacion "
                    "ponderada con las lecciones ya aprendidas del canal.",
                    "La rubrica NO esta validada contra CTR real: hace falta "
                    "ingerir el CSV de YouTube Studio (ingest_studio_csv.py).",
                    "Un titulo con score bajo puede funcionar; el score solo "
                    "dice cuanto se parece a lo que ya funciono antes.",
                ])

    def md(e):
        out = [base.cabecera_md(e), ""]
        for r in e["data"]["resultados"]:
            out.append(f"\n## {r['score']}/100 — {r['titulo']}  \n"
                       f"_{r['caracteres']} caracteres_\n")
            for d in r["desglose"]:
                mem = f" _(memoria: {d['memoria']})_" if d["memoria"] else ""
                out.append(f"- **{d['eje']}** {d['puntos']}/{d['peso']}{mem}")
                out.extend(f"    - {x}" for x in d["razones"])
        return "\n".join(out)

    emitir(env, args, md)


if __name__ == "__main__":
    main(TOOL, run)
