---
name: competitor-board
description: Create, sync and read the competitor board, a private web page (an Artifact) listing every long-form video your competitors published in the last 6 months, with thumbnail, date and outlier multiplier, filterable by channel, and with likely ad-bought views flagged. Triggered by "make me a competitor board", "sync the competitor board", "I added competitors to the board", "open the competitor board". In Spanish, "hazme el radar de competidores", "sincroniza el radar de competidores", "he añadido competidores", "abre el radar".
---

# Competitor board

## WHEN

- The user wants a visual board of what their competitors publish, or asks to
  create one.
- "Sync the board", or they say they added or removed @handles on the page.
- At the end of `/radar` and `competitor-ideation`, when a board exists: refresh
  it so it matches what was just analysed.

The page cannot call the YouTube API on its own (the artifact sandbox blocks it).
Handles typed on the page are stored in the page's database and show as
**pending** until this skill runs a sync.

## EXECUTION ORDER

### 0. Is there a board already?

Read `memory/competitor_board.md`. If it holds a URL, go to **Sync**. If not, go
to **Create**. Never create a second board when one exists: publishing without
its `url` makes a new page and orphans the list the user built.

### Create (first time only)

1. Build the data from the configured competitors, or from the handles the user
   gives:
   `python3 tools/competitor_board.py --list competitors`
   `python3 tools/competitor_board.py --handles @one @two`
   It adds your own channel automatically (through OAuth) behind the page's
   "include my channel" switch; `--own none` leaves it out.
2. Publish with the `Artifact` tool:
   - `file_path`: `artifacts/competitor-board/index.html`
   - `files`: the tool's `data.publish_files`, **as is**
   - `capabilities`: `{"db": {}}` (the page keeps the competitor list there)
   - `icon`: `radar`
3. Seed the page's list with `ArtifactData` `batch`, one `set` per channel the
   tool returned without `error`: collection `competitors`, `doc_id` = the
   handle lowercased without `@`, data
   `{"handle": "@handle", "enabled": true, "addedAt": "<ISO time>"}`.
   Skip the channel whose `own` is true: it is not a competitor.
4. Write `memory/competitor_board.md` with the URL and the date, and add its
   line to `memory/MEMORY.md`.

### Sync

1. `ArtifactData` `list` of collection `competitors` (page with `cursor` until
   there is no `next_cursor`). Save the documents' `data` objects as a JSON
   array in the scratchpad. Disabled ones stay in: the user may switch them
   back on.
2. `python3 tools/competitor_board.py --handles-file <that file>`
3. Publish with `Artifact`: the board's `url`, `file_path`
   `artifacts/competitor-board/index.html`, `files` = `data.publish_files` as is
   (it already carries `null` for channels that were removed). **Omit
   `capabilities`**: the stored declaration carries forward.
4. Any channel with `error` means the @ does not exist. Tell the user, and
   check for look-alikes: a handle can be squatted by an empty channel (e.g. a
   2-subscriber account holding the obvious name while the real creator uses a
   variant). Resolve the real one with the channel ID from
   `config/channels_lists.json` if the creator is there.

### Monthly plan tab

The page also holds an editable sheet of the videos planned per month, 8 per
month by default (2 per pillar, for a 2-a-week cadence). The user edits it on
the page; you write ideas into it with `ArtifactData`:

- `settings/pillars`: `{"items": [{"id": "p1", "name": "..."}, ...]}`. Take
  the names from `memory/`; never invent a pillar the user has not named.
- `plan/<YYYY-MM>-<slot>`: `month`, `slot`, `pillar` (an id above; pillar
  names are one or two words), `title`, `pattern`, `ref_id` / `ref_title` /
  `ref_channel` / `ref_ratio` / `ref_views` (the main backing outlier,
  **verbatim** from the board data), `format_refs` (**format references**, shown
  as links: `[{"id", "title", "channel", "ratio", "views"}]`, verbatim from the
  board data; the user can add and remove them on the page), `tam_views` (the
  topic's `tam_views_6m` from `topic_tam.py`), `status` (index string: 0 idea
  … 4 published, 5 dropped).
- `views_floor` / `views_mid` / `views_ceiling`: expected views from
  `python3 tools/topic_tam.py --topic "Name::regex"` (a `heuristic` estimate:
  write the topic, its market ratio and the user's own record on it into
  `views_basis`, shown when hovering the expected views). When the user has 2 or more videos on the topic, their own median
  beats the market projection. `views_real` is filled after publishing.
- Read the rows before writing and pin `if_version`: the user may have edited
  them. Never overwrite a title or note the user wrote.

### Reading the board (before quoting any figure from it)

- `ratio` is against the channel's own median, so a small channel can post
  100x with modest views. Quote the views next to the ratio.
- `ad_suspect` videos are left out of the median and hidden by default. An
  outlier with collapsed likes per 1k views is bought reach, not a format that
  worked: never recommend copying it.
- Videos under about 7 days old carry a deflated ratio; 1-4 week old videos run
  high on growing channels. Say so when the top of the list is that young.
- Fewer than 15 videos in a channel's window makes its median unstable.

## SOURCES

`competitor_board.py` is `derived` (the ratio and views per hour are computed
over API data). `ad_suspect` is `heuristic`: declare it as an estimate, never as
YouTube data. `paid` is `youtube_api` (the creator's own declaration) and marks a
sponsorship, not bought views. The competitor list on the page is user data, not
a measurement.

## OUTPUT

The board's link, plus what changed in one short block: channels added,
removed, not found, and how many videos and likely ads the sync produced. If
asked what stands out, the top organic outliers from `data.top_organic_outliers`
with title, channel, ratio and views **verbatim** from the tool.
