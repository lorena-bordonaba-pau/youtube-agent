#!/usr/bin/env python3
"""Download thumbnails and compute deterministic visual metrics.

The metrics here are objective: contrast, luminance, saturation. The semantic
reading — what is actually shown, whether the text competes with the title —
is done by the agent opening the downloaded file with vision.
"""
import urllib.request
from pathlib import Path

from PIL import Image

from lib import base  # noqa: F401
from lib import yt_data
from lib.contract import (DATA_DIR, EXIT_NO_DATA, SOURCE_DERIVED, ToolError,
                          emit, main, parser, envelope)

TOOL = "yt_thumbnails"
DIR = DATA_DIR / "thumbnails"


def download(video_id: str, url: str) -> Path:
    DIR.mkdir(parents=True, exist_ok=True)
    dest = DIR / f"{video_id}.jpg"
    if dest.exists():
        return dest
    # maxres does not always exist; fall back to hqdefault.
    candidates = [f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg", url,
                  f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"]
    for cand in [c for c in candidates if c]:
        try:
            req = urllib.request.Request(cand, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                if r.status == 200:
                    dest.write_bytes(r.read())
                    return dest
        except Exception:  # noqa: BLE001 — try the next candidate
            continue
    raise ToolError(f"Could not download the thumbnail for {video_id}", EXIT_NO_DATA)


def metrics(path: Path) -> dict:
    img = Image.open(path).convert("RGB")
    width, height = img.size
    peq = img.resize((160, 90))          # the real perceived size in the mobile feed
    pixeles = list(peq.getdata())

    lum = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in pixeles]
    media_lum = sum(lum) / len(lum)
    desv = (sum((x - media_lum) ** 2 for x in lum) / len(lum)) ** 0.5

    sat = []
    for r, g, b in pixeles:
        mx, mn = max(r, g, b), min(r, g, b)
        sat.append((mx - mn) / mx if mx else 0)

    # Contrast of the centre third: where the subject and big text usually go
    centro = peq.crop((40, 22, 120, 68)).convert("L")
    cpx = list(centro.getdata())
    c_media = sum(cpx) / len(cpx)
    c_desv = (sum((x - c_media) ** 2 for x in cpx) / len(cpx)) ** 0.5

    return {
        "file": str(path),
        "resolution": f"{width}x{height}",
        "is_maxres": width >= 1280,
        "mean_luminance": round(media_lum, 1),
        "global_contrast": round(desv, 1),
        "center_contrast": round(c_desv, 1),
        "mean_saturation": round(sum(sat) / len(sat), 3),
        "pct_dark_pixels": round(sum(1 for x in lum if x < 60) / len(lum) * 100, 1),
        "pct_light_pixels": round(sum(1 for x in lum if x > 200) / len(lum) * 100, 1),
    }


def run():
    p = parser(__doc__)
    p.add_argument("--video", required=True, help="video_id, or several separated by commas")
    args = p.parse_args()

    ids = [v.strip() for v in args.video.split(",") if v.strip()]
    stats = {s["video_id"]: s for s in yt_data.video_stats(ids)}

    out = []
    for vid in ids:
        info = stats.get(vid, {})
        path = download(vid, info.get("thumbnail"))
        out.append({"video_id": vid, "title": info.get("title"),
                       "views": info.get("views"), **metrics(path)})

    env = envelope(TOOL, SOURCE_DERIVED, out, {"video": ids},
                notes=[
                    "Objective metrics computed over the pixels, not opinions.",
                    "They do NOT judge the thumbnail or predict CTR.",
                    "To judge composition, subject or text, open the path in "
                    "`file` with the image reading tool.",
                ])
    emit(env, args, lambda e: base.md_header(e) + "\n" + base.md_table(
        e["data"], ["video_id", "title", "resolution", "global_contrast",
                    "center_contrast", "mean_luminance", "mean_saturation"]))


if __name__ == "__main__":
    main(TOOL, run)
