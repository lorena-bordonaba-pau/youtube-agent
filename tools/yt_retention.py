#!/usr/bin/env python3
"""Real retention curve for one of your videos: where people leave.

`averageViewPercentage` tells you HOW MUCH you retain but not WHERE viewers
go. This is what turns a script SOP's re-hook timings into something you can
verify.
"""
from lib import base  # noqa: F401
from lib import cache, yt_data
from lib import yt_analytics as ya
from lib.contract import (EXIT_NO_DATA, SOURCE_API, ToolError, emit, main,
                          parser, envelope)

TOOL = "yt_retention"

# A drop larger than this % of the audience between two consecutive curve
# points (each point = 1% of the video) is flagged as a concentrated exit.
DROP_THRESHOLD = 1.5


def run():
    p = parser(__doc__)
    p.add_argument("--video", required=True)
    p.add_argument("--days", type=int, default=365)
    p.add_argument("--threshold", type=float, default=DROP_THRESHOLD)
    args = p.parse_args()

    def fetch():
        curve = ya.retention(args.video, args.days)
        meta = yt_data.video_stats([args.video])
        return {"curve": curve, "meta": meta[0] if meta else None}

    payload_data, hit = cache.memo("own_analytics", f"{TOOL}:{args.video}:{args.days}",
                            fetch, not args.no_cache)
    curve = payload_data["curve"]
    if not curve:
        raise ToolError(
            f"No retention data for {args.video}.", EXIT_NO_DATA,
            "It may be too new, have too few views, or not belong to the "
            "authorised channel.")

    dur_s = (payload_data["meta"] or {}).get("duration_s", 0)

    # Annotate each point with its real timestamp and the drop from the last
    points, previo = [], None
    for row in curve:
        ratio = row["elapsedVideoTimeRatio"]
        watch = round(row["audienceWatchRatio"] * 100, 2)
        seg = int(ratio * dur_s) if dur_s else None
        punto = {
            "pct_video": round(ratio * 100, 1),
            "moment": f"{seg // 60}:{seg % 60:02d}" if seg is not None else None,
            "audience_pct": watch,
            "vs_similar": round(row.get("relativeRetentionPerformance", 0), 3),
            "drop": round(previo - watch, 2) if previo is not None else 0,
        }
        points.append(punto)
        previo = watch

    caidas = sorted((p for p in points if p["drop"] >= args.threshold),
                    key=lambda p: p["drop"], reverse=True)

    # Milestones a script SOP cares about
    def en(pct):
        return min(points, key=lambda p: abs(p["pct_video"] - pct))

    milestones = {}
    if dur_s:
        for label, segundo in (("intro_30s", 30), ("re_hook_min3", 180),
                                  ("re_hook_min6", 360)):
            if segundo < dur_s:
                milestones[label] = en(segundo / dur_s * 100)
    milestones["half"] = en(50)
    milestones["final"] = points[-1]

    env = envelope(TOOL, SOURCE_API,
                {"video_id": args.video,
                 "title": (payload_data["meta"] or {}).get("title"),
                 "duration": (payload_data["meta"] or {}).get("duration"),
                 "points": points,
                 "drops_detected": caidas[:10],
                 "milestones": milestones},
                {"video": args.video, "days": args.days, "threshold": args.threshold}, hit,
                notes=[
                    "`audience_pct` comes from the API (audienceWatchRatio).",
                    "`vs_similar` compares against videos of similar length across "
                    "YouTube: 0.5 is the median.",
                    "`drop` and `moment` are computed (source: derived).",
                ])

    def md(e):
        d = e["data"]
        out = [base.md_header(e), f"\n**{d['title']}** ({d['duration']})\n",
               "\n## Hitos\n",
               base.md_table([{"milestone": k, **v} for k, v in d["milestones"].items()],
                             ["milestone", "moment", "pct_video", "audience_pct",
                              "vs_similar"]),
               f"\n## Caidas concentradas (>= {args.threshold} points)\n",
               base.md_table(d["drops_detected"],
                             ["moment", "pct_video", "audience_pct", "drop"])]
        return "\n".join(out)

    emit(env, args, md)


if __name__ == "__main__":
    main(TOOL, run)
