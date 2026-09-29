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
git clone https://github.com/lorena-bordonaba-pau/youtube-agent.git
cd youtube-agent
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

**An image MCP** (Higgsfield or any other): copy `.mcp.json.example` to `.mcp.json`
(git-ignored), declare the server there,
set `"provider": "mcp"` in the config, and adjust the `tools` map. In this mode
the tools do not generate: they return the exact call for the agent to run,
because a script cannot invoke an MCP tool from the session.

**Check, spends nothing:**

```bash
python3 tools/generate_image.py --type thumbnail --prompt "a test" --dry-run --md
```

---

## Step 4 — Build the strategy: `/kickoff`

**This is the step people skip, and the one that decides whether the agent is
any use.** Without it you get textbook advice.

Open Claude Code in the directory and run **`/kickoff`**. No strategy
knowledge needed: it asks one question at a time, in plain words, with
examples —

1. What the channel sells (or that it sells nothing) and the one objective.
2. Who the viewer is: age, place, what they already know, what they want,
   what stops them.
3. Which neighbouring topics that viewer also cares about.
4. Four provisional content pillars built from those answers.
5. What you can say that others in your niche cannot.

It writes `memory/strategy.md`, fills in section 1 of `CLAUDE.md` and
`channel_context` / `language` / `region` in `config/config.json` — showing
you the changes before writing.

If the channel already has videos, it measures them first and ends with an
evaluation: what there is, what would be right, and the gaps that matter most.

**Then run `/competitors`** (needs the API key from step 1). It searches for
the channels already winning with your audience — in any language, because a
topic winning abroad and missing at home is the best opportunity there is —
and asks you about each one before adding it to `config/channels_lists.json`.
It ends by backing your pillars with real outlier videos.

Ideas, titles, thumbnails and scripts come after, whenever you ask for them.

**Check:** `python3 tools/init.py` no longer says `Strategy: NOT STARTED`.

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
