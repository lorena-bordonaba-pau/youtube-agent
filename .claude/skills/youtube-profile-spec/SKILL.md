---
name: youtube-profile-spec
description: Specification for a YouTube profile picture — 1:1, cropped to a circle. Triggered when generating or reviewing a channel profile picture.
---

# Profile picture specification

## WHEN

Any profile picture generation or review.

## THE RULE THAT DECIDES EVERYTHING

It is uploaded **square, 1:1**, but YouTube **crops it to a circle**. Anything
near the corners is lost.

And it is seen small: **32x32 pixels in the comments**. That is the real size
it has to be recognisable at, not the one in your editor.

## EXECUTION ORDER

1. **See the current one**
   `python3 tools/view_channel_packaging.py --only avatar --md` and open it.

2. **Generate**
   ```
   python3 tools/generate_image.py --type profile_image --prompt "..." \
     --ref face_photo.jpg:likeness --dry-run
   ```
   `--type profile_image` already asks for a centred subject, a simple
   background, no text and legibility at 32x32.

   If the creator's face appears, load `likeness-preservation`: in an avatar
   the identity is all there is.

3. **Verify at real size**, which is what almost nobody does:
   `python3 tools/export_image.py --image PATH --size 32x32 --out /tmp/avatar32.png`
   and open that 32x32 file. If you cannot tell who it is at that size, it does
   not work, however good it looks at 800x800.

4. Export the final one:
   `python3 tools/export_image.py --image PATH --type profile_image`

## COMPOSITION

- Subject centred and large: the circle eats the corners.
- Simple, single-colour background, high contrast against the subject.
- **No text and no fine detail.** At 32x32 it is a smudge.
- Colour-consistent with the banner.

## SOURCES

`source: generated` for the image; `derived` for the resizing.
