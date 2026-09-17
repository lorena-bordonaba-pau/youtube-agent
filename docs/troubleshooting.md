# Troubleshooting

Exit codes come first, because they tell you what kind of problem you have:

| Code | Meaning | What to do |
|---|---|---|
| `0` | Fine | — |
| `2` | Credentials missing or expired | Step 1 or 2 of [install.md](install.md) |
| `3` | Daily API quota exhausted | Wait until midnight Pacific, or use the cache |
| `4` | Not enough data to answer | Usually real: too few views, or a private video |
| `64` | Bad arguments | Read the tool's `--help` |

---

### "No YOUTUBE_API_KEY and no OAuth token"

The `.env` was not loaded. It is read at import time from the project root, so:
check the file is called exactly `.env`, sits next to `CLAUDE.md`, and that you
opened a new shell after writing it. A variable exported in your shell takes
precedence over the file.

### Tools started exiting with code 2 after a week

Expected while the Google Cloud app is in *Testing*: tokens expire after 7
days. Run `python3 tools/auth_setup.py` again, or publish the app on the
consent screen.

### "Daily YouTube API quota exhausted" (code 3)

`search.list` costs 100 units of the 10,000 you get per day, and it is used by
`yt_search.py` and `kw_research.py`. Use `kw_research.py --no-competition` to
skip it, and rely on the cache in `data/cache/` — `--no-cache` is what forces
a fresh call, so avoid it when you are close to the limit.

### `yt_retention.py` returns nothing for a real video

YouTube applies privacy thresholds: retention is withheld for videos that are
new or low-volume. It comes back as exit code 4, not as zero, on purpose.

### Transcripts fail

It tries YouTube captions first, then falls back to `whisper-cli` on downloaded
audio. If both fail: check the video is public and that `yt-dlp` is up to date
(`pip3 install -U yt-dlp`). Auto captions are unreliable word by word — never
quote them verbatim without checking the video.

### The image model ignores the aspect ratio

Known and handled. `fal-ai/nano-banana` ignores `image_size` and letterboxes
its output. `generate_image.py` measures the downloaded file, trims black bars
and forces the exact size. If you see the warning repeatedly, the model is
ignoring the prompt instruction — try another slug in
`config/image_providers.json`.

### "No model slug configured for action 'generate'"

Deliberate. A made-up slug burns credits and returns 404, or generates with a
different model. Find the model at
[fal.ai/explore/models](https://fal.ai/explore/models) and write its slug into
`config/image_providers.json`.

**Probing slugs by sending an invalid payload does not work**: fal's queue
returns 200 and only validates in the worker, so a bad path only shows up on a
real call.

### "FAL_KEY is stored TWICE"

A double paste into a hidden input field. The tools detect the exact case and
use the first half so the call still works, but fix the stored value.

### The agent gives generic advice

Check `python3 tools/init.py`. If it says `NOT PERSONALISED`, section 1 of
`CLAUDE.md` and `channel_context` are still empty — see step 4 of
[install.md](install.md). That is almost always the cause.

### The agent answers about itself from memory

That is a bug in the behaviour, not the code. The `transparencia` skill exists
precisely to stop it. Ask again naming the file: *"read `TOOLS.md` and quote
it"*. If it keeps happening, open an issue.

### A score looks too confident

Every score is `heuristic` and the rubrics ship uncalibrated
(`validated_against_ctr: false`). If the agent presents one as a CTR
prediction, that is a contract violation — worth an issue.
