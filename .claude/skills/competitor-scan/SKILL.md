---
name: competitor-scan
description: The weekly scan of competitor, inspiration and neighbourhood channels — what is performing right now, whether it already exists in your language, and the 3 widest gaps. Run by /radar. Triggered by "run the weekly scan", "what are my competitors doing this week", "scan my lists". In Spanish, "pasa el escaneo semanal", "qué están haciendo mis competidores esta semana", "escanea mis listas".
---

# Weekly competitor scan

## WHEN

The weekly review of the channel lists, usually through `/radar`. Always
started by the creator.

Not the competitor board (the web page with every video of the last 6 months:
that is `competitor-board`) and not a full ideation batch (that is
`competitor-ideation`). This scan finds what moved recently and where the gap
is; it ends with three proposals, not eight.

Read `CLAUDE.md` if you have not already done so this session.

## EXECUTION ORDER

### 1. Scan

```
python3 tools/yt_outliers_channels.py --min-ratio 2.0 --sample 25 --max-days 45
```

**`--max-days 45` is not optional.** Without it, ranking by ratio buries what
is recent under outliers from 6-11 months ago, which are no longer
opportunities.

If fewer than 10 outliers come back, drop to `--min-ratio 1.5` before
concluding there is nothing.

### 2. Add what was saved by hand

```
python3 tools/yt_outliers_playlist.py --days 14
```

### 3. Split by list — each one is read differently

- **`competitors`** (same language, same niche): what works here is direct
  competition. If a competitor lands an outlier, the gap is closing.
- **`inspiration`** (often another language, an arbitrage source): **this is
  usually the list that matters**. For each outlier, the question is: does it
  already exist in your language?
- **`neighbourhood`** (channels YouTube associates with yours): tells you how the
  algorithm is classifying you.

### 4. Adjust for market size before quoting figures

Views in a larger-market language **are not reachable as-is** in a smaller one.
Measure your own factor over time and write it into `memory/`; until you have
one, say you are quoting the raw figure and that it overstates the expectation.

If you have a memory about how to read outliers, apply it here.

### 5. Check the gap in your language

For the 3-5 strongest foreign-language outliers:

```
python3 tools/kw_research.py --kw "topic in your language; variant"
python3 tools/yt_search.py --query "topic in your language"
```

`yt_search` costs 100 quota units per query — use it only on the finalists. And
remember it **does not filter by language**: if the top results are in another
language, that does not prove the gap in yours is closed.

### 6. Leave out bought views

Before an outlier goes into the table, check its likes per 1k views against the
channel's usual. Views that arrive without likes are ad reach: drop the video
and say so. Affiliate links prove nothing, almost every channel carries them.

### 7. Filter against the channel's rules

Read `memory/rules.md` and `memory/creator_profile.md`. Discard what does not
fit and say why.

**Format reminder**: apply the restrictions in `memory/rules.md`, if there are
any. Never propose a format the channel has discarded.

**Title reminder**: do not copy the original's formula. Copy the TOPIC and
rewrite it with the house formula, whatever your own data says that is. And a
high ratio on a huge channel does not mean the same thing as on a small one.

## SOURCES

- Outlier ratios, views and likes: `youtube_api` (views, likes) and `derived`
  (the ratio against the channel's median).
- `kw_research.py` scores: `heuristic`, a proxy — **never** a search volume.
- `score_titles.py` scores: `heuristic`, **never** a CTR prediction.
- The market-size factor: `config` if it is in `memory/`, otherwise say there
  is none and that the raw figure overstates the expectation.

## OUTPUT

1. **Opportunity table**: outlier, channel, ratio, views, and whether it
   already exists in your language.
2. **The 3 with the widest gap**, each with a proposed title already in the
   channel's formula, scored with `python3 tools/score_titles.py`.
3. **One recommendation** and the reason for it.
4. If an outlier changes what was known about the niche, propose updating
   `memory/`.
5. If there is a competitor board (`memory/competitor_board.md`), sync it with
   the `competitor-board` skill and end with its link. If there is none, offer
   to create one in a single line.
