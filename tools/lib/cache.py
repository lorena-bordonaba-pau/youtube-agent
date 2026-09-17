"""Caché en disco con TTL por tipo de dato.

La cuota diaria de la API de YouTube son 10.000 unidades y `search.list` cuesta
100 por llamada. Sin caché, una sesión de ideación quema la cuota repitiendo
las mismas búsquedas.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from .contrato import DATOS_DIR

CACHE_DIR = DATOS_DIR / "cache"

# TTL en segundos, por familia de dato.
TTL = {
    "analitica_propia": 6 * 3600,        # cambia a diario, pero no cada hora
    "canal_ajeno": 24 * 3600,            # stats públicas de terceros
    "busqueda": 24 * 3600,               # search.list — la llamada más cara
    "transcripcion": 30 * 24 * 3600,     # el contenido de un vídeo no cambia
    "miniatura": 30 * 24 * 3600,
    "keywords": 7 * 24 * 3600,           # autocompletado: deriva lenta
}
TTL_DEFECTO = 6 * 3600


def _ruta(familia: str, clave: str) -> Path:
    h = hashlib.sha256(clave.encode("utf-8")).hexdigest()[:16]
    return CACHE_DIR / familia / f"{h}.json"


def leer(familia: str, clave: str):
    """Devuelve el valor cacheado o None si no existe o expiró."""
    ruta = _ruta(familia, clave)
    if not ruta.exists():
        return None
    edad = time.time() - ruta.stat().st_mtime
    if edad > TTL.get(familia, TTL_DEFECTO):
        return None
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)["valor"]
    except Exception:  # noqa: BLE001 — una caché corrupta no debe romper la tool
        return None


def escribir(familia: str, clave: str, valor) -> None:
    ruta = _ruta(familia, clave)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump({"clave": clave, "valor": valor}, f, ensure_ascii=False, default=str)


def memo(familia: str, clave: str, fn, usar_cache: bool = True):
    """Devuelve (valor, cache_hit). Ejecuta `fn` solo si hace falta."""
    if usar_cache:
        cacheado = leer(familia, clave)
        if cacheado is not None:
            return cacheado, True
    valor = fn()
    escribir(familia, clave, valor)
    return valor, False


def estado() -> dict:
    """Resumen para `tools/init.py`."""
    if not CACHE_DIR.exists():
        return {"entradas": 0, "familias": {}}
    familias = {}
    total = 0
    for sub in sorted(CACHE_DIR.iterdir()):
        if sub.is_dir():
            n = len(list(sub.glob("*.json")))
            if n:
                familias[sub.name] = n
                total += n
    return {"entradas": total, "familias": familias}
