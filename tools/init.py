#!/usr/bin/env python3
"""Estado del harness al abrir sesión. Se ejecuta desde el hook SessionStart.

Imprime lo que el agente necesita saber ANTES de su primera respuesta: si hay
credenciales, si el perfil de voz está poblado, cuándo se midió el canal por
última vez. Sin esto, lo descubre a mitad de una respuesta.

Nunca falla: si algo va mal, lo reporta como aviso. Un hook que revienta
bloquea el arranque de la sesión.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import auth, cache  # noqa: E402
from lib.contrato import (BASE_DIR, CONFIG_DIR, DATOS_DIR,  # noqa: E402
                          MEMORIA_DIR)

SNAPSHOTS = DATOS_DIR / "historico" / "snapshots.jsonl"


def dias_desde(fecha: str) -> int | None:
    try:
        return (datetime.now() - datetime.strptime(fecha, "%Y-%m-%d")).days
    except Exception:  # noqa: BLE001
        return None


def main() -> None:
    lineas = ["=== Harness de coach de YouTube ==="]
    avisos = []

    # Credenciales
    try:
        est = auth.estado()
        lineas.append(f"Credenciales: {'OK' if est['ok'] else 'NO'} — {est['motivo']}")
        if not est["ok"]:
            avisos.append(est.get("pista", ""))
    except Exception as e:  # noqa: BLE001
        lineas.append(f"Credenciales: no verificables ({e})")

    # Último snapshot del canal
    if SNAPSHOTS.exists():
        try:
            filas = [l for l in SNAPSHOTS.read_text(encoding="utf-8").splitlines()
                     if l.strip()]
            ultimo = json.loads(filas[-1])
            d = dias_desde(ultimo["fecha"])
            frescura = "hoy" if d == 0 else f"hace {d} dias"
            lineas.append(
                f"Ultimo snapshot: {ultimo['fecha']} ({frescura}) — "
                f"{ultimo['subs']} subs, {ultimo['vistas']} vistas/"
                f"{ultimo['ventana_dias']}d · {len(filas)} snapshots en total")
            if d is not None and d > 14:
                avisos.append("Los datos del canal tienen mas de 2 semanas: "
                              "ejecuta `python3 tools/yt_report.py` antes de "
                              "afirmar cifras.")
        except Exception as e:  # noqa: BLE001
            lineas.append(f"Ultimo snapshot: ilegible ({e})")
    else:
        lineas.append("Ultimo snapshot: ninguno todavia")
        avisos.append("Sin linea base. Ejecuta `python3 tools/yt_report.py` "
                      "para tener datos propios.")

    # Perfil de voz — la skill de guion depende de él
    voz = MEMORIA_DIR / "voice_profile.md"
    if voz.exists():
        cuerpo = voz.read_text(encoding="utf-8").split("---", 2)[-1].strip()
        palabras = len(cuerpo.split())
        # El placeholder explica como poblarlo y son ~160 palabras: contar solo
        # longitud daria un falso "poblado". El marcador explicito manda.
        poblado = "SIN POBLAR" not in cuerpo.upper() and palabras > 150
        lineas.append(f"Perfil de voz: {'poblado' if poblado else 'VACIO'} "
                      f"({palabras} palabras)")
        if not poblado:
            avisos.append("El perfil de voz esta sin poblar. La skill `guion` "
                          "debe construirlo con transcripciones reales antes de "
                          "escribir, no inventarlo.")
    else:
        lineas.append("Perfil de voz: no existe")

    # CTR real de Studio — sin esto las rúbricas quedan sin validar
    ctr = DATOS_DIR / "historico" / "studio_ctr.json"
    if ctr.exists():
        try:
            n = len(json.loads(ctr.read_text(encoding="utf-8"))["videos"])
            lineas.append(f"CTR de Studio: {n} videos ingeridos")
        except Exception:  # noqa: BLE001
            lineas.append("CTR de Studio: fichero ilegible")
    else:
        lineas.append("CTR de Studio: sin ingerir — las rubricas de scoring "
                      "siguen SIN VALIDAR contra CTR real")

    # Configuración inicial — el paso que más se salta y el que más duele.
    # Un harness sin identidad rellenada da consejos de manual, que es
    # exactamente lo que este proyecto existe para no hacer.
    sin_configurar = []
    contrato = BASE_DIR / "CLAUDE.md"
    if contrato.exists() and "[TEMA DEL CANAL]" in contrato.read_text(encoding="utf-8"):
        sin_configurar.append("la seccion 1 de CLAUDE.md (identidad del canal)")
    cfg_canal = CONFIG_DIR / "config.json"
    if cfg_canal.exists():
        try:
            if not json.loads(cfg_canal.read_text(encoding="utf-8")).get("channel_context"):
                sin_configurar.append("`channel_context` en config/config.json")
        except Exception:  # noqa: BLE001
            sin_configurar.append("config/config.json (ilegible)")
    if sin_configurar:
        lineas.append("Configuracion: SIN PERSONALIZAR")
        avisos.append(
            "INSTALACION SIN PERSONALIZAR. Falta rellenar: "
            + "; ".join(sin_configurar)
            + ". Hasta que este hecho, el agente no sabe de que va tu canal y "
              "dara consejos genericos. Ver el paso 3 del README.")
    else:
        lineas.append("Configuracion: personalizada")

    # Proveedor de imagen — la rama visual no arranca sin uno vivo
    prov_cfg = CONFIG_DIR / "image_providers.json"
    if prov_cfg.exists():
        try:
            pc = json.loads(prov_cfg.read_text(encoding="utf-8"))
            prov = pc.get("provider")
            if prov == "fal":
                tiene = bool(os.environ.get(
                    pc["fal"].get("key_env", "FAL_KEY"), "").strip())
                lineas.append(f"Imagen: proveedor fal.ai — "
                              f"{'clave OK' if tiene else 'SIN CLAVE'}")
                if not tiene:
                    avisos.append(
                        "No hay FAL_KEY: la rama visual solo funciona en "
                        "--dry-run. Ejecuta ~/.claude/scripts/set-fal-key.sh y "
                        "abre una sesion nueva.")
                sin_slug = [k for k in ("generate", "edit")
                            if not pc["fal"]["modelos"].get(k)]
                if sin_slug:
                    avisos.append(
                        f"Slugs de modelo sin resolver: {', '.join(sin_slug)}. "
                        "Se usara el respaldo gpt-image-2; para Nano Banana 2 hay "
                        "que apuntar el slug en config/image_providers.json.")
            else:
                lineas.append(f"Imagen: proveedor {prov} (via MCP) — "
                              "la tool devuelve la llamada, no genera")
        except Exception:  # noqa: BLE001
            lineas.append("Imagen: configuracion ilegible")

    # Caché
    try:
        c = cache.estado()
        lineas.append(f"Cache: {c['entradas']} entradas {c['familias'] or ''}")
    except Exception:  # noqa: BLE001
        pass

    if avisos:
        lineas.append("\nAvisos:")
        lineas += [f"  - {a}" for a in avisos if a]

    lineas.append(f"\nContrato: {BASE_DIR / 'CLAUDE.md'} · "
                  f"Herramientas: {BASE_DIR / 'TOOLS.md'} · "
                  f"Limites: {BASE_DIR / 'LIMITES.md'}")
    print("\n".join(lineas))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001 — un hook nunca debe romper la sesion
        print(f"[init] No se pudo componer el estado: {e}")
