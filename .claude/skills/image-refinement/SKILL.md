---
name: image-refinement
description: Edit an image that already exists instead of regenerating it from scratch. Triggered by "change the background", "remove the logo", "make it darker", "same but without the text".
---

# Image refinement

## WHEN

There is an image that is already mostly right and one part needs changing.

**The mistake this skill exists to prevent**: passing the nearly-good image as
a *reference* to `generate_image`. The model then draws another similar image
and whatever was working is lost. The image to edit goes in as the **source**,
never as a reference.

## BEFORE SPENDING A CREDIT

If the change is about **size, crop, format or weight**, this is not an edit:
`python3 tools/export_image.py --image PATH --type thumbnail`
It is local, deterministic and free. It redraws nothing.

## EXECUTION ORDER

1. **Open the current image** with the image reading tool and name exactly what
   is wrong. Without that, the instruction comes out vague and so does the
   result.

2. **One instruction, imperative, only the change**
   ```
   python3 tools/refine_image.py --image PATH \
     --instruction "change the background to flat cobalt blue"
   ```
   The tool already adds *"keep everything else exactly as it is"*. Describing
   the whole image in the instruction is what makes it redraw.

   `--type` defaults to `preserve`, which keeps the original's shape. Only
   change it when a different shape was actually asked for.

3. **If there is a face**, pass it as a separate reference:
   `--ref face_photo.jpg:likeness`. The face does **not** go in
   `--instruction`.

4. **Compare source and result by opening both.** An editing model changes
   things it was not asked to more often than you would expect.

5. Iterate one change at a time. Two changes in the same instruction collide.

## SOURCES

`source: generated`. An artefact, not a measurement. Name the model when
delivering.

## OUTPUT

The file path, the model that made it, and **what changed compared to the
source, after looking at both** — not an assumption about what should have
changed.
