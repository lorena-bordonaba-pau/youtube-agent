#!/usr/bin/env python3
"""Re-autoriza el acceso a Google. ES INTERACTIVO: abre el navegador.

Ninguna otra tool del harness abre navegador. Si una tool sale con codigo 2,
este es el comando que hay que ejecutar a mano.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import auth
from lib.contrato import EXIT_OK, ToolError, fallar

if __name__ == "__main__":
    try:
        creds = auth.get_credentials(interactivo=True)
    except ToolError as e:
        fallar(e, "auth_setup")
    print(f"Autorizacion completada. Token guardado en {auth.TOKEN_FILE}")
    print(f"Scopes concedidos: {len(auth.SCOPES)}")
    sys.exit(EXIT_OK)
