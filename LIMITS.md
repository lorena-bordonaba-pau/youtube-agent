# Limits

What this harness **cannot** do. Declared when relevant, without waiting to be
asked.

## Data that does not exist

**CTR and impressions.** Not in YouTube's public API, only in Studio. It is the
gap most often cited in channel reports: you can measure how many views there
were, but not why people did not click. The only route: export the CSV from
Studio → Analytics → Advanced mode → Videos, and ingest it with
`tools/ingest_studio_csv.py`.

**Search volume.** YouTube does not publish it for free. `kw_research.py`
combines autocomplete and the competition in the top results to give a
**relative ranking among the keywords compared within that same run**.
Comparing two different runs is not valid. For verified demand there is
`yt_search_terms.py`, which returns real traffic.

**Other channels' analytics.** Only what is public: views, likes, comments,
duration, tags. Never another channel's retention, traffic or demographics.
When a report talks about a competitor's retention, that is inference, not
measurement.

**Retention on low-view videos.** YouTube applies privacy thresholds:
`yt_retention.py` returns nothing for new or low-volume videos. That comes back
as exit code 4, not as zero.

## Estimates that are not measurements

**Title and thumbnail scores do not predict CTR.** They are weighted checklists
encoding lessons already learned from real videos. They say how closely
something resembles what worked before, not how it will perform.

**The rubrics are not validated.** While `data/history/studio_ctr.json` does
not exist, `validated_against_ctr` is `false` in both files under
`config/rubrics/`. That has to be said when giving a score. **On a fresh
install they are also uncalibrated**: every axis's `memory` field is `null`, so
they encode general good practice rather than your channel's lessons.

**60% of the thumbnail rubric is not automatic.** `score_thumbnail.py` scores
contrast, resolution and saturation; the axes for redundancy with the title,
result-vs-interface and logos require looking at the image. The tool returns
those questions unanswered on purpose, instead of inventing a number.

**A generated image is not evidence of anything.** It comes back as
`source: generated`: an artefact from an external model. It does not predict
CTR, does not predict clicks and does not prove a design works. When delivering
it you must name the model that produced it, and you cannot score it with the
rubric and then present that number as a forecast.

**Automatic transcripts contain errors.** Neither YouTube's captions nor
Whisper are reliable word by word. Never quote a sentence as someone's exact
words without checking it in the video.

## Actions that are not taken

- **Nothing is published or modified on YouTube.** The scopes are read-only.
  Changing titles, thumbnails, descriptions or visibility is manual in Studio;
  the harness gives you the text and the path.
- **A generated image is never uploaded to YouTube.** The harness leaves the
  file at the right dimensions; setting it as a thumbnail, banner or avatar is
  manual.
- **No video or audio is generated or edited.** It plans, structures and
  measures; rendering is a different tool.
- **No channels are contacted and no emails are sent.**

## External dependencies

- **A Google API key or OAuth credentials.** A key unlocks all public data.
  OAuth is needed for your own analytics; if the token expires, those tools
  exit with code 2 and `python3 tools/auth_setup.py` fixes it. Tokens for an
  app in *Testing* mode expire after 7 days.
- **`yt-dlp`** for transcripts and **`whisper-cli`** as a fallback.
- **An image provider**, only for the visual branch: a `FAL_KEY`, or an image
  MCP connected to the session. Without one, the branch only works in
  `--dry-run`.
- **The model does not honour the aspect ratio on its own.**
  `fal-ai/nano-banana` ignores `image_size` and letterboxes its output unless
  explicitly told not to. That is why `generate_image` measures the file, trims
  the bars and forces 16:9 after generating: the guarantee is in the pixels,
  not in the prompt.
- **A daily quota of 10,000 units**, shared with anything else using the same
  Google Cloud project.
