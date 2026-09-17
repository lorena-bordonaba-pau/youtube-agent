#!/usr/bin/env python3
"""Descarga el avatar y el banner de un canal y mide su pixel.

Es el paso previo a generar packaging nuevo: sin ver la marca actual, lo que se
genere será genérico o romperá la identidad que ya existe.

Las métricas son objetivas. La lectura de marca — qué transmite, qué falla — la
hace el agente abriendo los ficheros con visión.
"""
from pathlib import Path

from lib import auth, base  # noqa: F401
from lib import cache
from lib.contrato import (DATOS_DIR, EXIT_NO_DATA, SOURCE_DERIVED, ToolError,
                          emitir, main, parser, sobre)
from lib.imagegen import descargar
from yt_thumbnails import metricas

TOOL = "view_channel_packaging"
DIR = DATOS_DIR / "packaging"


def paquete(channel_id: str | None) -> dict:
    yt = auth.youtube()
    parts = "snippet,brandingSettings"
    req = (yt.channels().list(part=parts, mine=True) if channel_id is None
           else yt.channels().list(part=parts, id=channel_id))
    items = req.execute().get("items", [])
    if not items:
        raise ToolError(f"Canal no encontrado: {channel_id or 'propio'}", EXIT_NO_DATA)
    c = items[0]
    thumbs = c["snippet"].get("thumbnails", {})
    mejor = thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}
    return {
        "channel_id": c["id"],
        "title": c["snippet"]["title"],
        "avatar_url": mejor.get("url"),
        "banner_url": (c.get("brandingSettings", {})
                       .get("image", {}).get("bannerExternalUrl")),
        "keywords": c.get("brandingSettings", {}).get("channel", {}).get("keywords"),
    }


def run():
    p = parser(__doc__)
    p.add_argument("--channel", help="channel_id; omitir para el canal propio")
    p.add_argument("--only", choices=["avatar", "banner", "both"], default="both")
    args = p.parse_args()

    propio = args.channel is None
    familia = "analitica_propia" if propio else "canal_ajeno"
    info, hit = cache.memo(familia, f"{TOOL}:{args.channel or 'mine'}",
                           lambda: paquete(args.channel), not args.no_cache)

    DIR.mkdir(parents=True, exist_ok=True)
    cid = info["channel_id"]
    piezas = []
    objetivo = {"avatar": ["avatar"], "banner": ["banner"],
                "both": ["avatar", "banner"]}[args.only]

    for pieza in objetivo:
        url = info.get(f"{pieza}_url")
        if not url:
            piezas.append({"pieza": pieza, "estado": "el canal no tiene"})
            continue
        # El banner se sirve recortado por defecto; =w2560 pide el original.
        if pieza == "banner":
            url = f"{url}=w2560-fcrop64=1,00000000ffffffff-k-c0xffffffff-no-nd-rj"
        destino = DIR / f"{cid}_{pieza}.jpg"
        try:
            if not destino.exists():
                descargar(url, destino)
            piezas.append({"pieza": pieza, "estado": "ok", **metricas(destino)})
        except Exception as e:  # noqa: BLE001 — una pieza rota no tumba la otra
            piezas.append({"pieza": pieza, "estado": f"no descargada: {e}"})

    env = sobre(TOOL, SOURCE_DERIVED,
                {**info, "piezas": piezas}, {"channel": args.channel or "mine"}, hit,
                notas=[
                    "Metricas de pixel, no juicio de marca.",
                    "Para leer la identidad visual, ABRE los ficheros de `fichero` "
                    "con la herramienta de lectura de imagenes.",
                    "El banner se juzga por su banda central: en movil se recorta "
                    "el tercio superior y el inferior.",
                ])
    emitir(env, args, lambda e: base.cabecera_md(e) +
           f"\n\n**{e['data']['title']}** — `{e['data']['channel_id']}`\n\n" +
           base.tabla_md(e["data"]["piezas"],
                         ["pieza", "estado", "resolucion", "contraste_global",
                          "saturacion_media", "fichero"]))


if __name__ == "__main__":
    main(TOOL, run)
