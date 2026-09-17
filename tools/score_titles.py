#!/usr/bin/env python3
"""Score titles 0-100 with the channel's calibrated rubric.

IT DOES NOT PREDICT CTR. It is a weighted checklist encoding lessons already
learned from real videos (config/rubrics/titles.yaml). Every point added or
subtracted cites the memory that justifies it.
"""
import re

import yaml

from lib import base  # noqa: F401
from lib.contract import (CONFIG_DIR, EXIT_NO_DATA, SOURCE_HEURISTIC, ToolError,
                          emit, main, parser, envelope)

TOOL = "score_titles"
RUBRIC = CONFIG_DIR / "rubrics" / "titles.yaml"


def cargar_rubrica() -> dict:
    if not RUBRIC.exists():
        raise ToolError(f"Missing rubric at {RUBRIC}", EXIT_NO_DATA)
    with open(RUBRIC, encoding="utf-8") as f:
        return yaml.safe_load(f)


def evaluar_eje(title: str, axis: dict) -> dict:
    weight = axis["weight"]
    points, reasons = 0, []

    for b in axis.get("bonus", []):
        if re.search(b["patron"], title, re.IGNORECASE):
            points += b["points"]
            reasons.append(f"+{b['points']} {b['reason']}")
            break  # an axis bonus does not stack with itself

    for p in axis.get("penalties", []):
        if re.search(p["patron"], title, re.IGNORECASE):
            points += p["points"]
            reasons.append(f"{p['points']} {p['reason']}")

    if "ranges" in axis:
        n = len(title)
        for r in axis["ranges"]:
            if n <= r.get("max", 10 ** 9):
                points += r["points"]
                reasons.append(f"+{r['points']} {r['reason']} ({n} characters)")
                break

    # Axes with no signal detected start at half weight: the absence of a
    # marker is not proof the title is bad on that axis.
    if not reasons:
        points = round(weight * 0.5)
        reasons.append(f"+{points} No signal detected on this axis (neutral)")

    return {
        "axis": axis["id"],
        "weight": weight,
        "points": max(0, min(weight, points)),
        "memory": axis.get("memory"),
        "reasons": reasons,
    }


def puntuar(title: str, rubric: dict) -> dict:
    axes = [evaluar_eje(title, e) for e in rubric["axes"]]
    return {
        "title": title,
        "characters": len(title),
        "score": sum(e["points"] for e in axes),
        "breakdown": axes,
    }


def run():
    p = parser(__doc__)
    p.add_argument("--title", required=True,
                   help="title, or several separated by ' || '")
    args = p.parse_args()

    rubric = cargar_rubrica()
    titulos = [t.strip() for t in args.title.split("||") if t.strip()]
    results = sorted((puntuar(t, rubric) for t in titulos),
                        key=lambda r: r["score"], reverse=True)

    env = envelope(TOOL, SOURCE_HEURISTIC,
                {"rubric_version": rubric["version"],
                 "calibrated_with": rubric["calibrated_with"],
                 "validated_against_ctr": rubric["validated_against_ctr"],
                 "results": results},
                {"n_titles": len(titulos)}, False,
                notes=[
                    "NOT a CTR prediction. It is a weighted checklist built from "
                    "lessons already learned on this channel.",
                    "The rubric is NOT validated against real CTR: you need to "
                    "ingest the YouTube Studio CSV (ingest_studio_csv.py).",
                    "A low-scoring title can still work; the score only says how "
                    "closely it resembles what worked before.",
                ])

    def md(e):
        out = [base.md_header(e), ""]
        for r in e["data"]["results"]:
            out.append(f"\n## {r['score']}/100 — {r['title']}  \n"
                       f"_{r['characters']} characters_\n")
            for d in r["breakdown"]:
                mem = f" _(memory: {d['memory']})_" if d["memory"] else ""
                out.append(f"- **{d['axis']}** {d['points']}/{d['weight']}{mem}")
                out.extend(f"    - {x}" for x in d["reasons"])
        return "\n".join(out)

    emit(env, args, md)


if __name__ == "__main__":
    main(TOOL, run)
