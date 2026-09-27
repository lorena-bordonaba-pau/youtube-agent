---
name: competitor-mapping
description: Map the channels already winning with the channel's audience — in any language — validate each one with the creator, and back the provisional content pillars with real outliers. Runs after /kickoff. Triggered by "/competitors", "find my competitors", "who is winning in my niche", "validate my pillars". In Spanish, "busca mis competidores", "quién está ganando en mi nicho", "valida mis pilares".
---

# Competitor mapping and pillar validation

## WHEN

After `/kickoff`, when `memory/strategy.md` says `**Stage:** strategy`. If
the strategy is not written yet, stop and send the creator to `/kickoff`: the
map is built from the audience and the pillars, and without them any list of
channels is arbitrary.

Also whenever the creator wants the map refreshed or widened.

## THE METHOD

You learn what works for an audience by looking at who already wins with it:
to take what works, discard what does not, and find what nobody is offering
yet. Two rules shape the map:

- **Any language counts.** A channel in another market that wins with the same
  kind of viewer is often worth more than a local competitor: its winning
  topics may not exist in the creator's language yet. Those go to
  `inspiration`, and the question for each is "is this covered at home?".
- **The creator decides every channel.** The agent proposes; nothing enters
  `config/channels_lists.json` without an explicit yes for that channel.

## EXECUTION ORDER

**1. Build the search terms — and get them approved**
From `memory/strategy.md`: the core niche, the four provisional pillars and
the adjacent interests. Write each as a viewer would search it, in the
audience's language, in English, and in any other market ahead in the niche.
Aim for 8-15 terms. Show them with the cost — **100 quota units per term**, of
10,000 a day — and run only what the creator approves.

**2. Discover**
```
python3 tools/yt_discover_channels.py --terms "term 1; term 2; ..."
```
Thresholds come from `discovery` in `config/config.json`. If it warns that
there are fewer than 5 candidates, propose lowering `min_views` (small niches)
before adding more terms.

**3. Validate with the creator, five channels at a time**
For each candidate show: name, languages, number of outliers, and the best
one — title, views and ratio **verbatim** from the tool, with its URL
`https://www.youtube.com/watch?v=VIDEO_ID`. Flag `not_solo` channels (podcast,
interview, live): they are a different format from one person carrying the
video.

Propose a list for each, with one line of why:
- `competitors` — same audience, same language.
- `inspiration` — same audience, another language or another niche whose
  format or topics could be brought over.
- `neighbourhood` — the channels the creator knows their viewers also watch.

The creator answers per channel: yes to that list, another list, or no. For
every yes:
```
python3 tools/yt_channels_list.py --add CHANNEL_ID --to LIST --name "NAME" --notes "why, in one line"
```
Skip channels marked `already_in`. Keep going while the creator wants to; a
useful map has enough channels to yield around 50 outliers.

**4. Pull the outlier pool**
```
python3 tools/yt_outliers_channels.py --min-ratio 3 --sample 30 --max-days 180
```
Around 50 outliers is the target. Well short of it: go back to step 1 with
more terms, or lower the ratio to 2 and say so.

**5. Back the pillars with the market**
Hand the pool and `memory/strategy.md` to the `youtube-strategist` agent, in
its cold-start mode. For each provisional pillar it returns the outliers that
belong to it, and it proposes a replacement for any pillar the market does
not back, drawn from clusters of outliers that fit no pillar. The creator
approves every change.

**6. Write it down**
- `memory/channel_positioning.md`: the four pillars, each with its backing
  outliers (IDs and titles verbatim), and the map: which channels, which list,
  why.
- `memory/strategy.md`: section 4 updated with the validated pillars, no
  longer marked provisional, and `**Stage:** market-validated`.
Show the diff and write only what the creator approves.

## SOURCES

Candidates and the outlier pool are `derived`: the ratio is computed over each
channel's own mean. Views and titles are `youtube_api`. Languages are what
uploaders declared, often empty — say so rather than guessing a channel's
language from a title. The lists are `config`: the creator's judgement.

## OUTPUT

1. The map: how many channels per list, and the three most interesting
   inspirations from other markets with the question they raise for this one.
2. The four pillars, each with its three strongest backing outliers.
3. What changed from the provisional pillars, and why.
4. One next step: ideation is open. It starts when the creator asks for ideas
   (`competitor-ideation`), not here.
