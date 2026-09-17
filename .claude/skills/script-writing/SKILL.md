---
name: script-writing
description: Write video scripts in the channel's real voice with a validated retention structure. Triggered by "write the script", "give me the hook", "structure this video", "how do I open this one".
---

# Script

## WHEN

Writing or restructuring a script, designing the first-30-seconds hook, placing
re-hooks, reviewing a structure already written.

## EXECUTION ORDER

1. **Check the voice profile**
   Read `memory/voice_profile.md`.

   - If it is populated (more than 150 words, with verbatim phrases), use it
     and skip to step 3.
   - If it is empty or generic, **build it before writing anything**:
     ```
     python3 tools/yt_top_videos.py --days 180 --by-retention --limit 5
     python3 tools/yt_transcript.py --video ID --plain    # the best 3
     ```
     Analyse the real fillers, openings, transitions and closings, and write
     `memory/voice_profile.md` with verbatim quotes.

   Inventing the voice when transcripts are available is the error this step
   prevents.

2. **The SOP has structural primacy**
   Read `memory/sop/scripting_sop.md`. **It is the source of truth for
   structure.** If a formula exists there, the outliers and keywords from the
   next steps inform the TOPIC, they never rewrite the structure.

3. **Validate the topic**
   ```
   python3 tools/yt_outliers_channels.py --min-ratio 2.0
   python3 tools/kw_research.py --kw "main topic; variant"
   ```
   The outliers say which hooks are earning views right now. The keyword score
   is `heuristic`: it orders options, it does not assert demand.

4. **Verify the hook against real retention** — if a comparable video exists
   `python3 tools/yt_retention.py --video ID`
   Look at where the audience dropped in that video and do not repeat the
   pattern. This turns the SOP into something verifiable rather than an
   inherited convention.

5. Write, applying the SOP and the voice from step 1.

## SOURCES

Step 1 `youtube_api` (transcripts). Step 3 `derived` + `heuristic`. Step 4
`youtube_api`. When citing the keyword score, declare it.

## OUTPUT

Whatever was asked for: a hook broken down by seconds, a summary outline, or a
full script. Summary by default; the full script only on confirmation.

Each block declares its job (promise, proof, plan, re-hook) so it can be
measured afterwards with `yt_retention.py`.
