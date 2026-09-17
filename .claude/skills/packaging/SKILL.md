---
name: packaging
description: A video's titles, thumbnail and description, scored with the channel's calibrated rubric. Triggered by "give me titles", "score this title", "review my thumbnail", "improve the packaging".
---

# Packaging: titles and thumbnails

## WHEN

Generating or evaluating titles, diagnosing a thumbnail, reviewing the
title+thumbnail pair, writing the description and tags.

## EXECUTION ORDER

1. **Score the titles — mandatory, never opine first**
   `python3 tools/score_titles.py --title "A || B || C"`
   Returns 0-100 with a per-axis breakdown and the memory justifying each
   point. It is `heuristic`: **you must declare it is an own rubric, not a CTR
   prediction**, and that it is unvalidated until the Studio CSV is ingested.

1b. **Two rules about the number, before you look at it**

   **Do not chase the score.** If an honest title scores 78 and an exaggerated
   one scores 95, recommend the 78 and say why. The rubric measures resemblance
   to what worked, not whether the title is true; well-built clickbait scores
   high and damages the channel.

   **Scores are only comparable within the same call.** Score the current title
   ALONGSIDE the candidates, in one run
   (`--title "current || A || B || C"`). Comparing today's number with another
   session's is not valid. And only propose a candidate that beats the current
   one **strictly**: a tie is not an improvement.

2. **Demand backing**
   ```
   python3 tools/yt_search_terms.py --days 90        # REAL demand, first
   python3 tools/kw_research.py --kw "candidate 1; candidate 2"
   ```
   The first one wins: those are terms people already reached the channel
   with. The second is a proxy and only ranks candidates against each other.

3. **Real references, not intuition**
   `python3 tools/yt_outliers_channels.py --min-ratio 2.5`
   Look at how the niche's live outliers are titling right now.

4. **The thumbnail**
   ```
   python3 tools/yt_thumbnails.py --video ID
   python3 tools/score_thumbnail.py --video ID --title "the chosen title"
   ```
   `score_thumbnail` only scores the automatic 40%. **It returns the other 60%
   as unanswered questions, and you must answer them by opening the JPG with
   vision.** Inventing that 60% is the failure this tool is designed to
   prevent.

5. **If the thumbnail has to be CREATED, not just judged**
   This skill scores what exists. To generate it: `image-generation-core`
   (base rules) + `thumbnail-best-practices` (design), and
   `likeness-preservation` if a face appears. If there is a specific reference
   to work from, `thumbnail-inspiration`. A generated image comes back as
   `source: generated`: **you cannot score it and then present that score as a
   CTR forecast**.

6. **Anti-redundancy contrast — the step most often skipped**
   Check that title and thumbnail are not communicating the same concept. If
   the hard number is in the title, the thumbnail shows the visual result. If
   `memory/sop/niche_bend_sop.md` exists, its lessons outrank any general
   rule.

## SOURCES

Steps 1 and 2b `heuristic` — always declare it. Step 2a `youtube_api`.
Steps 3 and 4a `derived`. Step 4b is mixed: `derived` in the pixels, the
agent's judgement for the rest.

## OUTPUT

1. The titles ranked by score, with the per-axis breakdown.
2. One line per title explaining which axis lifts or sinks it, citing the
   memory.
3. The thumbnail diagnosis with the judgement axes already answered after
   looking at the image.
4. The title-thumbnail contrast: which angle each one covers.

Never say a title "is going to work". Say which real video it resembles, and
why.
