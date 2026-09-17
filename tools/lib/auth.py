"""Autenticación con Google — nunca bloqueante.

A diferencia del toolkit original, esta capa JAMAS lanza `run_local_server`
durante una ejecución normal: si el token falta o no refresca, sale con código
EXIT_AUTH y le dice al agente qué comando ejecutar. Un navegador abriéndose a
mitad de una sesión de agente la cuelga indefinidamente.
"""
from __future__ import annotations

import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from .contrato import DATOS_DIR, EXIT_AUTH, ToolError

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
]

AUTH_DIR = DATOS_DIR / "auth"
SECRETS_FILE = AUTH_DIR / "client_secrets.json"
TOKEN_FILE = AUTH_DIR / "token.pickle"

_PISTA = (
    "Ejecuta `python3 tools/auth_setup.py` una vez para re-autorizar. "
    "Ese comando SI abre el navegador, a proposito."
)


def get_credentials(interactivo: bool = False):
    creds = None
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:  # noqa: BLE001
            # Un refresh muerto es justo el caso que auth_setup viene a arreglar:
            # en modo interactivo se cae al flujo de navegador en vez de abortar.
            if not interactivo:
                raise ToolError(
                    f"El token caduco y no se pudo refrescar: {e}", EXIT_AUTH, _PISTA
                ) from e
            creds = None
        else:
            _guardar(creds)
            return creds

    if not interactivo:
        falta = "token.pickle" if not TOKEN_FILE.exists() else "un token valido"
        raise ToolError(
            f"No hay credenciales utilizables: falta {falta} en {AUTH_DIR}.",
            EXIT_AUTH,
            _PISTA,
        )

    # Solo se llega aquí desde auth_setup.py, que pide interactivo=True.
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not SECRETS_FILE.exists():
        raise ToolError(
            f"No se encontro client_secrets.json en {SECRETS_FILE}.",
            EXIT_AUTH,
            "Sigue el paso 2 del README: crea un proyecto en Google Cloud "
            "Console, activa YouTube Data API v3 y YouTube Analytics API, "
            "crea un ID de cliente OAuth de tipo Aplicacion de escritorio y "
            "guarda el JSON descargado con ese nombre exacto.",
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(SECRETS_FILE), SCOPES)
    creds = flow.run_local_server(port=8080)
    _guardar(creds)
    return creds


def _guardar(creds) -> None:
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(creds, f)
    TOKEN_FILE.chmod(0o600)


def youtube():
    """Cliente de YouTube Data API v3."""
    return build("youtube", "v3", credentials=get_credentials(), cache_discovery=False)


def analytics():
    """Cliente de YouTube Analytics API v2."""
    return build("youtubeAnalytics", "v2", credentials=get_credentials(),
                 cache_discovery=False)


def estado() -> dict:
    """Diagnóstico de credenciales para `tools/init.py`. No lanza excepciones."""
    if not TOKEN_FILE.exists():
        return {"ok": False, "motivo": "falta token.pickle", "pista": _PISTA}
    try:
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "motivo": f"token ilegible: {e}", "pista": _PISTA}
    if creds.valid:
        return {"ok": True, "motivo": "token valido"}
    if not (creds.expired and creds.refresh_token):
        return {"ok": False, "motivo": "token invalido y sin refresh_token",
                "pista": _PISTA}
    # "Tiene refresh_token" no significa que el refresh funcione: los tokens de
    # una app en modo Testing caducan a los 7 dias. Hay que intentarlo de verdad
    # antes de decir que las credenciales estan bien.
    try:
        creds.refresh(Request())
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "motivo": f"el refresh fallo: {e}", "pista": _PISTA}
    _guardar(creds)
    return {"ok": True, "motivo": "token refrescado"}
