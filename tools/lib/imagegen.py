"""Image generation adapter, agnostic to the provider.

No skill ever names a provider. They ask for an image; this module decides
whether to request it from fal.ai over REST or to hand back a directive for the
agent to call an MCP. You switch providers in `config/image_providers.json`.

Two hard rules:

1. **Model slugs are never invented.** If the requested model is `null` in the
   config, the tool fails with instructions instead of guessing. A made-up slug
   burns credits and returns 404 — or worse, generates with a different model.
2. **A generated image is never data.** Everything leaving here carries
   `source: generated`, which the contract translates to "artefact, not a
   measurement".
"""
from __future__ import annotations

import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import base  # noqa: F401 — importing it loads .env
from .contract import (CONFIG_DIR, DATA_DIR, EXIT_AUTH, EXIT_NO_DATA, ToolError)

CONFIG = CONFIG_DIR / "image_providers.json"
OUTPUT_DIR = DATA_DIR / "images"

# Format rules prepended to the prompt. Not style: technical requirements of
# the place the image is going, and if they are not in the prompt the model
# ignores them. The banner's mobile safe zone is the one people forget most.
SPEC = {
    "thumbnail": (
        "Wide 16:9 horizontal image for a YouTube video thumbnail. "
        "Fill the ENTIRE frame edge to edge. Absolutely no letterboxing, no "
        "black bars at the top or bottom, no cinematic bars, no borders, no "
        "frames, no padding: the photographed content must reach all four "
        "edges of the image. "
        "Must stay legible when scaled down to roughly 160 pixels wide."
    ),
    "profile_image": (
        "Square 1:1 image for a channel profile picture. Centre the main "
        "subject: the platform crops it to a circle, so anything near the "
        "corners is lost. Simple background. Must stay recognisable at 32x32 "
        "pixels, so no text and no fine detail."
    ),
    "banner": (
        "Exactly 2560x1440 pixels, YouTube channel banner. "
        "CRITICAL COMPOSITION RULE: only a narrow horizontal band across the "
        "vertical centre is visible on mobile; the upper and lower thirds are "
        "cropped away entirely. Place ALL important content (text, logos, "
        "channel name, faces, key branding) strictly within that narrow middle "
        "band. Upper and lower portions must contain ONLY simple backgrounds "
        "(gradients, blurs, patterns, solid colours)."
    ),
    # `preserve` imposes no shape: used when EDITING, where changing the
    # original's aspect ratio is never what was asked unless it is said.
    "preserve": (
        "Keep the exact same dimensions and aspect ratio as the source image. "
        "Do not reframe, do not crop, do not letterbox."
    ),
    "general": (
        "Wide 16:9 horizontal image. Fill the ENTIRE frame edge to edge, with "
        "no letterboxing, no black bars and no borders."
    ),
}

# Prepended to any prompt carrying a likeness reference. This is the sentence
# that stops the model returning "someone who looks a bit like them".
LIKENESS = (
    "Use the EXACT facial identity and likeness of the person in "
    "{label} — this must be recognisably the same individual, not merely "
    "someone who looks similar and not an AI-generated lookalike. Do not alter "
    "their facial features. Never crop at the neck: include the upper body."
)


def load() -> dict:
    if not CONFIG.exists():
        raise ToolError(f"Falta {CONFIG}", EXIT_NO_DATA)
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)


def provider_name(cfg: dict, requested: str | None = None) -> str:
    p = requested or cfg.get("provider", "fal")
    if p not in ("fal", "mcp"):
        raise ToolError(f"Proveedor desconocido: {p}", EXIT_NO_DATA,
                        "Valid: fal, mcp. Set it in image_providers.json")
    return p


def model_slug(cfg: dict, action: str, requested: str | None = None) -> str:
    """Resolve the model slug. Fails rather than inventing one."""
    if requested:
        return requested
    models = cfg["fal"]["models"]
    slug = models.get(action)
    if slug:
        return slug
    alt = models.get(f"{action}_gpt")
    if alt:
        return alt
    raise ToolError(
        f"No model slug configured for action '{action}'.",
        EXIT_NO_DATA,
        "Find the model at https://fal.ai/explore/models and write its slug into "
        f"config/image_providers.json (fal.models.{action}), o pasa --model. "
        "This tool refuses to guess slugs on purpose: a made-up one burns credits.",
    )


# Warnings the tool accumulates so they travel inside the envelope, not a log.
WARNINGS: list[str] = []


def fal_key(cfg: dict) -> str:
    """Return the fal key, correcting a double paste.

    Key prompts usually hide what you type, so pasting twice is invisible and
    leaves the key written twice, which returns 401. Only the exact case is
    detected — even length and two identical halves — and the first half is
    used, leaving a visible warning. Nothing else is corrected: a key that is
    simply wrong is never guessed at.
    """
    env = cfg["fal"].get("key_env", "FAL_KEY")
    key = os.environ.get(env, "").strip()
    if not key:
        raise ToolError(
            f"{env} is not set in the environment.",
            EXIT_AUTH,
            "Set it in your .env (see .env.example) and start a new session. "
            "Get a key at https://fal.ai/dashboard/keys",
        )
    half = len(key) // 2
    if len(key) % 2 == 0 and half > 8 and key[:half] == key[half:]:
        WARNINGS.append(
            f"{env} is stored TWICE ({len(key)} characters instead of "
            f"{half}). The first half was used so the call works, but "
            "conviene arreglarla: ejecuta ~/.claude/scripts/set-fal-key.sh y "
            "paste the key ONCE (the field is hidden, which is why a double "
            "paste is invisible).")
        return key[:half]
    return key


def _request(url: str, key: str, payload_data: bytes | None = None,
              content_type: str = "application/json", method: str | None = None):
    req = urllib.request.Request(url, data=payload_data, method=method)
    req.add_header("Authorization", f"Key {key}")
    if payload_data is not None:
        req.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read()
            if r.headers.get("Content-Type", "").startswith("application/json"):
                return json.loads(body)
            return body
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        raise ToolError(f"fal.ai devolvio {e.code}: {detail}", EXIT_NO_DATA,
                        "If it is a 404 the model slug does not exist: check it at "
                        "https://fal.ai/explore/models") from e


def upload_file(path: Path, cfg: dict, key: str) -> str:
    """Upload a local file to fal storage and return its public URL.

    It is **two steps**, not one: ask `/storage/upload/initiate` for a signed
    URL, then `PUT` the bytes to it. Verified 2026-09-17; an earlier version
    POSTed straight to `rest.fal.run`, a host that does not even resolve.
    """
    kind = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    start = _request(
        cfg["fal"]["upload_initiate_url"], key,
        json.dumps({"content_type": kind, "file_name": path.name}).encode("utf-8"))
    if not isinstance(start, dict) or not start.get("upload_url"):
        raise ToolError(f"fal storage returned no upload_url for {path}",
                        EXIT_NO_DATA)

    req = urllib.request.Request(start["upload_url"], data=path.read_bytes(),
                                 method="PUT")
    req.add_header("Content-Type", kind)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            if r.status not in (200, 201, 204):
                raise ToolError(f"The upload returned {r.status}", EXIT_NO_DATA)
    except urllib.error.HTTPError as e:
        raise ToolError(f"Failed to upload {path.name}: {e.code}", EXIT_NO_DATA) from e

    return start["file_url"]


def reference_url(ref: str, cfg: dict, key: str) -> str:
    """A reference can be a URL, a local file, or a YouTube video_id."""
    if ref.startswith(("http://", "https://")):
        return ref
    p = Path(ref)
    if p.exists():
        return upload_file(p, cfg, key)
    if len(ref) == 11 and "/" not in ref:   # parece un video_id
        return f"https://i.ytimg.com/vi/{ref}/maxresdefault.jpg"
    raise ToolError(f"Reference could not be resolved: {ref}", EXIT_NO_DATA,
                    "Use an existing local path, a URL, or a video_id.")


def enqueue(slug: str, payload: dict, cfg: dict, key: str) -> dict:
    """Enqueue the job, wait for it to finish, and return the response."""
    base = cfg["fal"]["queue_base"].rstrip("/")
    submission = _request(f"{base}/{slug}", key,
                      json.dumps(payload).encode("utf-8"))
    rid = submission.get("request_id")
    if not rid:
        raise ToolError(f"fal.ai returned no request_id: {submission}", EXIT_NO_DATA)

    status_url = submission.get("status_url") or f"{base}/{slug}/requests/{rid}/status"
    resp_url = submission.get("response_url") or f"{base}/{slug}/requests/{rid}"

    limit = time.time() + cfg["fal"].get("timeout_s", 300)
    wait = cfg["fal"].get("poll_s", 3)
    while time.time() < limit:
        st = _request(status_url, key)
        state = st.get("status") if isinstance(st, dict) else None
        if state == "COMPLETED":
            return _request(resp_url, key)
        if state in ("FAILED", "CANCELLED"):
            raise ToolError(f"The fal.ai job ended as {state}: {st}",
                            EXIT_NO_DATA)
        time.sleep(wait)
    raise ToolError(f"Timeout esperando a fal.ai ({rid})", EXIT_NO_DATA,
                    f"The job may still be running. Check {status_url}")


def urls_from(response: dict) -> list[str]:
    """Pull image URLs out of a fal response, tolerating schema differences."""
    out = []
    for key in ("images", "image", "output", "outputs", "data"):
        val = response.get(key) if isinstance(response, dict) else None
        if isinstance(val, dict):
            val = [val]
        if isinstance(val, list):
            for item in val:
                if isinstance(item, dict) and item.get("url"):
                    out.append(item["url"])
                elif isinstance(item, str) and item.startswith("http"):
                    out.append(item)
        elif isinstance(val, str) and val.startswith("http"):
            out.append(val)
    return out


def download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        dest.write_bytes(r.read())
    return dest


def trim_letterbox(path: Path, threshold: int = 18) -> tuple[int, int]:
    """Trim uniform black bars from the top and bottom, if there are any.

    `fal-ai/nano-banana` letterboxes its output: in the 2026-09-17 test it
    returned 1344x768 with 80px black bars top and bottom. Because the bars are
    pixels of the image, cropping to the ratio does not remove them — they have
    to be detected and trimmed first.

    Returns (pixels trimmed from the top, pixels trimmed from the bottom).
    """
    from PIL import Image

    with Image.open(path) as original:
        grey = original.convert("L")
        w, h = grey.size
        px = grey.load()

        def uniform(y: int) -> bool:
            samples = [px[x, y] for x in range(0, w, max(1, w // 80))]
            return max(samples) <= threshold

        top_edge = next((y for y in range(h) if not uniform(y)), 0)
        bottom_edge = next((y for y in range(h - 1, -1, -1) if not uniform(y)), h - 1)
        if top_edge == 0 and bottom_edge == h - 1:
            return 0, 0
        # A bar eating more than a third of the height is not letterboxing:
        # it is a genuinely dark image. Leave it alone.
        if (top_edge + (h - 1 - bottom_edge)) > h / 3:
            return 0, 0
        original.crop((0, top_edge, w, bottom_edge + 1)).save(path)
    return top_edge, h - 1 - bottom_edge


def verify_ratio(path: Path, cfg: dict, kind: str) -> tuple[str, Path | None]:
    """Check the file's aspect ratio and fix it when the format pins one.

    The prompt asks for 16:9 and the payload asks again, but the model can
    return something else: `fal-ai/nano-banana` returns 1024x1024 regardless.
    "Thumbnails are always 16:9" is only true if it is checked in the pixels,
    so here it is measured and, when needed, cropped.

    Returns (the resolution that arrived, the corrected path or None).
    """
    from PIL import Image

    with Image.open(path) as img:
        received = f"{img.size[0]}x{img.size[1]}"

    top, bottom = trim_letterbox(path)
    if top or bottom:
        WARNINGS.append(
            f"The model returned {received} WITH BLACK BARS ({top}px top, "
            f"{bottom}px bottom). They were trimmed. If this repeats, the model is "
            "ignoring the instruction to fill the frame.")

    with Image.open(path) as img:
        width, height = img.size
    returned = received if not (top or bottom) else f"{received} -> {width}x{height} bars removed"

    fmt = cfg["formats"].get(kind)
    if fmt is None:                      # `preserve`: no shape to impose
        return returned, None
    target_w, target_h = (int(x) for x in fmt["px"].split("x"))
    if abs(width / height - target_w / target_h) < 0.01:
        return returned, None
    if not fmt.get("fixed_ratio"):
        WARNINGS.append(
            f"The model returned {returned}, not {fmt['ratio']}. To force it: "
            f"python3 tools/export_image.py --image {path} --type {kind}")
        return returned, None

    # Format with a pinned ratio: fixed right here, spending no credits.
    import subprocess
    fixed_path = path.with_name(path.stem + f"_{target_w}x{target_h}.jpg")
    subprocess.run(
        ["python3", str(Path(__file__).resolve().parent.parent / "export_image.py"),
         "--image", str(path), "--type", kind, "--out", str(fixed_path)],
        check=True, capture_output=True)
    WARNINGS.append(
        f"The model returned {returned}, which is not {fmt['ratio']}. It was "
        f"centre-cropped to {target_w}x{target_h}. OPEN the file: "
        "if the subject was off-centre, the crop will have cut it.")
    return returned, fixed_path


LEDGER = OUTPUT_DIR / "ledger.jsonl"


def _fingerprint(slug: str, kind: str, prompt: str) -> str:
    import hashlib
    return hashlib.sha256(f"{slug}|{kind}|{prompt}".encode()).hexdigest()[:16]


def warn_if_repeated(slug: str, kind: str, prompt: str, hours: int = 24) -> None:
    """Warn if this same prompt was generated recently.

    Generation is not cached: asking for another take on the same prompt is
    normal, and returning the old file would be worse than charging twice.
    What this avoids is *accidental* repetition — a retry, a loop — by naming
    the file that already exists so it can be reused if it fits.
    """
    import time

    if not LEDGER.exists():
        return
    fingerprint = _fingerprint(slug, kind, prompt)
    limit = time.time() - hours * 3600
    for line in reversed(LEDGER.read_text(encoding="utf-8").splitlines()):
        try:
            row = json.loads(line)
        except Exception:  # noqa: BLE001 — a corrupt line breaks nothing
            continue
        if row.get("fingerprint") == fingerprint and row.get("ts", 0) >= limit:
            WARNINGS.append(
                f"This same prompt was already generated recently with {slug}: "
                f"{row.get('file')}. If it works, reuse it instead of paying again. "
                "If you wanted a variant, ignore this notice.")
            return


def log_generation(tool: str, slug: str, kind: str, prompt: str, file: Path,
           refs: list[dict] | None = None) -> None:
    """Record every generation in `data/images/ledger.jsonl`.

    It serves two purposes: spotting repeats, and one day being able to cross
    which generated thumbnail actually got uploaded against the CTR it earned.
    Without this ledger, that validation cannot be reconstructed.
    """
    import time

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": int(time.time()),
        "date": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "tool": tool,
        "model_slug": slug,
        "kind": kind,
        "fingerprint": _fingerprint(slug, kind, prompt),
        "prompt": prompt,
        "file": str(file),
        "references": [f"{r['origin']}:{r['role']}" for r in (refs or [])],
        "uploaded_to_youtube": None,   # filled in by hand once published
    }
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def output_path(prefijo: str, kind: str, ext: str = "png") -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sello = time.strftime("%Y%m%d-%H%M%S")
    return OUTPUT_DIR / f"{prefijo}_{kind}_{sello}.{ext}"


def size_payload(cfg: dict, kind: str) -> dict:
    """Translate the target format into the size keys the model expects.

    Each fal model accepts some keys and rejects the rest, so which ones get
    sent lives in `fal.size_keys` in the config: if one returns 422, remove it
    from there without touching code.

    `image_size` goes as an object `{width, height}`, fal's universal form.
    Sending the string "1280x720" is invalid, and that was the bug this fixes.
    """
    fmt = cfg["formats"][kind]
    width, height = (int(x) for x in fmt["px"].split("x"))
    keys = cfg["fal"].get("size_keys", ["image_size"])
    payload = {}
    if "image_size" in keys:
        payload["image_size"] = {"width": width, "height": height}
    if "aspect_ratio" in keys:
        payload["aspect_ratio"] = fmt["ratio"]
    if "image_size_enum" in keys and fmt.get("enum_fal"):
        payload["image_size"] = fmt["enum_fal"]
    return payload


def validate_ratio(cfg: dict, kind: str) -> None:
    """Thumbnails are always 16:9. Verified, not trusted."""
    fmt = cfg["formats"].get(kind)
    if fmt is None or not fmt.get("fixed_ratio"):
        return
    width, height = (int(x) for x in fmt["px"].split("x"))
    esperado = tuple(int(x) for x in fmt["ratio"].split(":"))
    if abs(width / height - esperado[0] / esperado[1]) > 0.01:
        raise ToolError(
            f"Format '{kind}' is configured as {fmt['px']}, which is not "
            f"{fmt['ratio']}.", EXIT_NO_DATA,
            "Thumbnails are always 16:9. Fix `px` in "
            "config/image_providers.json.")


def compose_prompt(kind: str, prompt: str, refs: list[dict]) -> str:
    """Prepend the format spec and, when there is a likeness ref, its clause."""
    parts = [SPEC.get(kind, SPEC["general"])]
    for i, r in enumerate(refs, 1):
        if r["role"] == "likeness":
            parts.append(LIKENESS.format(label=f"Reference Image {i}"))
            break
    parts.append(prompt)
    if refs:
        labels = ", ".join(
            f"Reference Image {i} ({r['role']} reference)" for i, r in enumerate(refs, 1))
        parts.append(f"Reference images provided, in order: {labels}.")
        parts.append("Remove any watermark or third-party logo present in the "
                      "reference images.")
    parts.append("Do not add text that was not requested.")
    return " ".join(parts)


def sort_refs(refs: list[dict], cfg: dict) -> list[dict]:
    """People first, objects next, composition last. Three at most."""
    order = {"likeness": 0, "style": 1, "packaging": 2, "composition": 3}
    ordered = sorted(refs, key=lambda r: order.get(r["role"], 9))
    cap = cfg.get("max_references", 3)
    if len(ordered) > cap:
        raise ToolError(
            f"{len(ordered)} references, the maximum is {cap}.", EXIT_NO_DATA,
            "More references dilute the result. Drop the least important ones.")
    return ordered


def parse_ref(value: str, cfg: dict) -> dict:
    """`source:role`. An explicit role is required, never guessed.

    The source can contain colons (a URL does), so the role is always whatever
    follows the LAST `:`.
    """
    path, _, role = value.rpartition(":")
    if not path or role not in cfg["reference_roles"]:
        raise ToolError(
            f"Reference without a valid role: {value}", EXIT_NO_DATA,
            "Format: --ref SOURCE:ROLE, with ROLE in "
            f"{cfg['reference_roles']}. The role decides reference ordering "
            "and whether the likeness clause applies; guessing it "
            "ruins the face.")
    return {"origin": path, "role": role}


def mcp_directive(cfg: dict, action: str, prompt: str, refs: list[dict],
                  kind: str) -> dict:
    """In MCP mode this tool does not generate: it returns what the agent must call.

    A script cannot invoke an MCP tool from the session. Rather than pretend it
    can, it emits the exact call and stops.
    """
    m = cfg["mcp"]
    return {
        "mode": "mcp",
        "action_required": (
            f"This tool has NOT generated anything. Call the MCP tool "
            f"`{m['tools'].get(action, 'generate_image')}` on server "
            f"`{m['server']}` yourself, with the parameters in `call`."
        ),
        "server": m["server"],
        "tool": m["tools"].get(action, "generate_image"),
        "call": {
            "prompt": prompt,
            "model": m.get("default_model"),
            "aspect_ratio": cfg["formats"][kind]["ratio"],
            "references": [{"origin": r["origin"], "role": r["role"]} for r in refs],
        },
        "warnings": [
            f"Maximo {m.get('max_concurrent')} generaciones simultaneas.",
            "MCP tools cannot read local files: upload the image or pass a URL.",
            f"If `{m['server']}` is not in the session it is not connected: "
            "connect it in your connector settings, or switch `provider` to 'fal' "
            "en config/image_providers.json.",
        ],
    }
