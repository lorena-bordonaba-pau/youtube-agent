"""Contrato común de todas las herramientas del harness.

Toda tool devuelve el mismo sobre de metadatos y usa los mismos códigos de
salida. El campo `source` es el mecanismo central de honestidad: indica si una
cifra es dato medido, cálculo derivado o estimación propia.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATOS_DIR = BASE_DIR / "datos"
MEMORIA_DIR = BASE_DIR / "memoria"

# --- Códigos de salida -----------------------------------------------------
EXIT_OK = 0
EXIT_AUTH = 2          # credenciales ausentes o caducadas
EXIT_QUOTA = 3         # cuota de la API agotada
EXIT_NO_DATA = 4       # datos insuficientes para responder
EXIT_USO = 64          # argumentos mal invocados (argparse usa 2 por
                       # defecto, que colisiona con EXIT_AUTH)

# --- Valores válidos de `source` -------------------------------------------
SOURCE_API = "youtube_api"      # dato directo de la API de Google
SOURCE_DERIVED = "derived"      # calculado en código sobre datos de la API
SOURCE_HEURISTIC = "heuristic"  # rúbrica o proxy propio — NO es dato medido
SOURCE_CONFIG = "config"        # contenido de un fichero local del harness
SOURCE_GENERATED = "generated"  # artefacto creado por un modelo externo — NO es
                                # medición de nada, ni evidencia de rendimiento

_SOURCES = {SOURCE_API, SOURCE_DERIVED, SOURCE_HEURISTIC, SOURCE_CONFIG,
            SOURCE_GENERATED}

# Cómo debe presentar el agente cada tipo de dato. Viaja dentro del sobre para
# que la regla esté delante del modelo en el momento de citar la cifra.
_AVISO = {
    SOURCE_API: "Dato directo de la API de YouTube.",
    SOURCE_DERIVED: "Calculado sobre datos de la API.",
    SOURCE_HEURISTIC: (
        "ESTIMACION PROPIA, no dato medido. Al citarla hay que declararlo "
        "explicitamente y no presentarla como prediccion de CTR ni de vistas."
    ),
    SOURCE_CONFIG: "Contenido de un fichero de configuracion local, no una medicion.",
    SOURCE_GENERATED: (
        "ARTEFACTO GENERADO por un modelo externo. No es un dato ni una "
        "medicion: no dice nada sobre como va a rendir. Al entregarlo hay que "
        "nombrar el proveedor y el modelo que lo produjo."
    ),
}


class ToolError(Exception):
    """Error con código de salida propio del contrato."""

    def __init__(self, mensaje: str, code: int = EXIT_NO_DATA, pista: str = ""):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.code = code
        self.pista = pista


def sobre(tool: str, source: str, data, params: dict | None = None,
          cache_hit: bool = False, notas: list[str] | None = None) -> dict:
    """Construye el sobre de metadatos estándar."""
    if source not in _SOURCES:
        raise ValueError(f"source invalido: {source!r}. Validos: {sorted(_SOURCES)}")
    envelope = {
        "tool": tool,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "aviso": _AVISO[source],
        "cache_hit": cache_hit,
        "params": params or {},
        "data": data,
    }
    if notas:
        envelope["notas"] = notas
    return envelope


class _Parser(argparse.ArgumentParser):
    """argparse sale con codigo 2 ante un error de uso, el mismo que usamos para
    credenciales. Un agente no podria distinguir "falta el token" de "falta un
    argumento", asi que los errores de uso salen con EXIT_USO."""

    def error(self, message):  # noqa: D102
        print(json.dumps({"tool": self.prog, "error": f"uso incorrecto: {message}",
                          "exit_code": EXIT_USO}, ensure_ascii=False),
              file=sys.stderr)
        sys.exit(EXIT_USO)


def parser(descripcion: str) -> argparse.ArgumentParser:
    """Parser base con los flags comunes a todas las tools."""
    p = _Parser(description=descripcion)
    p.add_argument("--json", action="store_true", default=True,
                   help="salida JSON (por defecto)")
    p.add_argument("--md", action="store_true",
                   help="salida Markdown legible para humanos")
    p.add_argument("--no-cache", action="store_true",
                   help="ignora la cache y fuerza llamada a la API")
    return p


def emitir(envelope: dict, args=None, md_fn=None) -> None:
    """Imprime el resultado en el formato pedido y sale con código 0."""
    if args is not None and getattr(args, "md", False) and md_fn is not None:
        print(md_fn(envelope))
    else:
        print(json.dumps(envelope, ensure_ascii=False, indent=2, default=str))
    sys.exit(EXIT_OK)


def fallar(err: "ToolError | Exception", tool: str = "") -> None:
    """Imprime un error estructurado por stderr y sale con su código.

    Nunca deja escapar un traceback crudo: el agente necesita un mensaje que
    pueda leer y transmitir.
    """
    if isinstance(err, ToolError):
        code, mensaje, pista = err.code, err.mensaje, err.pista
    else:
        code, mensaje, pista = EXIT_NO_DATA, str(err), ""
    payload = {"tool": tool, "error": mensaje, "exit_code": code}
    if pista:
        payload["pista"] = pista
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    sys.exit(code)


def main(tool: str, fn) -> None:
    """Envoltorio de ejecución: captura errores y los traduce al contrato."""
    try:
        fn()
    except ToolError as e:
        fallar(e, tool)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:  # noqa: BLE001 — frontera de proceso a propósito
        from googleapiclient.errors import HttpError
        if isinstance(e, HttpError):
            if e.resp.status == 403 and "quota" in str(e).lower():
                fallar(ToolError(
                    "Cuota diaria de la API de YouTube agotada.",
                    EXIT_QUOTA,
                    "La cuota se reinicia a medianoche hora del Pacifico. "
                    "Usa datos cacheados o espera.",
                ), tool)
            fallar(ToolError(f"Error de la API de YouTube: {e}", EXIT_NO_DATA), tool)
        fallar(e, tool)
