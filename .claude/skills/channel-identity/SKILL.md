---
name: channel-identity
description: Channel positioning, differentiation against the competitive neighbourhood, and niche reframing. Triggered by "how do I position myself", "what makes me different", "where do I take the channel", "who is my real competition".
---

# Identity and positioning

## EXECUTION ORDER

1. **Where the channel is today**
   `python3 tools/yt_channel_stats.py`

2. **What the real neighbourhood is**
   `python3 tools/yt_outliers_channels.py --min-ratio 1.5`
   With a low threshold, because here you want each channel's editorial
   pattern, not only its peaks.

3. **Who you are actually producing for**
   ```
   python3 tools/yt_demographics.py --days 90
   python3 tools/yt_geography.py --days 90
   ```
   The contrast between the audience you think you have and the one you have
   is usually where the finding is.

4. **What people arrive with** — a signal of perceived positioning
   `python3 tools/yt_search_terms.py --days 180`
   The terms people search and find you with say how you are perceived, which
   is not always how you want to be positioned.

5. Update `memory/channel_positioning.md` if the analysis changes something
   stable. Only if stable: one week of data does not reposition a channel.

## SOURCES

Steps 1, 3 and 4 `youtube_api`. Step 2 `derived`.

## OUTPUT

- Current position, with figures and a date.
- Neighbourhood: which channels occupy the same space and how they differ.
- The concrete gap, with the evidence backing it.
- What would change in the editorial line, and what must NOT be touched.
