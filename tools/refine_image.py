#!/usr/bin/env python3
"""Edita una imagen que ya existe, en vez de generar una nueva.

La diferencia con `generate_image` no es cosmética. Si una imagen que ya está
casi bien se pasa como *referencia* a un generador, el modelo dibuja otra imagen
parecida y se pierde lo que funcionaba. Aquí la imagen va como **origen de la
edición**, y el modelo solo cambia lo que se le pide.

Si lo que hace falta es cambiar tamaño, recorte o peso, esto no es la
herramienta: es `export_image.py`, que no gasta créditos.
"""
import json
from pathlib import Path

from lib import base  # noqa: F401
from lib import imagegen as ig
from lib.contrato import (EXIT_NO_DATA, SOURCE_CONFIG, SOURCE_GENERATED, ToolError,
                          emitir, main, parser, sobre)

TOOL = "refine_image"


def run():
    p = parser(__doc__)
    p.add_argument("--image", required=True,
                   help="imagen a editar: ruta local, URL o video_id")
    p.add_argument("--instruction", required=True,
                   help="qué cambiar, en imperativo y solo eso")
    p.add_argument("--type", default="preserve", dest="tipo", choices=list(ig.SPEC),
                   help="por defecto `preserve`: mantiene la forma del original. "
                        "Solo se cambia si se ha pedido cambiar la forma")
    p.add_argument("--ref", action="append", default=[], metavar="ORIGEN:ROL",
                   help="referencia extra, típicamente la foto de likeness")
    p.add_argument("--model", help="slug del modelo de edición")
    p.add_argument("--provider", choices=["fal", "mcp"])
    p.add_argument("--out")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    cfg = ig.cargar()
    if args.tipo != "preserve":
        ig.validar_ratio(cfg, args.tipo)
    refs = ig.ordenar_refs([ig.parsear_ref(r, cfg) for r in args.ref], cfg)

    # El prompt de una edición no describe la imagen entera: describe el cambio.
    # Describirla entera es lo que hace que el modelo la redibuje.
    prompt = ig.componer_prompt(args.tipo, (
        f"Edit the source image: {args.instruction}. "
        "Keep everything else in the source image exactly as it is."), refs)
    prov = ig.proveedor(cfg, args.provider)
    params = {"image": args.image, "tipo": args.tipo, "provider": prov}

    if prov == "mcp":
        directiva = ig.directiva_mcp(cfg, "edit", prompt, refs, args.tipo)
        directiva["llamada"]["imagen_origen"] = args.image
        directiva["avisos"].append(
            "La imagen de origen va como imagen a editar, NUNCA como referencia "
            "de estilo: si va como referencia, el modelo la redibuja.")
        env = sobre(TOOL, SOURCE_CONFIG, directiva, params,
                    notas=["Esta ejecucion NO ha editado nada."])
        emitir(env, args, lambda e: base.cabecera_md(e) + "\n\n" +
               e["data"]["accion_requerida"] + "\n\n```json\n" +
               json.dumps(e["data"]["llamada"], ensure_ascii=False, indent=2) + "\n```")

    slug = ig.modelo(cfg, "edit", args.model)

    ig.avisar_si_repetida(slug, args.tipo, prompt)

    if args.dry_run:
        env = sobre(TOOL, SOURCE_CONFIG,
                    {"modo": "dry-run", "modelo": slug, "origen": args.image,
                     "prompt_final": prompt}, params,
                    notas=ig.AVISOS + [
                        "Dry-run: no se ha llamado a fal.ai, no hay coste."])
        emitir(env, args, lambda e: base.cabecera_md(e) +
               f"\n\n**Modelo**: `{e['data']['modelo']}`\n\n**Prompt final**\n\n> " +
               e["data"]["prompt_final"])

    key = ig.clave_fal(cfg)
    origen_url = ig.referencia_url(args.image, cfg, key)
    # `image_url` es la imagen a editar. `image_urls` son las referencias
    # adicionales, y el origen NO se repite ahí: mandarlo dos veces hace que
    # algunos modelos lo traten como dos entradas y mezclen la imagen consigo
    # misma.
    payload = {"prompt": prompt, "image_url": origen_url}
    if args.tipo != "preserve":
        payload.update(ig.tamanio_payload(cfg, args.tipo))
    extra = [ig.referencia_url(r["origen"], cfg, key) for r in refs]
    if extra:
        payload["image_urls"] = extra

    respuesta = ig.encolar(slug, payload, cfg, key)
    salidas = ig.urls_de(respuesta)
    if not salidas:
        raise ToolError(f"El modelo no devolvio ninguna imagen: {respuesta}",
                        EXIT_NO_DATA)

    destino = Path(args.out) if args.out else ig.ruta_salida(TOOL, args.tipo)
    ig.descargar(salidas[0], destino)

    ig.anotar(TOOL, slug, args.tipo, prompt, destino, refs)

    env = sobre(TOOL, SOURCE_GENERATED, {
        "fichero": str(destino), "origen": args.image, "modelo": slug,
        "proveedor": "fal.ai", "instruccion": args.instruction,
        "prompt_final": prompt,
    }, params, notas=ig.AVISOS + [
        f"Imagen editada por {slug} via fal.ai. Al entregarla, nombrar el modelo.",
        "Compara el resultado con el origen ABRIENDO ambos: un modelo de edicion "
        "a veces cambia cosas que no se le pidieron.",
    ])
    emitir(env, args, lambda e: base.cabecera_md(e) +
           f"\n\n`{e['data']['fichero']}`\n\nModelo: `{e['data']['modelo']}`")


if __name__ == "__main__":
    main(TOOL, run)
