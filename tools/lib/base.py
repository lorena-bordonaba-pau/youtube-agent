"""Andamiaje compartido por las tools: bootstrap de sys.path y helpers de MD."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_RAIZ = Path(__file__).resolve().parent.parent.parent


def cargar_env(ruta: Path | None = None) -> list[str]:
    """Carga `.env` de la raíz del proyecto en el entorno del proceso.

    Sin dependencias: `python-dotenv` no está en requirements y esto son veinte
    líneas. Una variable que ya venga del entorno real **no se pisa**, para que
    exportarla en la shell siga mandando sobre el fichero.

    Devuelve los nombres cargados, nunca los valores: ninguna clave debe acabar
    en un log ni en la salida de una tool.
    """
    import os

    fichero = ruta or _RAIZ / ".env"
    cargadas = []
    if not fichero.exists():
        return cargadas
    for linea in fichero.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        clave = clave.strip()
        valor = valor.strip().strip('"').strip("'")
        if clave and valor and not os.environ.get(clave):
            os.environ[clave] = valor
            cargadas.append(clave)
    return cargadas


# Se ejecuta al importar: todas las tools hacen `from lib import base`.
cargar_env()


def tabla_md(filas: list[dict], columnas: list[str] | None = None) -> str:
    """Renderiza una lista de dicts como tabla Markdown."""
    if not filas:
        return "_Sin datos._"
    cols = columnas or list(filas[0].keys())
    out = ["| " + " | ".join(cols) + " |",
           "|" + "|".join("---" for _ in cols) + "|"]
    for f in filas:
        celdas = [str(f.get(c, "")).replace("|", "\\|").replace("\n", " ") for c in cols]
        out.append("| " + " | ".join(celdas) + " |")
    return "\n".join(out)


def cabecera_md(envelope: dict) -> str:
    """Cabecera que deja la procedencia del dato a la vista también en Markdown."""
    return (f"# {envelope['tool']}\n\n"
            f"**Fuente:** `{envelope['source']}` — {envelope['aviso']}  \n"
            f"**Generado:** {envelope['generated_at']}"
            f"{' (cache)' if envelope['cache_hit'] else ''}\n")
