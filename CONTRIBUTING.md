# Contributing

Thanks for looking. This project has one rule that overrides every other
preference, and a few conventions that follow from it.

## The rule

**A tool must never present an estimate as a measurement.**

Every tool returns a `source` field. If you add one, pick the honest value:

| `source` | Use it when |
|---|---|
| `youtube_api` | The figure came straight from Google's API |
| `derived` | You computed it in code over API data |
| `heuristic` | It is your own rubric, proxy or weighting |
| `config` | It is the contents of a local file |
| `generated` | It is an artefact from an external model |

If you are unsure between `derived` and `heuristic`, it is `heuristic`.

A corollary that matters: **if a tool cannot measure something, it should
return the question rather than a plausible number.** `score_thumbnail.py` is
the reference implementation — it scores 40% and hands back the other 60% as
unanswered questions.

## Before opening a pull request

```bash
python3 tests/test_offline.py    # 12 tests, no credentials, no network, no quota
python3 tools/init.py            # must not crash
```

CI runs the same suite on Python 3.10 and 3.12, plus hygiene checks that fail
if a credential is committed or if the config templates ship with real data.

## Conventions

- **Exit codes** come from `tools/lib/contract.py`: `2` credentials, `3` quota,
  `4` no data, `64` bad usage. Never let a raw traceback escape.
- **Every tool** takes `--md` and `--no-cache`, and returns the standard
  envelope via `envelope()` / `emit()`.
- **Cache anything that costs quota.** `search.list` costs 100 units of 10,000.
- **Comments explain why, not what.** If a line is surprising, say what would
  go wrong without it.
- **English** in code, comments and docs. The agent's *replies* follow the
  channel's language, set in `CLAUDE.md`.

## Adding a skill

A skill is a `.claude/skills/<name>/SKILL.md` with front matter and a fixed
tool execution order. Look at an existing one first. Two things people get
wrong:

- The order is the point. "Run the tool that measures before the one that
  opines" is not decoration.
- Declare the `source` of each step in a `SOURCES` section, so the agent knows
  how to cite it.

## What will get pushed back

- A tool that returns a number it cannot justify.
- A rubric axis with no `memory` field and no explanation of where it came from.
- Anything that writes to YouTube. The scopes are read-only and stay that way.
- Committing your own channel's data. `data/` and the config templates must
  stay empty in the repo.

## Reporting a problem with the agent's behaviour

Bugs in *what the agent says* are as real as bugs in the code. If it presented
a heuristic as a measurement, or answered about itself from memory instead of
reading the file, that is a legitimate issue — please include the exchange.
