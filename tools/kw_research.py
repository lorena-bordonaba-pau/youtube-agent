#!/usr/bin/env python3
"""Investigación de keywords por PROXY. No da volumen de búsqueda real.

YouTube no publica volumen de búsqueda gratis. Esto combina tres señales:
  1. DEMANDA    — autocompletado de YouTube: cuántas variantes sugiere y
                  cómo de pronto aparece la keyword.
  2. COMPETENCIA— search.list: vistas medianas del top, antigüedad, tamaño de
                  los canales que rankean.
  3. CAMPO      — cruce con yt_search_terms: si ya te trae tráfico REAL, eso
                  pesa más que cualquier estimación.

El resultado es una POSICION RELATIVA entre las keywords comparadas, marcada
como `heuristic`. Nunca se debe presentar como volumen de búsqueda.
"""
import json
import statistics
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from lib import base  # noqa: F401
from lib import cache, yt_data
from lib.contrato import SOURCE_HEURISTIC, emitir, main, parser, sobre

TOOL = "kw_research"
ABC = "abcdefghijklmnopqrstuvwxyz"


def sugerencias(q: str, hl: str = "es", gl: str = "es") -> list[str]:
    url = ("https://suggestqueries.google.com/complete/search"
           f"?client=firefox&ds=yt&hl={hl}&gl={gl}&q={urllib.parse.quote(q)}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))[1]
    except Exception:  # noqa: BLE001 — sin sugerencias se sigue con las otras señales
        return []


def demanda(kw: str, profundo: bool) -> dict:
    """Señal de demanda: variantes que YouTube sugiere para la keyword."""
    base_sug = sugerencias(kw)
    todas = list(base_sug)
    if profundo:
        for letra in ABC:
            todas.extend(sugerencias(f"{kw} {letra}"))
    unicas = sorted({s for s in todas if kw.lower() in s.lower()})
    # Que la keyword exacta salga la primera indica intención de búsqueda propia.
    exacta = bool(base_sug) and base_sug[0].strip().lower() == kw.strip().lower()
    return {
        "variantes": len(unicas),
        "sugerencias": unicas[:40],
        "es_sugerencia_exacta": exacta,
        "score_demanda": min(100, round(len(unicas) * 2.5 + (20 if exacta else 0))),
    }


def competencia(kw: str, usar_cache: bool) -> dict:
    """Señal de competencia: cómo de duro está el top de resultados."""
    datos, _ = cache.memo(
        "busqueda", f"{TOOL}:comp:{kw}",
        lambda: yt_data.buscar(kw, 10, duracion="any"), usar_cache)
    if not datos:
        return {"resultados": 0, "score_competencia": 0, "mediana_vistas": 0}

    vistas = [d["views"] for d in datos]
    mediana = statistics.median(vistas)
    ahora = datetime.now(timezone.utc)
    antiguedades = []
    for d in datos:
        try:
            pub = datetime.fromisoformat(d["published_at"].replace("Z", "+00:00"))
            antiguedades.append((ahora - pub).days)
        except Exception:  # noqa: BLE001
            pass
    antiguedad_mediana = statistics.median(antiguedades) if antiguedades else 0

    # Mucha vista mediana = difícil. Resultados viejos = hueco de actualización.
    dureza = min(100, mediana / 1000)
    frescura = max(0, 40 - antiguedad_mediana / 18)  # >2 años ⇒ 0
    return {
        "resultados": len(datos),
        "mediana_vistas": int(mediana),
        "max_vistas": max(vistas),
        "antiguedad_mediana_dias": int(antiguedad_mediana),
        "top3": [{"title": d["title"], "channel_title": d["channel_title"],
                  "views": d["views"], "published_at": d["published_at"]}
                 for d in sorted(datos, key=lambda x: x["views"], reverse=True)[:3]],
        "score_competencia": round(dureza),
        "bonus_hueco_antiguedad": round(frescura),
    }


def run():
    p = parser(__doc__)
    p.add_argument("--kw", required=True, help="keyword, o varias separadas por ';'")
    p.add_argument("--profundo", action="store_true",
                   help="expande con el alfabeto (26 llamadas más de autocompletado)")
    p.add_argument("--sin-competencia", action="store_true",
                   help="omite search.list y ahorra 100 unidades de cuota por keyword")
    args = p.parse_args()

    keywords = [k.strip() for k in args.kw.split(";") if k.strip()]
    salida = []
    for kw in keywords:
        d = demanda(kw, args.profundo)
        c = ({} if args.sin_competencia
             else competencia(kw, not args.no_cache))
        # Oportunidad = demanda alta con competencia baja, más el hueco por antigüedad.
        oportunidad = (d["score_demanda"] - c.get("score_competencia", 0) * 0.6
                       + c.get("bonus_hueco_antiguedad", 0))
        salida.append({
            "keyword": kw,
            "score_oportunidad": max(0, min(100, round(oportunidad))),
            **d, **c,
        })

    salida.sort(key=lambda x: x["score_oportunidad"], reverse=True)
    env = sobre(TOOL, SOURCE_HEURISTIC, salida,
                {"kw": keywords, "profundo": args.profundo}, False,
                notas=[
                    "NO es volumen de busqueda. Es una posicion relativa entre las "
                    "keywords comparadas en esta misma ejecucion.",
                    "Comparar dos ejecuciones con keywords distintas no es valido.",
                    "Para demanda REAL y verificada, usa `yt_search_terms.py`: esos "
                    "si son terminos con los que la gente llego al canal.",
                ])
    emitir(env, args, lambda e: base.cabecera_md(e) + "\n" + base.tabla_md(
        e["data"], ["keyword", "score_oportunidad", "score_demanda", "variantes",
                    "score_competencia", "mediana_vistas", "antiguedad_mediana_dias"]))


if __name__ == "__main__":
    main(TOOL, run)
