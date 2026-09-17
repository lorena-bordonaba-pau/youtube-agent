# Tool catalogue

28 scripts: 20 data tools, 4 for the visual branch and 4 utilities. All are run
from the project root and return JSON by default; `--md` gives readable output.

**How to read the `source` column** — it determines how each figure may be
cited. See the table in section 3 of `CLAUDE.md`.

Flags common to all: `--md`, `--no-cache`.
Exit codes: `0` OK · `2` credentials · `3` quota exhausted · `4` no data · `64` bad usage.

## Authentication: two levels

| What you have | What works |
|---|---|
| `YOUTUBE_API_KEY` in `.env` | Everything public: any channel, video stats, search, thumbnails, transcripts, keywords, outliers |
| OAuth (`data/auth/`) | The above, **plus** your own channel's private analytics |

Tools marked 🔑 need only a key. The rest need OAuth because the data is
private and no key can reach it.

## Your own channel's analytics

Require OAuth. Private data for the authorised channel.

| Tool | What it does | Command | `source` | Quota |
|---|---|---|---|---|
| `yt_report` | Full report + snapshot to history | `python3 tools/yt_report.py [--days 28]` | `youtube_api` | low |
| `yt_analytics` | Daily series: views, retention, subs, engagement | `python3 tools/yt_analytics.py [--days 28]` | `youtube_api` | low |
| `yt_top_videos` | Videos by views or by retention | `python3 tools/yt_top_videos.py [--days 90] [--limit 25] [--by-retention]` | `youtube_api` | low |
| `yt_video_analytics` | Day-by-day evolution of one video | `python3 tools/yt_video_analytics.py --video ID` | `youtube_api` | low |
| `yt_retention` | **Retention curve: where people leave** | `python3 tools/yt_retention.py --video ID [--threshold 1.5]` | `youtube_api` | low |
| `yt_search_terms` | **Real search terms bringing traffic** | `python3 tools/yt_search_terms.py [--type YT_SEARCH\|RELATED_VIDEO]` | `youtube_api` | low |
| `yt_traffic` | Traffic sources, with readable labels | `python3 tools/yt_traffic.py [--days 28]` | `youtube_api` | low |
| `yt_demographics` | Audience age and gender | `python3 tools/yt_demographics.py [--days 90]` | `youtube_api` | low |
| `yt_geography` | Audience by country | `python3 tools/yt_geography.py [--days 90]` | `youtube_api` | low |

## Public data (any channel) 🔑

| Tool | What it does | Command | `source` | Quota |
|---|---|---|---|---|
| `yt_channel_stats` | Subs, views, video count | `python3 tools/yt_channel_stats.py [--channel ID]` | `youtube_api` | low |
| `yt_recent_videos` | Recent videos, with or without stats | `python3 tools/yt_recent_videos.py [--channel ID] [--limit 15] [--stats]` | `youtube_api` | low |
| `yt_video_stats` | Views, likes, duration, tags | `python3 tools/yt_video_stats.py --video ID[,ID2]` | `youtube_api` | low |
| `yt_outliers_channels` | Outliers across competitors and inspirations | `python3 tools/yt_outliers_channels.py [--min-ratio 2.0] [--sample 30] [--list competitors]` | `derived` | medium |
| `yt_outliers_playlist` | Outliers from your saved playlist | `python3 tools/yt_outliers_playlist.py [--days 7]` | `derived` | medium |
| `yt_search` | Search YouTube and flag outliers | `python3 tools/yt_search.py --query "..." [--limit 10]` | `derived` | **100 u/query** |
| `yt_thumbnails` | Download thumbnails + pixel metrics | `python3 tools/yt_thumbnails.py --video ID` | `derived` | low |
| `yt_transcript` | Transcript (captions, or Whisper) | `python3 tools/yt_transcript.py --video ID [--plain]` | `youtube_api` / `derived` | none |

## Own heuristics

**Nothing here is measured data.** When citing any output from this section you
must declare it is an own estimate.

| Tool | What it does | Command | `source` |
|---|---|---|---|
| `kw_research` 🔑 | Keywords by proxy: demand + competition | `python3 tools/kw_research.py --kw "a; b" [--deep] [--no-competition]` | `heuristic` |
| `score_titles` | Scores titles 0-100 with the channel's rubric | `python3 tools/score_titles.py --title "A \|\| B"` | `heuristic` |
| `score_thumbnail` 🔑 | Scores the automatic 40%; the 60% is left to visual judgement | `python3 tools/score_thumbnail.py --video ID \| --image PATH [--title "..."]` | `heuristic` |

The rubrics live in `config/rubrics/*.yaml`. **On a fresh install they are
uncalibrated**: each axis's `memory` field is `null`. Calibrating them — one
lesson from your own channel at a time — is what turns them from a checklist
into an advantage.

## Visual branch

These generate or transform images. **Nothing here is data**: a generated image
measures nothing and predicts nothing about performance.

No skill names a provider: that lives in `config/image_providers.json`. With
`provider: "fal"` it calls fal.ai over REST (needs `FAL_KEY`); with
`provider: "mcp"` the tool does not generate and instead returns the exact MCP
call for the agent to run.

| Tool | What it does | Command | `source` | Cost |
|---|---|---|---|---|
| `generate_image` | Generates according to the target format | `python3 tools/generate_image.py --prompt "..." --type thumbnail\|banner\|profile_image\|general [--ref SOURCE:ROLE] [--dry-run]` | `generated` | **credits** |
| `refine_image` | Edits an existing image without redrawing it | `python3 tools/refine_image.py --image PATH --instruction "..." [--ref face.jpg:likeness] [--dry-run]` | `generated` | **credits** |
| `export_image` | Exact dimensions and weight, local and deterministic | `python3 tools/export_image.py --image PATH --type thumbnail \| --size 1280x720` | `derived` | none |
| `view_channel_packaging` | Downloads a channel's avatar and banner + metrics | `python3 tools/view_channel_packaging.py [--channel ID] [--only avatar\|banner\|both]` | `derived` | low |

**`--dry-run` before spending.** It returns the composed final prompt without
calling the provider. If the prompt does not say what you meant, fix it there.

**Reference roles are mandatory.** `--ref SOURCE:ROLE` with `ROLE` in
`likeness`, `style`, `composition`, `packaging`. The tool rejects a reference
with no role: the role decides ordering and whether the facial identity clause
is applied.

**Thumbnails are always 16:9.** `thumbnail` carries `fixed_ratio` in the config
and the tool validates the ratio before calling the provider.

**No model slug is ever invented.** A `null` slot makes the tool fail with
instructions instead of guessing. Probing slugs with an invalid payload **does
not work**: fal's queue returns 200 and the path error only appears on a real
call.

**The ratio is verified in the file, not trusted to the model.** After
downloading, `generate_image` measures the image, trims black bars if the model
letterboxed, and forces the exact size when the format pins a ratio. All of it
is recorded in the envelope's `notes`.

**Every generation is logged** to `data/images/ledger.jsonl`: model, type,
prompt, file and references. It warns about a repeated prompt before you pay
for it twice, and it is what would one day let you cross which generated
thumbnail was uploaded against the CTR it earned. The `uploaded_to_youtube`
field is filled in by hand.

## Utilities

| Tool | What it does | Command |
|---|---|---|
| `init` | Harness status (run by the start-up hook) | `python3 tools/init.py` |
| `auth_setup` | Re-authorise with Google. **Opens a browser** | `python3 tools/auth_setup.py` |
| `ingest_studio_csv` | Ingests CTR and impressions from the Studio CSV | `python3 tools/ingest_studio_csv.py --csv path.csv` |
| `yt_channels_list` | Lists the configured channels | `python3 tools/yt_channels_list.py [--list competitors]` |

## Quota

The daily YouTube API quota is 10,000 units. Almost every call costs 1–3;
**`search.list` costs 100**, and it is used by `yt_search.py` and
`kw_research.py` (unless you pass `--no-competition`).

Everything is cached in `data/cache/` with a TTL per family: 6 h for your own
analytics, 24 h for other channels and searches, 30 days for transcripts and
thumbnails. `--no-cache` forces the call.

## What does NOT exist here

See `LIMITS.md`. In short: no CTR or impressions via the API, no real search
volume, nothing is published or modified on YouTube — not even a generated
image, which you upload by hand in Studio — and no video is generated or
edited.
