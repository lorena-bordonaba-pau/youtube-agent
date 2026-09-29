---
name: History and outcomes
description: FICTIONAL EXAMPLE — what was predicted and what actually happened.
metadata:
  type: project
---

> **Fictional example.** Note the miss: it is written down like the hits.

## VIDEO_E — "Why your shot is sour (and it's not the beans)" — 2026-03-18
- **Predicted:** title scored 8.1 with `score_titles.py` (`heuristic`, own
  rubric — not a CTR prediction), closest to VIDEO_A (3.4× the median).
- **Happened:** 2.9× the channel median at 28 days (`yt_report.py`,
  2026-04-15). CTR 7.8 % from the Studio export (`ingest_studio_csv.py`).
- **Teaches:** the "and it's not X" structure travels. Second data point for it.

## VIDEO_F — "The €200 grinder upgrade nobody talks about" — 2026-04-01
- **Predicted:** strong; the topic was a 4.2× outlier on a competitor channel.
- **Happened:** 0.6× the median at 28 days (`yt_report.py`, 2026-04-29).
- **Teaches:** a gear topic without a fix did not carry over, even from a
  proven outlier. Not a rule yet — one miss. Retest once, inside a fix.
