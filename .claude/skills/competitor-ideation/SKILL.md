---
name: competitor-ideation
description: Next-video ideas drawn from real outliers among competitors and inspirations. Triggered by "ideas for this week", "what should I record", "what's blowing up in my niche", "analyse my competition". In Spanish, "ideas para la semana", "qué grabo ahora", "qué está petando en mi nicho", "analiza a mi competencia".
---

# Ideation from competitors

## WHEN

Next-video ideas, competitor analysis, "what is working in the niche", the
weekly opportunity review. Always started by the creator.

If `memory/strategy.md` is `NOT POPULATED`, say that ideas without a strategy
are guesses and offer `/kickoff` first. If it is at `**Stage:** strategy`, the
pillars are not market-backed yet: offer `/competitors`, or go ahead and label
the ideas as resting on provisional pillars.

## HOW IDEAS ARE BUILT

**Every idea belongs to a pillar.** Plan in batches of 8 — two per pillar —
so that after a month each pillar has been tested twice. Then review with
`/pillars`: learn, iterate, and scale what worked. One idea per pillar is too
little to conclude anything.

Three ways to get from an outlier to an idea. Name which one each idea uses:

- **Bring it over.** A title structure or format proven in another niche or
  another market, applied to this channel's topic. The structure travels; the
  topic is yours. The strongest source is a winner abroad with no equivalent
  in the creator's language.
- **Idea first, outlier second.** Start from something the creator genuinely
  wants to say, then find a format YouTube has already proven and fit the idea
  into it. The idea is original; the packaging is not a gamble.
- **Same title, different video.** Only for titles so general that nobody owns
  them ("if I had to start X today, this is what I would do"), and only when
  the creator brings something the original could not. Otherwise it is a copy
  and it competes with the original.

## EXECUTION ORDER

1. **Outliers across the configured channels**
   `python3 tools/yt_outliers_channels.py --min-ratio 2.0 --sample 30`
   Reads the competitor and inspiration lists from
   `config/channels_lists.json`. If very few come back, drop to
   `--min-ratio 1.5` before concluding there is nothing.

   **If there is a competitor board** (`memory/competitor_board.md` holds its
   URL), sync it with the `competitor-board` skill and use its
   `data.top_organic_outliers` too. It covers every long-form video of the last
   6 months, not a sample, and it has already dropped the videos whose views
   look bought as ads.

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

4.5 **Size each idea**
   `python3 tools/topic_tam.py --topic "idea 1::regex" --topic "idea 2::regex"`
   Match the audience's interest, not the exact case (an agent that runs your
   YouTube channel is sized as "an AI that runs your business"). It gives the
   TAM the topic moved on the board and floor / expected / ceiling views for
   this channel. `heuristic`: quote it as an estimate, with the user's own
   record on the topic next to it.

5. **Prioritise against the channel, not in the abstract**
   Read `memory/strategy.md`, `memory/creator_profile.md` and
   `memory/MEMORY.md`. An idea that attracts a viewer the objective does not
   need gets dropped, however strong its outlier. An idea with a
   good outlier that does not fit the channel's archetype gets dropped, and you
   say why.

**Before building on any outlier, check its likes per 1k views against the
channel's usual.** Views that arrive without likes are paid reach (ads), and
the ratio they post says nothing about the format or the title. Affiliate links
are no signal: almost every channel carries them.

**The order adapts.** If step 1 returns a 10x outlier, prioritise it and go
deep even though the manual said transcribe everything first.

## SOURCES

Steps 1-2 `derived` (the ratio is computed over each channel's mean; the
board uses the median). The board's `ad_suspect` flag is `heuristic`. Step 3
`youtube_api`. Step 4 `heuristic` — declare it.

## OUTPUT

Prioritised ideas, grouped by pillar. Each with:
- The pillar it tests and the technique it uses.
- The outlier backing it: title, channel, ratio and URL **verbatim** from the
  tool.
- Why it worked there and what changes when bringing it to this channel.
- Your own angle, not a copy.

At the end, a single recommendation and the reason for it.
