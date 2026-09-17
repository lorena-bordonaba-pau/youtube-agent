#!/usr/bin/env python3
"""Fit an image to the exact dimensions of a target format.

Deterministic and local: resizes, crops and re-compresses with PIL. **It calls
no model, spends no credits and redraws nothing.** To resize an image that is
already good you do not generate again: you export.

YouTube rejects thumbnails over 2 MB; this is the step that avoids that
without repeating the generation.
"""
from pathlib import Path

from PIL import Image

from lib import base  # noqa: F401
from lib.contract import (EXIT_NO_DATA, SOURCE_DERIVED, ToolError, emit, main,
                          parser, envelope)
from lib.imagegen import load, output_path

TOOL = "export_image"


def encajar(img: Image.Image, width: int, height: int) -> Image.Image:
    """Centre-crop to the target ratio, then scale.

    Cropping happens before scaling so nothing is distorted: a stretched
    thumbnail is immediately obvious on a face.
    """
    target = width / height
    w, h = img.size
    current = w / h
    if abs(current - target) > 0.01:
        if current > target:                      # sobra anchura
            nuevo_w = int(h * target)
            izq = (w - nuevo_w) // 2
            img = img.crop((izq, 0, izq + nuevo_w, h))
        else:                                      # sobra altura
            nuevo_h = int(w / target)
            arriba = (h - nuevo_h) // 2
            img = img.crop((0, arriba, w, arriba + nuevo_h))
    return img.resize((width, height), Image.LANCZOS)


def guardar_bajo_limite(img: Image.Image, dest: Path,
                        max_bytes: int | None) -> tuple[dict, Path]:
    """Save, and if it exceeds the limit drop quality until it fits.

    Also returns the final path, which may not be the one asked for: a PNG
    with a size limit becomes a JPG, because PNG has no quality lever.
    """
    attempts = []
    # PNG has no quality lever: if there is a size limit and the PNG does not
    # fit, the only real fix is changing format. YouTube accepts JPG anyway.
    if (max_bytes and dest.suffix.lower() == ".png"):
        dest = dest.with_suffix(".jpg")
    if dest.suffix.lower() in (".jpg", ".jpeg"):
        img = img.convert("RGB")
        for quality in (95, 90, 85, 80, 72, 65, 55):
            img.save(dest, "JPEG", quality=quality, optimize=True)
            tam = dest.stat().st_size
            attempts.append({"quality": quality, "bytes": tam})
            if max_bytes is None or tam <= max_bytes:
                break
    else:
        img.save(dest, optimize=True)
        attempts.append({"quality": None, "bytes": dest.stat().st_size})
    return {"attempts": attempts, "final_bytes": dest.stat().st_size}, dest


def run():
    p = parser(__doc__)
    p.add_argument("--image", required=True, help="path to the source image")
    p.add_argument("--type", dest="kind", help="target format from the config")
    p.add_argument("--size", help="explicit AxB, when not using --type")
    p.add_argument("--out", help="output path; .jpg or .png decides the format")
    p.add_argument("--max-bytes", type=int, help="override the format's byte limit")
    args = p.parse_args()

    origin = Path(args.image)
    if not origin.exists():
        raise ToolError(f"No exists {origin}", EXIT_NO_DATA)
    if not args.kind and not args.size:
        raise ToolError("Hace missing --type o --size", EXIT_NO_DATA,
                        "Ej: --type thumbnail  |  --size 1280x720")

    cfg = load()
    if args.kind:
        if args.kind not in cfg["formats"]:
            raise ToolError(f"Formato desconocido: {args.kind}", EXIT_NO_DATA,
                            f"Validos: {list(cfg['formats'])}")
        fmt = cfg["formats"][args.kind]
        width, height = (int(x) for x in fmt["px"].split("x"))
        max_bytes = args.max_bytes or fmt.get("max_bytes")
    else:
        width, height = (int(x) for x in args.size.lower().split("x"))
        max_bytes = args.max_bytes

    dest = Path(args.out) if args.out else output_path(
        TOOL, args.kind or f"{width}x{height}", "jpg")

    img = Image.open(origin)
    original = {"resolution": f"{img.size[0]}x{img.size[1]}",
                "bytes": origin.stat().st_size}
    result, dest = guardar_bajo_limite(encajar(img, width, height), dest,
                                             max_bytes)

    dentro = max_bytes is None or result["final_bytes"] <= max_bytes
    env = envelope(TOOL, SOURCE_DERIVED, {
        "origin": str(origin), "file": str(dest),
        "original": original,
        "resolution": f"{width}x{height}",
        "byte_limit": max_bytes,
        "within_limit": dentro,
        **result,
    }, {"image": str(origin), "type": args.kind, "size": args.size},
        notes=[
            "Local, deterministic operation: no model, no credits.",
            "It centre-crops before scaling to avoid distortion. If the subject "
            "is off-centre, crop it yourself with --size and check the result.",
    ] + ([] if dentro else [
            f"STILL OVER THE LIMIT ({result['final_bytes']} > {max_bytes}). "
            "Lower the resolution or simplify the image."]))
    emit(env, args, lambda e: base.md_header(e) +
           f"\n\n`{e['data']['file']}` — {e['data']['resolution']}, "
           f"{e['data']['final_bytes']} bytes")


if __name__ == "__main__":
    main(TOOL, run)
