# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/1.1.0/).

## [0.5.2] — 2026-09-28

### Changed
- **`/radar` runs the new `competitor-scan` skill.** The weekly scan lived
  inside the command; it now has the same skeleton as every other skill, and
  the command is a thin entry point like the rest. `transparency` also knows
  where to read commands and the subagent.
- **The SessionStart hook uses `$CLAUDE_PROJECT_DIR`.** With a relative path
  it failed when Claude Code was opened from a subfolder.
- **`.mcp.json` is no longer shipped.** A fork loaded the Higgsfield server
  even though the default provider is fal.ai. Copy `.mcp.json.example` if you
  use an image MCP; `.mcp.json` is git-ignored.

### Added
- `.gitignore` covers `.claude/settings.local.json` and `CLAUDE.local.md`.
- Tests: every command hands over to a skill or agent that exists, every hook
  command reaches its script through `$CLAUDE_PROJECT_DIR`, and the personal
  Claude Code files stay ignored.

## [0.5.1] — 2026-09-27

### Added
- **`topic_tam.py`**: the TAM of a video topic and the views it could bring
  this channel, from the competitor board's data — videos and channels on the
  topic, the views it moved, its ratio spread, and your median × its 25th /
  50th / 90th percentile ratio as floor / expected / ceiling, with your own
  record on the topic next to it. `heuristic`, no API calls.
  `competitor-ideation` sizes each idea with it.
- **Monthly plan tab** on the competitor board: 8 videos a month (2 per
  pillar), editable on the page; the agent writes ideas into it with
  `ArtifactData`, backing outliers verbatim from the board.
- `discovery.market_factor` in `config.json`: how many foreign-market views
  equal one in yours. Defaults to 1.0; foreign-language views are divided by
  it and the language split follows `language` (es, pt, fr, de, it; any other
  language, English included, counts everything as home).

## [0.5.0] — 2026-09-27

### Added
- **Competitor board.** A private web page (a Claude artifact) with every
  long-form video your competitors published in the last 6 months: thumbnail,
  date, views, outlier multiplier and views per hour. You add or remove
  @handles on the page and switch channels on and off; the agent syncs the data
  when you ask it to, because the page cannot call the YouTube API itself.
  `tools/competitor_board.py` builds the data, the `competitor-board` skill
  creates, syncs and reads it, and `/radar` and `competitor-ideation` refresh
  it when one exists. Page copy follows `language` in `config/config.json`
  (Spanish or English).
- **Bought views are flagged.** A video above its channel's median with under
  20% of the channel's usual likes per 1k views is marked as a likely ad and
  left out of the baseline. On a real board, one ad-promoted video posted 323x
  with 25M views and 0.4 likes per 1k. Affiliate links are no signal: almost
  every channel carries them. `/radar` and `competitor-ideation` now apply the
  same check before quoting an outlier.
- Two offline tests: the ad flag (and hidden likes not tripping it), and the
  page fetching nothing but its own published files.

## [0.4.0] — 2026-09-27

### Added
- **`/kickoff`** (`channel-kickoff` skill): builds the channel's strategy with
  someone who knows nothing about YouTube strategy — business and objective,
  audience profile, adjacent interests, four provisional pillars and
  differentiation — one plain question at a time. On an existing channel it
  measures first and ends with an evaluation: what there is, what would be
  right, the gap and the action. Strategy only: competitors, ideas and
  thumbnails are separate flows.
- **`/competitors`** (`competitor-mapping` skill): maps the channels already
  winning with the audience, in any language — a topic winning abroad and
  missing at home is the best opportunity there is. Every channel enters a
  list only after an explicit yes, and the pillars are backed with real
  outliers.
- **`yt_discover_channels.py`**: candidate channels from search terms, with
  configurable thresholds (`discovery` in `config.json`), the declared
  language of each channel and a flag for podcast/interview/live formats.
- `yt_channels_list.py --add / --remove`, so validation writes the lists
  deterministically.
- `memory/strategy.md` with a stage that `init.py` reads to say which step is
  next.
- `youtube-strategist` cold-start mode: pillars from the market when there is
  no catalogue yet.
- `competitor-ideation` builds ideas per pillar, in batches of 8, naming the
  technique behind each.
- Three offline tests (27 in total).

### Fixed
- A Spanish fragment left in `yt_outliers_channels`' notes.

## [0.3.0] — 2026-09-27

### Added
- **`youtube-strategist` subagent.** Defines, measures and reviews content
  pillars, diagnoses ideation vs distribution, and reads the competition's
  editorial structure rather than only its outliers. It reads its method from
  `memory/sop/` and says so when a SOP has not been written yet. It may only
  write inside `memory/` (its own PreToolUse hook), and ends every answer with
  a structured handoff block.
- **Spend guard.** A PreToolUse hook asks before any command that spends
  fal.ai credits (`generate_image`, `refine_image` without `--dry-run`) or 100
  API units (`yt_search`, `kw_research` without `--no-competition`). It asks,
  it never blocks.
- **`deny` rules** on `data/auth/` and `.env`, so tokens and keys never enter
  the model's context.
- **`/pillars` and `/audit`** commands as entry points.
- Spanish trigger phrases in every skill description.
- Every skill now follows the same skeleton: WHEN … SOURCES → OUTPUT.
- Seven offline tests (24 in total), each guarding a failure that actually
  happened or a rule that was only prose.

### Fixed
- **Every generation with a reference image was blocked.** The prompt added
  "Remove any watermark...", and fal.ai's content checker rejects the word
  "watermark" with `content_policy_violation`. Reworded with the same intent.
- **`generate_image` ignored references.** It always used the `generate` slug,
  which is text-to-image and discards `image_urls`. Any `--ref` now selects the
  `edit` model, and a `likeness` reference selects `edit_gpt`.
- `yt_channels_list` (and so `/radar`) crashed with `'str' object is not a
  mapping`: the `_instructions` key in `channels_lists.json` was read as a
  list. Keys starting with `_` are now skipped.
- `PyYAML` was missing from `requirements.txt`, so the scoring tools failed on
  a clean install. CI installed it separately, which hid the problem.
- The CI check that config templates ship empty looked for the old Spanish
  keys, so it always passed. It now checks every list, whatever its name.
- Spanish left inside English messages by the translation ("hace 5 days",
  "Transcrito via", "**Modelo**", ...). The mangled-strings test now looks for
  them. One test wrote into `datos/` instead of `data/`.
- A skill description containing ": " made its front matter invalid YAML.
  Now guarded by a test.

## [0.2.1] — 2026-09-17

### Fixed
- `yt_top_videos` returned `video_id` as `video`, so feeding it into
  `yt_retention` — the exact chain the channel-analytics skill prescribes —
  silently broke. Normalised across every tool, with a test.
- An empty channel list reported "0 outliers" instead of saying no channels
  were configured. It now exits with code 4 and tells you where to add them.
- The cache is versioned (`SCHEMA`), so a change in output shape invalidates
  stale entries. Without it an upgrade kept serving the old field names until
  each TTL expired, invisibly.
- Start-up advice is ordered by dependency, and steps blocked by an earlier
  one are hidden: it used to tell you to run `yt_report.py` before you had
  credentials, which exits with code 2.
- The `data/` directories are shipped on a fresh clone. `.gitignore` excluded
  the directories themselves, and git cannot re-include a file inside an
  excluded directory, so `data/auth/` — where the install guide tells you to
  put `client_secrets.json` — did not exist.
- Skill folder names and their front matter now agree, and the slugs are
  English like the rest.

### Added
- Five more offline tests, each guarding a failure that actually happened:
  field-name drift between tools, cache versioning, shipped directories,
  skill name/folder agreement, and mangled strings left by bulk renames.

## [0.2.0] — 2026-09-17

First public release.

### Added
- **API-key mode.** Eight public-data tools now work with just
  `YOUTUBE_API_KEY`, no OAuth, no consent screen. OAuth is required only for
  your own channel's private analytics.
- **Visual branch**, provider-agnostic: `generate_image`, `refine_image`,
  `export_image`, `view_channel_packaging`, plus 9 skills. fal.ai over REST or
  any image MCP, chosen in `config/image_providers.json` without touching a
  skill.
- **`generated` source type** in the contract, so a model artefact can never be
  cited as a measurement.
- **Aspect ratio verified in the pixels**: the downloaded file is measured,
  letterbox bars are trimmed, and a pinned ratio is enforced after generation.
- **`score_thumbnail --image`**, so a freshly generated thumbnail can be scored
  with the same rubric as a published one.
- **Generation ledger** (`data/images/ledger.jsonl`) with a warning when
  the same prompt was generated recently, so a retry does not silently pay
  twice.
- **Offline test suite** (12 tests) and CI on Python 3.10 and 3.12, including
  hygiene checks for committed credentials and non-empty config templates.
- `docs/install.md` written so an agent can follow it, plus
  `docs/troubleshooting.md`.
- Configurable `language` / `region` for autocomplete and transcription.

### Fixed
- `image_size` was sent as the string `"1280x720"`, which fal ignores. It now
  goes as `{width, height}`, with `aspect_ratio` alongside for models that use
  it instead.
- fal uploads used a single POST to a host that does not resolve. Replaced with
  the real two-step signed-URL flow.
- `refine_image` sent the source image twice, which made some models blend it
  with itself. It also defaulted to `--type thumbnail`, silently imposing 16:9
  on edits; the default is now `preserve`.
- `export_image` could not respect a byte limit on PNG, which has no quality
  lever. It now converts to JPG when a limit is set.
- A usage error exited with code 2, colliding with "credentials missing".

### Notes
- The rubrics ship **uncalibrated** (`validated_against_ctr: false`) and the
  memory starts empty. Both are deliberate: they are meant to be built from
  your own channel, not inherited from someone else's.
