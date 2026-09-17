---
name: thumbnail-inspiration
description: Analyse a reference thumbnail and generate one inspired by it, adapting its design principles to your own content. Triggered by "make me a thumbnail like this one", "I like this thumbnail", "take inspiration from this video".
---

# Thumbnail inspired by a reference

## WHEN

There is **one specific reference**: an image provided, someone else's video
thumbnail, or one generated earlier. If there is no reference and the goal is
to read a whole channel's style, that is `analyse-thumbnails`.

**Adapt principles, do not copy.** Copying a competitor's thumbnail puts yours
next to theirs in the feed, competing with the original and losing.

## EXECUTION ORDER

1. **See the reference**
   - It is a YouTube video: `python3 tools/yt_thumbnails.py --video ID` and
     open the file.
   - It is a local file or a provided image: open it directly.

2. **Measure it, if it is from YouTube**
   `python3 tools/score_thumbnail.py --video ID`
   Gives the reference's real contrast and saturation, which is what makes it
   stand out in the feed and what usually gets lost when imitating by eye.

3. **Extract the design formula in 5-8 bullets**: layout, palette, typography
   (relative size, outline, word count), mood, human elements (expression,
   pose, gaze direction, framing), and **what makes it clickable**. Load
   `thumbnail-best-practices` to name the axes.

4. **Decide what to adapt and what to change — the step that avoids
   plagiarism.**
   Keep: composition, hierarchy, contrast, type of emotion.
   Change: the topic, the subject, the palette if it is someone's brand, the
   text.

5. **Check against your own rubric before generating.** If the reference works
   because of a big logo or because it repeats the title, here that subtracts:
   `not_redundant_with_title` carries 25 points and `logos` penalises more than
   one. The reference does not override the channel's rubric.

6. **Generate**, describing the **new** topic, not the reference's:
   ```
   python3 tools/generate_image.py --type thumbnail \
     --prompt "<new topic>. Use the composition of Reference Image 1: <formula>" \
     --ref REFERENCE:composition --ref face.jpg:likeness --dry-run
   ```
   A hard rule about the reference: **if another person appears in it, do not
   pass it as `--ref`**. Describe its composition in the prompt and leave it at
   that. Passing someone else's face is how it ends up in the image.

   If the creator appears, or nobody does, it can go in as a reference.

7. Drop `--dry-run`, generate, **open the result**, and offer one concrete
   adjustment — not a numbered menu.

## SOURCES

The generated image is `source: generated`: an artefact, not a prediction. The
reference's score is `heuristic`, unvalidated against CTR. When delivering,
name the model and say what it was inspired by.
