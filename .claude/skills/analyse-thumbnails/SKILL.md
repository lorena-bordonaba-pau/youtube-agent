---
name: analyse-thumbnails
description: Extract a channel's thumbnail style, your own or someone else's, before generating a new one. Triggered by "what are my thumbnails like", "analyse this channel's style", "what visual pattern does my competition follow".
---

# Thumbnail style analysis

## WHEN

Proactive study of a channel's style, **with nobody having provided a specific
reference**. If the creator brings one thumbnail they like, that is
`thumbnail-inspiration`, not this skill.

It serves two purposes: knowing your own brand before generating something that
breaks it, and reading a competitor's visual pattern.

## EXECUTION ORDER

1. **Pick 3 to 5 representative videos**
   ```
   python3 tools/yt_recent_videos.py [--channel ID] --limit 15 --stats
   ```
   Representative of the **current** style: skip collaborations and
   off-brand experiments. If the channel changed style, only what came after.

2. **Download and measure the pixels**
   `python3 tools/yt_thumbnails.py --video ID1,ID2,ID3`
   Gives contrast, luminance, saturation and resolution. Objective, not
   arguable.

3. **Look at them.** Open each `file` path with the image reading tool. **This
   step is not optional**: the pixels do not tell you what is shown.

4. **Score one or two** to get the quantitative contrast:
   `python3 tools/score_thumbnail.py --video ID --title "..."`

5. **Extract the pattern**, noting in how many of the N each trait appears:
   - Colour palette and dominant temperature.
   - Typography: size relative to width, outline, word count. Flag it if the
     text occupies less than a third of the width.
   - Layout: where the subject falls, where the text does, what space is left.
   - Face usage: if one appears, **note the `video_id` where it reads best** —
     that is the likeness reference for generating later.
   - Recurring motifs: arrows, frames, split screens, logos, emoji.

   A trait appearing in 1 of 5 is not the channel's style, it is an exception.

6. **Cross against performance.** The pattern only matters against what worked:
   `python3 tools/yt_outliers_channels.py --min-ratio 2.0`.
   A consistent style that performs badly is a consistent style that performs
   badly.

## OUTPUT

1. **A style brief in 5-8 bullets**, each with its frequency ("4 of 5").
2. **The 1-2 most representative `video_id`s** and why they are.
3. If there is a face, the `video_id` of the best likeness reference.
4. What must be **kept** so the brand is not broken, and what is **weak**
   measured against the rubric.

## SOURCES

Pixel metrics `derived`. Views and outliers `derived` over `youtube_api`. The
style reading is the agent's judgement over images it has opened, and is
declared as such. The rubric is `heuristic`, unvalidated against CTR.
