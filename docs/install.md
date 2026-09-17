# Install guide

This page is written so an AI agent can follow it end to end. If you are a
person, it works for you too — it is just unusually explicit.

> **Agent:** follow these steps in order. Ask the human only for the two values
> marked **ASK THE USER**. Never invent a key. After each step, run the check
> and report what it said before moving on.

---

## Step 0 — Requirements

- Python 3.10 or newer
- [Claude Code](https://claude.com/claude-code)
- A Google account with access to the channel you want to analyse
- Optional: `yt-dlp` and `whisper-cli` for transcripts
- Optional: a [fal.ai](https://fal.ai) key or an image MCP, for the visual branch

```bash
git clone https://github.com/lorena-bordonaba-pau/youtube-coach-harness.git
cd youtube-coach-harness
pip3 install -r requirements.txt
```

**Check:** `python3 tools/init.py` prints a status block without crashing.

---

## Step 1 — API key (60 seconds, unlocks public data)

This is enough for: any channel's stats, video data, search, thumbnails,
transcripts, keyword research and competitor outliers.

1. Open [Google Cloud Console](https://console.cloud.google.com/) and create a
   project.
2. **APIs & Services → Library**, enable **YouTube Data API v3**.
3. **APIs & Services → Credentials → Create credentials → API key**. Copy it.
4. **ASK THE USER** for that key, then:

```bash
cp .env.example .env
# write the key into .env as:  YOUTUBE_API_KEY=AIza...
```

**Check:**

```bash
python3 tools/yt_channel_stats.py --channel UCBJycsmduvYEL83R_U4JriQ --md
```

Should print stats for that channel. If it says *"No YOUTUBE_API_KEY"*, the
`.env` was not picked up — start a new shell.

> **Security:** never print the key back to the user, never paste it into a
> file other than `.env`, never commit it. `.env` is git-ignored.

---

## Step 2 — OAuth (5 minutes, unlocks *your own* analytics)

Only needed for private data about your channel: retention curves, traffic
sources, demographics, real search terms, monetisation thresholds. Skip it if
you only want competitor research.

1. In the same project, **enable YouTube Analytics API** as well.
2. **OAuth consent screen** → **External** → fill in the minimum → **add
   yourself as a test user**.
3. **Credentials → Create credentials → OAuth client ID** → type **Desktop
   app**. Download the JSON.
4. Save it as exactly:

```
data/auth/client_secrets.json
```

5. Authorise. **This command opens a browser on purpose** — it is the only one
   that does:

```bash
python3 tools/auth_setup.py
```

Three read-only scopes are requested: `youtube.readonly`,
`yt-analytics.readonly`, `yt-analytics-monetary.readonly`. **The harness cannot
publish or change anything on your channel.**

> While the app is in *Testing*, Google expires the token after 7 days. When
> tools start exiting with code 2, run `auth_setup.py` again. Publishing the
> app on the consent screen avoids it.

**Check:** `python3 tools/yt_report.py --md` prints your own report.

---

## Step 3 — Image provider (optional)

Two routes. The skills never name a provider; you choose in
`config/image_providers.json`.

**fal.ai over REST:** add `FAL_KEY=` to `.env`
(get one at [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys)).

**An image MCP** (Higgsfield or any other): declare the server in `.mcp.json`,
set `"provider": "mcp"` in the config, and adjust the `tools` map. In this mode
the tools do not generate: they return the exact call for the agent to run,
because a script cannot invoke an MCP tool from the session.

**Check, spends nothing:**

```bash
python3 tools/generate_image.py --type thumbnail --prompt "a test" --dry-run --md
```

---

## Step 4 — Tell it who you are

**This is the step people skip, and the one that decides whether the agent is
any use.** Without it you get textbook advice.

**ASK THE USER** for: their channel topic, their language, and who watches —
then fill in:

**`CLAUDE.md`, section 1.** Replace the bracketed placeholders. Be as specific
as a brief, not as a bio: *"people newly diagnosed with coeliac disease who do
not know where to start"* is a niche; *"people interested in cooking"* is not.

**`config/config.json`:**
- `channel_context` — describe the channel the way you would to a consultant
  charging by the hour.
- `language` / `region` — drive keyword autocomplete and transcription
  (`en`/`us` by default).

**`config/channels_lists.json`** — competitors, inspirations, neighbourhood.
You can leave it empty and ask the agent to propose them after step 2.

**Check:** `python3 tools/init.py` no longer says `NOT PERSONALISED`.

---

## Step 5 — First measurement

```bash
python3 tools/yt_report.py     # baseline and first snapshot
```

Open Claude Code in the directory and ask it *"how's the channel doing?"*.

---

## Verifying the install

```bash
python3 tests/test_offline.py   # 12 tests, no credentials, no quota
python3 tools/init.py           # status and what is still missing
```

The acceptance test for the agent itself: ask *"what is the tool execution
order for each skill?"*. It must read the `SKILL.md` files and quote them, not
improvise.

---

## If something breaks

See [troubleshooting.md](troubleshooting.md).
