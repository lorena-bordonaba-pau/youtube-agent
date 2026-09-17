---
name: analyse-channel-packaging
description: Extract a channel's profile and banner branding before generating new packaging. Triggered by "analyse my banner", "what is this channel's visual brand", "review my channel packaging".
---

# Channel packaging analysis

## WHEN

Before generating a banner or a profile picture, your own or inspired by
another channel. Without seeing the current brand, whatever gets generated will
be generic or will break an identity that already works.

## EXECUTION ORDER

1. **Download and measure both pieces**
   ```
   python3 tools/view_channel_packaging.py [--channel ID] --md
   ```
   Returns the avatar and banner downloaded, with the resolution, contrast and
   saturation of each.

2. **Open both files** with the image reading tool. The pixels tell you whether
   there is contrast; they do not tell you what it conveys.

3. **Read the banner by its centre band.** This is the most common reading
   error: on mobile the top and bottom thirds are cropped away entirely. A
   banner is judged by what survives in that strip, not by what you see on a
   desktop. See `youtube-banner-spec`.

4. **Analyse the elements**
   - Colour scheme, and whether avatar and banner agree with each other.
   - Banner typography: tagline, hierarchy, legibility when small.
   - Avatar: is it recognisable at 32x32, its size in the comments?
   - Banner zones: what sits in the safe band and what is lost to the crop.
   - Identity elements: logos, signature colours, repeated motifs.

5. **Cross against the positioning.** Read `memory/channel_positioning.md`:
   the packaging either backs the channel's promise or contradicts it. That
   crossing is the analysis; describing colours is not.

6. **If you are going to generate**, load `youtube-banner-spec` or
   `youtube-profile-spec` depending on the piece, and pass the current
   packaging as a reference:
   ```
   python3 tools/generate_image.py --type banner --prompt "..." \
     --ref data/packaging/<channel_id>_banner.jpg:packaging --dry-run
   ```
   Identity elements are preserved unless a full, explicit rebrand was asked
   for.

## OUTPUT

A brief in 5-8 bullets: what works, what is lost on mobile, what contradicts
the positioning, and what would stay untouched in a redesign.

## SOURCES

`view_channel_packaging` is `derived`: pixel metrics over images from the API.
The brand reading is the agent's judgement over files it has opened, and is
declared as such. `channel_positioning.md` is `config`, with its date.
