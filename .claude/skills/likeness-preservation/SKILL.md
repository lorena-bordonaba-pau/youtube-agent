---
name: likeness-preservation
description: Preserve the creator's exact facial identity when generating or editing images. Triggered whenever an image is meant to include a real person.
---

# Facial identity preservation

## WHEN

Any image that should include the creator, or any real person. Load it
**before** generating, not after seeing the face come out wrong: a lost
identity is not recovered by iterating the prompt.

**If a face was not explicitly asked for, do not put one in.** When in doubt:
objects, text, graphics or abstract. An invented person in the thumbnail of a
channel with a recognisable face breaks the brand.

## EXECUTION ORDER

1. **Get a sharp facial reference.** In order of quality:
   - A photo the creator provides in this conversation.
   - An image generated earlier in this conversation where the face came out
     well.
   - One of their own thumbnails with the face clear and large:
     ```
     python3 tools/yt_recent_videos.py --limit 15 --stats
     python3 tools/yt_thumbnails.py --video ID
     ```
     And **open it** to confirm the face is visible. A blurred, profile or
     obscured face guarantees a bad result.

2. **Do not proceed without a confirmed reference.** If there is none, say so
   and ask for a photo. Generating "something similar" is worse than not
   generating.

3. **Label it with the `likeness` role**
   ```
   python3 tools/generate_image.py --prompt "..." --type thumbnail \
     --ref path_to_the_face.jpg:likeness
   ```
   The role does two things: it places the reference **first** and it activates
   the exact-identity clause in the prompt. Without the role, neither happens.

4. **When refining**, the image to edit goes in `--image` and the face in
   `--ref face.jpg:likeness`. Never the other way round.

5. **Verify by opening the result.** The criterion:

   | Acceptable | Not acceptable |
   |---|---|
   | Different pose, different angle | Different facial features |
   | Different expression | Someone who "looks like them" |
   | Different light, different clothes | A clearly generated face |

   If it is not recognisably the same person, redo it with a better reference.
   Do not deliver it saying "it came out close".

## WHAT THE TOOL ALREADY DOES

When `generate_image.py` detects a reference with the `likeness` role, it
prepends the exact-identity clause and the prohibition on cropping at the neck.
There is no need to repeat it in `--prompt`; verify it with `--dry-run`.

## SOURCES

`source: generated`. A well-preserved face is still an artefact, not a
photograph: if it is used publicly, say so.
