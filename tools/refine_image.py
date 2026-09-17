#!/usr/bin/env python3
"""Edit an image that already exists, instead of generating a new one.

The difference from `generate_image` is not cosmetic. If an image that is
already nearly right is passed as a *reference* to a generator, the model
draws another similar image and whatever was working is lost. Here the image
goes in as the **edit source**, and the model changes only what it is told to.

If what you need is a different size, crop or file weight, this is not the
tool: that is `export_image.py`, which spends no credits.
"""
import json
from pathlib import Path

from lib import base  # noqa: F401
from lib import imagegen as ig
from lib.contract import (EXIT_NO_DATA, SOURCE_CONFIG, SOURCE_GENERATED, ToolError,
                          emit, main, parser, envelope)

TOOL = "refine_image"


def run():
    p = parser(__doc__)
    p.add_argument("--image", required=True,
                   help="the image to edit: local path, URL or video_id")
    p.add_argument("--instruction", required=True,
                   help="what to change, imperative, and only that")
    p.add_argument("--type", default="preserve", dest="kind", choices=list(ig.SPEC),
                   help="defaults to `preserve`: keeps the original's shape. "
                        "Only change it when a new shape was asked for")
    p.add_argument("--ref", action="append", default=[], metavar="ORIGEN:ROL",
                   help="extra reference, typically the likeness photo")
    p.add_argument("--model", help="slug of the editing model")
    p.add_argument("--provider", choices=["fal", "mcp"])
    p.add_argument("--out")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    cfg = ig.load()
    if args.kind != "preserve":
        ig.validate_ratio(cfg, args.kind)
    refs = ig.sort_refs([ig.parse_ref(r, cfg) for r in args.ref], cfg)

    # An edit prompt does not describe the whole image: it describes the
    # change. Describing the whole thing is what makes the model redraw it.
    prompt = ig.compose_prompt(args.kind, (
        f"Edit the source image: {args.instruction}. "
        "Keep everything else in the source image exactly as it is."), refs)
    provider = ig.provider_name(cfg, args.provider)
    params = {"image": args.image, "kind": args.kind, "provider": provider}

    if provider == "mcp":
        directiva = ig.mcp_directive(cfg, "edit", prompt, refs, args.kind)
        directiva["call"]["imagen_origen"] = args.image
        directiva["warnings"].append(
            "The source image goes in as the image to edit, NEVER as a style "
            "reference: as a reference, the model redraws it.")
        env = envelope(TOOL, SOURCE_CONFIG, directiva, params,
                    notes=["This run has NOT edited anything."])
        emit(env, args, lambda e: base.md_header(e) + "\n\n" +
               e["data"]["action_required"] + "\n\n```json\n" +
               json.dumps(e["data"]["call"], ensure_ascii=False, indent=2) + "\n```")

    slug = ig.model_slug(cfg, "edit", args.model)

    ig.warn_if_repeated(slug, args.kind, prompt)

    if args.dry_run:
        env = envelope(TOOL, SOURCE_CONFIG,
                    {"mode": "dry-run", "model_slug": slug, "origin": args.image,
                     "final_prompt": prompt}, params,
                    notes=ig.WARNINGS + [
                        "Dry run: fal.ai was not called, there is no cost."])
        emit(env, args, lambda e: base.md_header(e) +
               f"\n\n**Modelo**: `{e['data']['model_slug']}`\n\n**Prompt final**\n\n> " +
               e["data"]["final_prompt"])

    key = ig.fal_key(cfg)
    source_url = ig.reference_url(args.image, cfg, key)
    # `image_url` is the image to edit. `image_urls` are the extra references,
    # and the source is NOT repeated there: sending it twice makes some models
    # treat it as two inputs and blend the image with itself.
    payload = {"prompt": prompt, "image_url": source_url}
    if args.kind != "preserve":
        payload.update(ig.size_payload(cfg, args.kind))
    extra = [ig.reference_url(r["origin"], cfg, key) for r in refs]
    if extra:
        payload["image_urls"] = extra

    response = ig.enqueue(slug, payload, cfg, key)
    outputs = ig.urls_from(response)
    if not outputs:
        raise ToolError(f"The model returned no image: {response}",
                        EXIT_NO_DATA)

    dest = Path(args.out) if args.out else ig.output_path(TOOL, args.kind)
    ig.download(outputs[0], dest)

    ig.log_generation(TOOL, slug, args.kind, prompt, dest, refs)

    env = envelope(TOOL, SOURCE_GENERATED, {
        "file": str(dest), "origin": args.image, "model_slug": slug,
        "provider_name": "fal.ai", "instruction": args.instruction,
        "final_prompt": prompt,
    }, params, notes=ig.WARNINGS + [
        f"Image edited by {slug} via fal.ai. Name the model when delivering it.",
        "Compare the result with the source by OPENING both: an editing model "
        "sometimes changes things it was not asked to.",
    ])
    emit(env, args, lambda e: base.md_header(e) +
           f"\n\n`{e['data']['file']}`\n\nModelo: `{e['data']['model_slug']}`")


if __name__ == "__main__":
    main(TOOL, run)
