#!/usr/bin/env python3
"""Score a thumbnail with the channel's calibrated rubric.

IT DOES NOT PREDICT CTR, and it does not score alone: only 40% of the rubric
is automatic (contrast, resolution, saturation). The other 60% are JUDGEMENT
axes that require looking at the image. The tool returns those as open
questions for the agent to answer by opening the file, instead of inventing a
number.
"""
from pathlib import Path

import yaml

from lib import base  # noqa: F401
from lib.contract import (CONFIG_DIR, EXIT_NO_DATA, EXIT_USAGE, SOURCE_HEURISTIC,
                          ToolError, emit, main, parser, envelope)
from yt_thumbnails import download, metrics

TOOL = "score_thumbnail"
RUBRIC = CONFIG_DIR / "rubrics" / "thumbnails.yaml"


def por_rango(value: float, axis: dict) -> tuple[int, str]:
    for r in axis.get("ranges", []):
        if value >= r.get("min", 0):
            return r["points"], r["reason"]
    return 0, "Fuera de span"


def run():
    p = parser(__doc__)
    p.add_argument("--video", help="video_id of an already published thumbnail")
    p.add_argument("--image", help="path to a local image, e.g. one just generated")
    p.add_argument("--title", help="the video title, for the redundancy axis")
    args = p.parse_args()

    if bool(args.video) == bool(args.image):
        raise ToolError("Needs --video or --image, and exactly one of them",
                        EXIT_USAGE,
                        "--video ID for a published thumbnail; --image PATH for a "
                        "local file, such as one just generated.")

    if not RUBRIC.exists():
        raise ToolError(f"Missing rubric at {RUBRIC}", EXIT_NO_DATA)
    with open(RUBRIC, encoding="utf-8") as f:
        rubric = yaml.safe_load(f)

    meta = {}
    if args.image:
        path = Path(args.image)
        if not path.exists():
            raise ToolError(f"{path} does not exist", EXIT_NO_DATA)
    else:
        from lib import yt_data
        try:
            info = yt_data.video_stats([args.video])
            meta = info[0] if info else {}
        except Exception:  # noqa: BLE001 — without the API, carry on with pixels only
            meta = {}
        path = download(args.video, meta.get("thumbnail"))
    m = metrics(path)

    automaticos, total_auto, peso_auto = [], 0, 0
    for axis in rubric["automatic_axes"]:
        weight = axis["weight"]
        peso_auto += weight
        if axis["id"] == "center_contrast":
            pts, reason = por_rango(m["center_contrast"], axis)
            value = m["center_contrast"]
        elif axis["id"] == "saturation":
            pts, reason = por_rango(m["mean_saturation"], axis)
            value = m["mean_saturation"]
        elif axis["id"] == "resolution":
            pts = weight if m["is_maxres"] else round(weight * 0.3)
            reason = ("maxres" if m["is_maxres"]
                      else "Below 1280x720: it will look soft")
            value = m["resolution"]
        else:
            continue
        pts = min(pts, weight)
        total_auto += pts
        automaticos.append({"axis": axis["id"], "value": value, "points": pts,
                            "weight": weight, "reason": reason})

    judgement = [{"axis": e["id"], "weight": e["weight"], "memory": e.get("memory"),
               "question": e["question"].strip(), "points": None}
              for e in rubric["judgement_axes"]]

    env = envelope(TOOL, SOURCE_HEURISTIC, {
        "video": args.video,
        "image": args.image,
        "title": args.title or meta.get("title"),
        "file": m["file"],
        "metrics": m,
        "automatic_subtotal": f"{total_auto}/{peso_auto}",
        "automatic_axes": automaticos,
        "pending_judgement_axes": judgement,
        "total_score": None,
    }, {"video": args.video, "image": args.image}, False, notes=[
        "DELIBERATELY INCOMPLETE SCORE: only the automatic 40% is scored.",
        f"To complete it, open {m['file']} with the image reading tool and "
        "answer the `pending_judgement_axes`.",
        "NOT a CTR prediction. The rubric is not validated against real CTR.",
    ] + ([
        "Local image, probably generated: scoring it does NOT make it data. "
        "A high score on a generated image is still an unvalidated rubric "
        "applied to an artefact.",
    ] if args.image else []))

    def md(e):
        d = e["data"]
        out = [base.md_header(e),
               f"\n**{d['title'] or '(untitled)'}**  \n`{d['file']}`\n",
               f"\n## Automatic: {d['automatic_subtotal']}\n",
               base.md_table(d["automatic_axes"],
                             ["axis", "value", "points", "weight", "reason"]),
               "\n## Pending visual judgement (60 points)\n"]
        for j in d["pending_judgement_axes"]:
            mem = f" _(memory: {j['memory']})_" if j["memory"] else ""
            out.append(f"- **{j['axis']}** ({j['weight']} pts){mem}: {j['question']}")
        return "\n".join(out)

    emit(env, args, md)


if __name__ == "__main__":
    main(TOOL, run)
