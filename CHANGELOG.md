# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/1.1.0/).

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
