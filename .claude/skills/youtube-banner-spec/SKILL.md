---
name: youtube-banner-spec
description: Technical specification for a YouTube banner — 2560x1440 and the mobile safe zone. Triggered when generating, reviewing or diagnosing a channel banner.
---

# Banner specification

## WHEN

Any banner generation or review. Load it **before** writing the prompt: the
safe zone cannot be fixed afterwards.

## THE RULE THAT DECIDES EVERYTHING

The banner is uploaded at **2560x1440**, but **on mobile only a narrow
horizontal strip across the vertical centre is visible**. The top and bottom
thirds are cropped away entirely.

Everything that matters — text, logo, channel name, faces, branding — goes
**inside that centre band**. Above and below, only simple backgrounds:
gradients, blurs, patterns, flat colour.

A banner that puts the channel name at the top disappears on mobile. It is the
most frequent failure and the most invisible one from a desktop.

## EXECUTION ORDER

1. **See the current banner before replacing it**
   `python3 tools/view_channel_packaging.py --only banner --md`
   and open the file.

2. **Generate with the right type**
   ```
   python3 tools/generate_image.py --type banner --prompt "..." --dry-run --md
   ```
   `--type banner` prepends the critical composition rule with the safe band.
   Check it in the dry run: if that clause is not in the final prompt,
   something is wrong with the configuration.

3. **Verify the result by opening it** and checking, specifically, that with
   the top and bottom thirds covered you can still tell what the channel is
   about.

4. **Adjust dimensions without regenerating**
   `python3 tools/export_image.py --image PATH --type banner`
   Leaves it at exactly 2560x1440. The crop is centred, so if the subject is
   off-centre you need to check it.

## STYLE

- Large, legible text; the banner is seen small on mobile.
- Branding centred, inside the band.
- The channel's palette, for consistency with the avatar. Load
  `analyse-channel-packaging` if you do not know it.

## SOURCES

The image is `source: generated`. The dimensions after `export_image` are
`derived` and verifiable in the file.
