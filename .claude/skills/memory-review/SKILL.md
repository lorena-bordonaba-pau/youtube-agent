---
name: memory-review
description: Review the session for stable learnings about the channel, the voice, the formats or the way of working, and propose memory updates for the creator to approve. Run by /remember, and offered before a long session is compacted. Triggered by "remember this", "save what we learned", "update the memory", "what did we learn today". In Spanish, "acuérdate de esto", "guarda lo que hemos aprendido", "actualiza la memoria", "qué hemos aprendido hoy".
---

# Memory review

## WHEN

At the end of a working session, when the creator asks to remember something,
or when the session-start or pre-compaction notice suggests it. Always with the
creator's approval before anything is written.

Memory is what turns a consultant into a coach, but only if what goes in is
**stable** and **true**. A memory full of one-off remarks is noise the agent
then obeys.

## EXECUTION ORDER

1. **Read `memory/MEMORY.md`** and the files it indexes that the session
   touched. Nothing is proposed without knowing what is already there.

2. **List the candidates.** Go through the session and keep only what will
   still be true next month:

   | Keep | Leave out |
   |---|---|
   | A preference the creator stated or corrected ("tables, not prose") | What only matters to today's task |
   | A prediction made and, later, its outcome | Figures that a tool can measure again (store the date and the tool, not the number, unless it is an outcome) |
   | A format, pillar or positioning decision | Guesses about why a metric moved: correlation is not a measurement |
   | A voice trait backed by a verbatim quote | Anything the repo already records (tools, skills, config) |

3. **Find the home of each candidate.** Update the file that already covers
   it; create a new one only when none does, with the same front matter as the
   rest (`name`, `description`, `metadata.type`) and a line in `MEMORY.md`.

4. **`memory/rules.md` is special.** A candidate goes there only if the creator
   **explicitly imposed** it in this session. Quote their words and the date.
   A pattern you noticed is not a rule: propose it for `coach_preferences.md`
   or the journal instead, or leave it out.

5. **Propose, do not write.** Show each change as: file, the exact lines to add
   or replace, and why it is stable. Ask once for approval of the whole batch;
   the creator can drop items.

6. **Write only what was approved**, then update `MEMORY.md` if a file was
   added or its status changed from **not populated**.

## SOURCES

- The session itself and the tool outputs in it: every figure carried into
  memory keeps the `source` label and the date the tool returned it.
- `memory/*.md`: `config`, what was already stored.
- Nothing in this skill calls the YouTube API or spends quota.

## OUTPUT

A short list of proposed changes, grouped by file, each with its reason; then,
after approval, one line per file saying what was written. If nothing stable
came out of the session, say so in one line: an empty review is a valid
result.
