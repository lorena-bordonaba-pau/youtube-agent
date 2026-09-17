---
name: monetizacion
description: Partner Programme thresholds, subscriber and watch-hour projection. Triggered by "when do I monetise", "how far am I from YPP", "will I hit the requirements".
---

# Monetisation

## EXECUTION ORDER

1. **Status against the thresholds**
   `python3 tools/yt_channel_stats.py`

2. **Real trend, not hope**
   ```
   python3 tools/yt_analytics.py --days 90
   python3 tools/yt_report.py --days 28
   ```
   That gives net subs and minutes watched per window. The projection is built
   on the measured trend, not on the best week.

3. Project. Every projection is `derived` and is declared as such, with the
   assumption visible ("at the pace of the last 90 days").

## SOURCES

`youtube_api` for the status, `derived` for the projection.

## THIS SKILL'S LIMITS

- **There is no revenue data.** The monetary scope is granted but no tool
  requests revenue metrics. RPM and earnings are not estimated.
- Partner Programme thresholds are set by YouTube and change by country and
  content type. If there is doubt about a specific requirement, say so and
  point at the official documentation rather than asserting it from memory.

## OUTPUT

Current status against each threshold, the measured pace, a projection with its
assumption declared, and the highest-impact lever according to the channel's
data.
