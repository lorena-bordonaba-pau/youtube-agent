# Security

## What this project touches

The harness reads YouTube data with **read-only** scopes and writes only to
your local `data/` directory. It cannot publish, edit or delete anything on
your channel, and there is no code path that tries.

## Credentials

Three secrets may exist on your machine. None of them should ever reach git:

| Secret | Where it lives | Git |
|---|---|---|
| Google OAuth client | `data/auth/client_secrets.json` | ignored |
| Google OAuth token | `data/auth/token.pickle` (mode 600) | ignored |
| API keys (`YOUTUBE_API_KEY`, `FAL_KEY`) | `.env` | ignored |

CI fails the build if any of those become tracked, or if something shaped like
an API key appears anywhere in the tree.

**The tools never print a key.** `load_env()` returns the *names* it loaded,
never the values, for exactly this reason. If you find a code path that logs or
echoes a secret, that is a security bug — please report it.

## Reporting a vulnerability

Open a [security advisory](https://github.com/lorena-bordonaba-pau/youtube-agent/security/advisories/new)
rather than a public issue. Include what you found, how to reproduce it, and
what an attacker could do with it. You will get a first reply within a week.

Please do not include a working exploit in a public thread.

## If you think you leaked a key

1. Revoke it immediately — Google Cloud Console → Credentials, or
   fal.ai → Dashboard → Keys. Revoking is faster than rewriting history.
2. Then clean the history. A key in a public repo is scraped within minutes;
   deleting the commit does not help if it was already pushed.

## Scope

In scope: credential handling, path traversal in the tools, anything that
writes outside the project directory, prompt content that could exfiltrate
local data to an image provider.

Out of scope: YouTube API rate limits, third-party model providers' own
security, and the fact that a generated image is not a measurement (that is
documented behaviour, not a vulnerability).
