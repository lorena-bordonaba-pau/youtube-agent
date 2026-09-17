#!/usr/bin/env python3
"""Genera una imagen con el proveedor configurado (fal.ai o un MCP).

Agnóstica al proveedor: la skill pide una imagen, no un modelo. El formato
(`--type`) antepone al prompt los requisitos técnicos del sitio donde va la
imagen — la zona segura móvil del banner, el recorte circular del perfil, el
"no hagas un tríptico" del 9:16 — porque sin eso el modelo los ignora.

Lo que sale de aquí es `source: generated`: un artefacto, no una medición.
No dice nada sobre cómo va a rendir.
"""
import json
from pathlib import Path

from lib import base  # noqa: F401
from lib import imagegen as ig
from lib.contrato import SOURCE_CONFIG, SOURCE_GENERATED, emitir, main, parser, sobre

TOOL = "generate_image"


def run():
    p = parser(__doc__)
    p.add_argument("--prompt", required=True, help="qué se quiere ver en la imagen")
    p.add_argument("--type", default="thumbnail", dest="tipo",
                   choices=list(ig.SPEC), help="destino de la imagen")
    p.add_argument("--ref", action="append", default=[], metavar="ORIGEN:ROL",
                   help="referencia: ruta, URL o video_id, más su rol "
                        "(likeness|style|composition|packaging). Repetible, máx 3")
    p.add_argument("--model", help="slug del modelo; por defecto el de la config")
    p.add_argument("--provider", choices=["fal", "mcp"], help="fuerza proveedor")
    p.add_argument("--out", help="ruta de salida; por defecto datos/imagenes/")
    p.add_argument("--dry-run", action="store_true",
                   help="muestra el prompt final sin gastar créditos")
    args = p.parse_args()

    cfg = ig.cargar()
    ig.validar_ratio(cfg, args.tipo)
    refs = ig.ordenar_refs([ig.parsear_ref(r, cfg) for r in args.ref], cfg)
    prompt = ig.componer_prompt(args.tipo, args.prompt, refs)
    formato = cfg["formatos"][args.tipo]
    prov = ig.proveedor(cfg, args.provider)
    params = {"tipo": args.tipo, "provider": prov,
              "refs": [f"{r['origen']}:{r['rol']}" for r in refs]}

    if prov == "mcp":
        env = sobre(TOOL, SOURCE_CONFIG,
                    ig.directiva_mcp(cfg, "generate", prompt, refs, args.tipo),
                    params, notas=["Esta ejecucion NO ha generado ninguna imagen."])
        emitir(env, args, lambda e: base.cabecera_md(e) + "\n\n" +
               e["data"]["accion_requerida"] + "\n\n```json\n" +
               json.dumps(e["data"]["llamada"], ensure_ascii=False, indent=2) +
               "\n```")

    slug = ig.modelo(cfg, "generate", args.model)

    ig.avisar_si_repetida(slug, args.tipo, prompt)

    if args.dry_run:
        env = sobre(TOOL, SOURCE_CONFIG, {
            "modo": "dry-run", "modelo": slug, "formato": formato,
            "prompt_final": prompt,
            "referencias": [r["origen"] for r in refs],
        }, params, notas=ig.AVISOS + [
            "Dry-run: no se ha llamado a fal.ai, no hay coste."])
        emitir(env, args, lambda e: base.cabecera_md(e) +
               f"\n\n**Modelo**: `{e['data']['modelo']}`\n\n**Prompt final**\n\n> " +
               e["data"]["prompt_final"])

    key = ig.clave_fal(cfg)
    urls = [ig.referencia_url(r["origen"], cfg, key) for r in refs]

    payload = {"prompt": prompt, **ig.tamanio_payload(cfg, args.tipo)}
    if urls:
        payload["image_urls"] = urls

    respuesta = ig.encolar(slug, payload, cfg, key)
    salidas = ig.urls_de(respuesta)
    if not salidas:
        from lib.contrato import EXIT_NO_DATA, ToolError
        raise ToolError(f"El modelo no devolvio ninguna imagen: {respuesta}",
                        EXIT_NO_DATA)

    destino = Path(args.out) if args.out else ig.ruta_salida(TOOL, args.tipo)
    ig.descargar(salidas[0], destino)

    # El modelo no siempre respeta la proporción pedida: nano-banana devuelve
    # 1024x1024 aunque se le pida 16:9. Se comprueba en el fichero y, si el
    # formato la tiene fija, se recorta. "Siempre 16:9" tiene que ser cierto en
    # el pixel, no solo en el prompt.
    devuelto, corregido = ig.verificar_proporcion(destino, cfg, args.tipo)
    if corregido:
        destino = corregido

    ig.anotar(TOOL, slug, args.tipo, prompt, destino, refs)

    env = sobre(TOOL, SOURCE_GENERATED, {
        "fichero": str(destino),
        "modelo": slug,
        "proveedor": "fal.ai",
        "tipo": args.tipo,
        "formato_objetivo": formato,
        "prompt_final": prompt,
        "resolucion_devuelta": devuelto,
        "referencias": [f"{r['origen']} ({r['rol']})" for r in refs],
        "extra": salidas[1:],
    }, params, notas=ig.AVISOS + [
        f"Imagen generada por {slug} via fal.ai. Al entregarla, nombrar el modelo.",
        "NO es una prediccion de nada. Para juzgarla hay que abrirla con vision.",
        f"Para ajustar dimensiones exactas sin gastar creditos: "
        f"python3 tools/export_image.py --image {destino} --type {args.tipo}",
    ])
    emitir(env, args, lambda e: base.cabecera_md(e) +
           f"\n\n`{e['data']['fichero']}`\n\nModelo: `{e['data']['modelo']}`")


if __name__ == "__main__":
    main(TOOL, run)
