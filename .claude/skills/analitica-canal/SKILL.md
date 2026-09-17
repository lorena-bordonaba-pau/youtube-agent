---
name: analitica-canal
description: Audit and diagnose your own channel with real data — performance, retention, traffic, audience, and comparison against earlier snapshots. Triggered by "how's the channel doing?", "audit my videos", "why did it drop", "what's working".
---

# Channel audit

## WHEN

Performance diagnosis, periodic report, "why did this video flop?", "what is
working and what is not?", comparing periods.

## EXECUTION ORDER

1. **Baseline and history**
   `python3 tools/yt_report.py --days 28`
   Gives the overall state, top videos, traffic, audience and geography, and
   appends a snapshot. If earlier snapshots exist it returns
   `change_since_last_snapshot`: **that delta is the real diagnosis**, not the
   still photo.

2. **Rank by retention, not only by views**
   `python3 tools/yt_top_videos.py --days 90 --by-retention`
   A video with few views and high retention is a format signal; one with many
   views and low retention is a promise problem.

3. **Where people come from**
   `python3 tools/yt_traffic.py --days 28`
   `python3 tools/yt_search_terms.py --days 90`
   The second is the one that pays: those are the **real** terms people arrive
   through. Subscriber dependence above 50% means the channel is not reaching
   beyond its own base.

4. **Where they leave** — on the 3 most relevant videos from step 2
   `python3 tools/yt_retention.py --video ID`
   Look at `milestones`: `intro_30s`, `re_hook_min3`, `re_hook_min6`. A drop in
   the intro is a promise problem; a drop at a re-hook is a structure problem.
   If `memory/sop/scripting_sop.md` exists, contrast against it.

5. **Mandatory cross-check before concluding**
   `python3 tools/yt_outliers_channels.py --min-ratio 2.0`
   Without this you cannot tell a channel problem from the whole niche moving.

6. Compare against what was already known: `memory/MEMORY.md`, especially any
   `outcome_*` files, which hold the prediction made before the video against
   the real result.

**The order adapts to the data.** If step 1 reveals a sharp drop, go straight
to step 4 on the affected video. The data outranks the manual.

## SOURCES

Steps 1-4 `youtube_api` (aggregates and percentages `derived`). Step 5
`derived`. No heuristics: this skill estimates nothing.

## OUTPUT

1. Headline: what changed and since when, with the data's date.
2. Status table with the delta against the previous snapshot.
3. Diagnosis: 2-3 causes, each backed by a concrete figure.
4. Priority action: one only, the highest impact.

If CTR is missing to close the diagnosis, say so and point at
`tools/ingest_studio_csv.py`. See `LIMITS.md`.
