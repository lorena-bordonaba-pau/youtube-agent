# Memory index

One file per field. This index is read at start-up; the content lives in the
files, never here.

**On a fresh install everything is unpopulated.** That is normal, and the agent
should say so rather than paper over it. Memory is built through use, from real
data, not by filling in templates in one sitting.

## Who you are and what the channel is

- [Creator profile](creator_profile.md) — **not populated**
- [Positioning](channel_positioning.md) — **not populated**
- [Voice profile](voice_profile.md) — **not populated**: built by `script-writing` from real transcripts
- [Loose facts](facts.md) — **not populated**

## How to work

- [Working preferences](coach_preferences.md) — **not populated**
- [Imposed rules](rules.md) — **deliberately empty**: only what you ask for

## What has been learned

- [History and outcomes](conversation_journal.md) — **not populated**
- [SOP](sop/README.md) — how the distilled procedures get generated

## How this grows

When the agent learns something **stable** — not what only matters in one
conversation — it writes or updates the relevant file and adds its line here.
Before creating a new file, check whether one already covers it.

Feedback files (`feedback_*.md`) and project files (`project_*.md`) accumulate
as you go, and they are what end up calibrating the rubrics in
`config/rubrics/`: every axis should be able to cite the memory that justifies
it.

## A note on freshness

Every figure stored here is from the date it was written. For current figures,
run the corresponding tool.
