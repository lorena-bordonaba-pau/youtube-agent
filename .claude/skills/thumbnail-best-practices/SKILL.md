---
name: thumbnail-best-practices
description: Thumbnail design rules — composition, text, mobile legibility. Triggered when generating or judging a thumbnail, whether your own or someone else's.
---

# Thumbnail design rules

## WHEN

Generating a thumbnail, diagnosing one, or extracting a channel's style. These
are design rules: they apply regardless of which provider generates.

## RELATIONSHIP WITH THE CHANNEL'S RUBRIC

These rules are **general**. `config/rubrics/thumbnails.yaml` is the rubric
**calibrated with this channel's memories**, and it wins where they conflict.
Its judgement axes carry 60 of the 100 points:

- `not_redundant_with_title` (25) — if the hard number is in the title, the
  thumbnail shows the **visual result**, it does not repeat the number.
- `result_not_ui` (18) — a timeline or a dense interface is grey noise at feed
  size.
- `logos` (9) — **one at most**, and only if it is an anchor your audience
  recognises.
- `short_text` (8) — four words or fewer.

On a fresh install those four axes are **uncalibrated examples**: each one's
`memory` field is `null`. Adapt them to your channel and, when you learn
something from your own thumbnails, write it into `memory/` and point the axis
at that file. When generating, the live axes go into the prompt.

## GENERAL RULES

**Mobile legibility** — the real bar. The thumbnail is seen at roughly 160 px
wide.
- The text should occupy **a third of the width or more**. Below that it is
  illegible.
- Heavy bold sans-serif, thick outline or hard shadow.
- A simple background area behind the text, for maximum contrast.
- Three to five words maximum.

**Composition**
- Rule of thirds: the focal point on an intersection.
- Negative space reserved for the text, preferably at the top.
- Leading lines (arms, arrows, architecture) pointing at the subject.
- Bottom right corner left clear: the duration stamp goes there.
- One single focal idea. Limited palette. High subject/background contrast.

**Authenticity**
- Only what actually appears in the video. A scene that does not exist is
  clickbait, and it penalises growth even when it lifts clicks.
- Realistic aesthetics over over-processed plastic.
- The expression should match the video's real emotion.
- Show the **action**, not a static pose.

**Human elements**
- A face helps but is not mandatory: hands, POV or an object work too.
- Different clothes and pose in each video, to signal fresh content.

**What to avoid**
- Crowded composition, small text, stock-photo aesthetics, thick borders,
  mixed colour temperatures (warm orange with daylight).

## VERIFICATION

Measure what is objective, do not opine about it:
```
python3 tools/yt_thumbnails.py --video ID          # contrast, saturation, resolution
python3 tools/score_thumbnail.py --video ID --title "..."
python3 tools/score_thumbnail.py --image path.jpg  # for one just generated
```
`score_thumbnail` scores the automatic 40% and **returns the 60% as unanswered
questions**. You answer them by opening the file. Inventing that 60% is the
failure the tool is designed to prevent.

## SOURCES

The rubric is `heuristic` and **not validated against CTR** while
`data/history/studio_ctr.json` does not exist. A score is never presented as
a click prediction. `yt_thumbnails`' pixel metrics are `derived`.
