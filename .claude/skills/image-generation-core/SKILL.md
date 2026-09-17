---
name: image-generation-core
description: Base rules for generating any channel image — thumbnails, banner, profile picture, graphics. Triggered by "generate an image", "make me a thumbnail", "create the banner", or before any other skill in the visual branch.
---

# Image generation: base rules

## WHEN

Any generation. The other visual skills depend on this one: if
`generate_image.py` is going to be called, these rules apply.

To **edit** an image that already exists, this is not the skill: that is
`image-refinement`. To change only size or weight, neither of them:
`export_image.py`, which is local and free.

## EXECUTION ORDER

1. **Pick the format before the prompt**
   `--type` decides which technical requirements get prepended to the prompt.

   | `--type` | For what | Pixels |
   |---|---|---|
   | `thumbnail` | Video thumbnail | 1280x720 (16:9) |
   | `profile_image` | Profile picture | 800x800 |
   | `banner` | Channel banner | 2560x1440 |
   | `general` | A graphic, an illustration, anything else | 1920x1080 |

   There is **no separate tool for video thumbnails** here: it is
   `generate_image.py --type thumbnail`. Do not go looking for a
   `generate_thumbnail`.

   **Thumbnails are always 16:9** and the tool validates the ratio before
   calling the provider. If your channel publishes vertical, restore the
   `vertical_thumbnail` format from `_retired_formats` in
   `config/image_providers.json`, and check `memory/rules.md` first in case a
   restriction forbids it.

2. **Label every reference with its role — mandatory**
   `--ref SOURCE:ROLE`, with `ROLE` in `likeness`, `style`, `composition`,
   `packaging`. The source can be a local path, a URL or a `video_id`.

   The tool **rejects a reference with no role** on purpose: the role decides
   the order they are handed to the model and whether the facial identity
   clause applies. Guessing it ruins the face.

   The tool imposes the order: people first, style next, composition last.
   Three references maximum; more dilute the result.

3. **If a person appears, load `likeness-preservation` before generating.**
   A badly resolved face is not fixed by iterating the prompt.

4. **Dry run before spending**
   `python3 tools/generate_image.py --prompt "..." --type banner --dry-run --md`
   Returns the composed final prompt without calling the provider. If the final
   prompt does not say what you meant, fix it here rather than after paying.

5. **Generate**
   `python3 tools/generate_image.py --prompt "..." --type thumbnail --ref photo.jpg:likeness`

6. **Look at the result.** Open the returned file with the image reading tool.
   Delivering an image you have not seen is the easiest mistake to make in this
   branch.

7. **Adjust dimensions with `export_image.py`, never by regenerating.**
   `python3 tools/export_image.py --image PATH --type thumbnail`
   It is deterministic, local and costs no credits. YouTube rejects thumbnails
   over 2 MB and this brings them under without repeating the generation.

## PROMPT RULES

- **No text that was not asked for.** The tool already requests this; do not
  contradict it.
- **Fill the frame.** No borders, no frames, no white margin.
- **Large subject**: between 50% and 70% of the frame.
- **Rule of thirds**: the focal point on an intersection, not dead centre.
- **Other people's watermarks and logos out.** The tool asks for this in every
  prompt.
- **When in doubt, no face.** Objects, text, graphics or abstract before an
  invented generic person.

## PROVIDER

No skill names one. It lives in `config/image_providers.json`:

- `provider: "fal"` — calls fal.ai over REST. Needs `FAL_KEY` in the
  environment (put it in `.env`).
- `provider: "mcp"` — the tool **does not generate**: it returns the exact MCP
  call for the agent to run, because a script cannot invoke an MCP tool from
  the session.

Model slots left at `null` in the config make the tool fail with instructions.
**That is deliberate**: an invented slug burns credits and returns 404, or
generates with a different model without saying so.

## SOURCES

`generate_image` returns `source: generated`. It is neither data nor a
measurement: **it says nothing about how it will perform**. When delivering the
image, name the model that produced it. `export_image` is `derived`.
