---
name: competitor-ideation
description: Next-video ideas drawn from real outliers among competitors and inspirations. Triggered by "ideas for this week", "what should I record", "what's blowing up in my niche", "analyse my competition".
---

# Ideation from competitors

## WHEN

Next-video ideas, competitor analysis, "what is working in the niche", the
weekly opportunity review.

## EXECUTION ORDER

1. **Outliers across the configured channels**
   `python3 tools/yt_outliers_channels.py --min-ratio 2.0 --sample 30`
   Reads the competitor and inspiration lists from
   `config/channels_lists.json`. If very few come back, drop to
   `--min-ratio 1.5` before concluding there is nothing.

2. **Hand-saved outliers**
   `python3 tools/yt_outliers_playlist.py --days 7`
   Whatever was saved during the week. If the playlist is not configured the
   tool says so with exit code 4; that is not a failure.

3. **Filter for relevance before spending quota**
   Discard by title anything that does not fit the channel. Only then:
   `python3 tools/yt_transcript.py --video ID --plain`
   on the ones that do. Transcribing everything is wasted time.

4. **Validate each idea**
   `python3 tools/kw_research.py --kw "idea 1; idea 2; idea 3"`
   `heuristic` score: it ranks the ideas against each other, it does not
   measure absolute demand.

5. **Prioritise against the channel, not in the abstract**
   Read `memory/creator_profile.md` and `memory/MEMORY.md`. An idea with a
   good outlier that does not fit the channel's archetype gets dropped, and you
   say why.

**The order adapts.** If step 1 returns a 10x outlier, prioritise it and go
deep even though the manual said transcribe everything first.

## SOURCES

Steps 1-2 `derived` (the ratio is computed over each channel's mean). Step 3
`youtube_api`. Step 4 `heuristic` — declare it.

## OUTPUT

Prioritised ideas. Each with:
- The outlier backing it: title, channel, ratio and URL **verbatim** from the
  tool.
- Why it worked there and what changes when bringing it to this channel.
- Your own angle, not a copy.

At the end, a single recommendation and the reason for it.
