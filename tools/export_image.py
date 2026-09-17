#!/usr/bin/env python3
"""Ajusta una imagen a las dimensiones exactas del formato de destino.

Determinista y local: redimensiona, recorta y recomprime con PIL. **No llama a
ningún modelo, no gasta créditos y no redibuja nada.** Para cambiar el tamaño
de una imagen que ya está bien no se vuelve a generar: se exporta.

YouTube rechaza miniaturas de más de 2 MB; este es el paso que evita ese
rechazo sin repetir la generación.
"""
from pathlib import Path

from PIL import Image

from lib import base  # noqa: F401
from lib.contrato import (EXIT_NO_DATA, SOURCE_DERIVED, ToolError, emitir, main,
                          parser, sobre)
from lib.imagegen import cargar, ruta_salida

TOOL = "export_image"


def encajar(img: Image.Image, ancho: int, alto: int) -> Image.Image:
    """Recorta al ratio de destino por el centro y luego escala.

    Se recorta antes de escalar para no deformar: una miniatura estirada se
    nota inmediatamente en una cara.
    """
    objetivo = ancho / alto
    w, h = img.size
    actual = w / h
    if abs(actual - objetivo) > 0.01:
        if actual > objetivo:                      # sobra anchura
            nuevo_w = int(h * objetivo)
            izq = (w - nuevo_w) // 2
            img = img.crop((izq, 0, izq + nuevo_w, h))
        else:                                      # sobra altura
            nuevo_h = int(w / objetivo)
            arriba = (h - nuevo_h) // 2
            img = img.crop((0, arriba, w, arriba + nuevo_h))
    return img.resize((ancho, alto), Image.LANCZOS)


def guardar_bajo_limite(img: Image.Image, destino: Path,
                        max_bytes: int | None) -> tuple[dict, Path]:
    """Guarda, y si excede el límite baja calidad hasta entrar.

    Devuelve también la ruta final, que puede no ser la pedida: un PNG con
    límite de peso se convierte a JPG, porque PNG no tiene con qué comprimir.
    """
    intentos = []
    # PNG no tiene palanca de calidad: si hay límite de peso y el PNG no cabe,
    # el único arreglo real es cambiar de formato. YouTube acepta JPG igual.
    if (max_bytes and destino.suffix.lower() == ".png"):
        destino = destino.with_suffix(".jpg")
    if destino.suffix.lower() in (".jpg", ".jpeg"):
        img = img.convert("RGB")
        for calidad in (95, 90, 85, 80, 72, 65, 55):
            img.save(destino, "JPEG", quality=calidad, optimize=True)
            tam = destino.stat().st_size
            intentos.append({"calidad": calidad, "bytes": tam})
            if max_bytes is None or tam <= max_bytes:
                break
    else:
        img.save(destino, optimize=True)
        intentos.append({"calidad": None, "bytes": destino.stat().st_size})
    return {"intentos": intentos, "bytes_final": destino.stat().st_size}, destino


def run():
    p = parser(__doc__)
    p.add_argument("--image", required=True, help="ruta de la imagen de origen")
    p.add_argument("--type", dest="tipo", help="formato de destino de la config")
    p.add_argument("--size", help="AxB explícito, si no se usa --type")
    p.add_argument("--out", help="ruta de salida; .jpg o .png decide el formato")
    p.add_argument("--max-bytes", type=int, help="sobrescribe el límite del formato")
    args = p.parse_args()

    origen = Path(args.image)
    if not origen.exists():
        raise ToolError(f"No existe {origen}", EXIT_NO_DATA)
    if not args.tipo and not args.size:
        raise ToolError("Hace falta --type o --size", EXIT_NO_DATA,
                        "Ej: --type thumbnail  |  --size 1280x720")

    cfg = cargar()
    if args.tipo:
        if args.tipo not in cfg["formatos"]:
            raise ToolError(f"Formato desconocido: {args.tipo}", EXIT_NO_DATA,
                            f"Validos: {list(cfg['formatos'])}")
        fmt = cfg["formatos"][args.tipo]
        ancho, alto = (int(x) for x in fmt["px"].split("x"))
        max_bytes = args.max_bytes or fmt.get("max_bytes")
    else:
        ancho, alto = (int(x) for x in args.size.lower().split("x"))
        max_bytes = args.max_bytes

    destino = Path(args.out) if args.out else ruta_salida(
        TOOL, args.tipo or f"{ancho}x{alto}", "jpg")

    img = Image.open(origen)
    original = {"resolucion": f"{img.size[0]}x{img.size[1]}",
                "bytes": origen.stat().st_size}
    resultado, destino = guardar_bajo_limite(encajar(img, ancho, alto), destino,
                                             max_bytes)

    dentro = max_bytes is None or resultado["bytes_final"] <= max_bytes
    env = sobre(TOOL, SOURCE_DERIVED, {
        "origen": str(origen), "fichero": str(destino),
        "original": original,
        "resolucion": f"{ancho}x{alto}",
        "limite_bytes": max_bytes,
        "dentro_del_limite": dentro,
        **resultado,
    }, {"image": str(origen), "type": args.tipo, "size": args.size},
        notas=[
            "Operacion local y determinista: sin modelo, sin creditos.",
            "Se recorta por el centro antes de escalar para no deformar. Si el "
            "sujeto no esta centrado, recorta tu con --size y revisa el resultado.",
    ] + ([] if dentro else [
            f"SIGUE POR ENCIMA DEL LIMITE ({resultado['bytes_final']} > {max_bytes}). "
            "Baja la resolucion o simplifica la imagen."]))
    emitir(env, args, lambda e: base.cabecera_md(e) +
           f"\n\n`{e['data']['fichero']}` — {e['data']['resolucion']}, "
           f"{e['data']['bytes_final']} bytes")


if __name__ == "__main__":
    main(TOOL, run)
