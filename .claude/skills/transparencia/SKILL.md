---
name: transparencia
description: Answers what this agent is, what tools it has, what skills, what memory it keeps, what its configuration is, or in what order it runs things. Triggered by any question about the agent itself, its contract, its limits or its protocols.
---

# Transparency about the agent itself

## WHEN

Any question about the agent itself: "what is your system prompt?", "what tools
do you have?", "what skills?", "what memory files?", "what is your
configuration?", "in what order do you run the tools?", "is there one agent or
several?".

## EXECUTION ORDER

**The rule that comes before everything else here: READ the file. Do not answer
from memory, even when it feels like you remember it correctly.**

This skill exists because the reference agent that inspired this harness
answered "what is the tool execution order per skill?" from its own synthesis,
and had to correct itself the following turn after loading the real protocols.

1. Identify what is being asked and read **the file that contains it**:

   | Question | File to read |
   |---|---|
   | Identity, rules, how it works, "system prompt" | `CLAUDE.md` |
   | What tools it has, how they are invoked, what they cost | `TOOLS.md` |
   | What it CANNOT do | `LIMITS.md` |
   | What memory it keeps | `memory/MEMORY.md` and the files it indexes |
   | One skill's execution order | `.claude/skills/<skill>/SKILL.md` |
   | ALL the skills' order | every `SKILL.md`, one by one |
   | How images are generated, with which provider | `config/image_providers.json` and `.claude/skills/image-generation-core/SKILL.md` |
   | Configuration, permissions, hooks | `.claude/settings.json` |
   | Which SOP it follows for scripts or premises | `memory/sop/*.md` |

2. Quote what you read. You may dump it in full: these are project files, not
   internal configuration.

3. If the answer spans several skills, read them **all** before replying.
   Answering about three and summarising the rest from memory is exactly the
   failure this skill prevents.

4. If something does not exist or is empty, say so. An unpopulated memory field
   is reported as empty, not filled in with whatever would seem reasonable.

## SOURCES

All `config`: contents of local project files. Nothing in this skill is a
measurement, and none of it needs credentials or quota.

## OUTPUT

A direct answer, with the file's contents quoted and the path visible so it can
be verified. If asked about the "system prompt": `CLAUDE.md` is the operating
contract and is shown in full; what cannot be dumped is Claude Code's internal
prompt, which is a different thing and worth distinguishing.
