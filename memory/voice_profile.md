---
name: Voice profile
description: How you sound when you speak: signature phrases, rhythm, hooks, humour. With verbatim quotes.
metadata:
  type: user
---

**NOT POPULATED.** The `script-writing` skill cannot write without this.

It is built from REAL transcripts of your best-retaining videos:

```
python3 tools/yt_top_videos.py --days 180 --by-retention --limit 5
python3 tools/yt_transcript.py --video ID --plain
```

It must carry **verbatim quotes**, not adjectives. "Warm tone" is useless; the
exact phrase you open your videos with is not. Under 200 words or without
quotes, it is too thin and needs redoing.

Inventing the voice when transcripts are available is the error this memory
exists to prevent.
