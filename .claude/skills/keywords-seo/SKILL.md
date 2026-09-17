---
name: keywords-seo
description: Keywords, tags, description and the search gap. Triggered by "what keywords should I use", "optimise the SEO", "give me the tags", "how do people find me".
---

# Keywords and SEO

## EXECUTION ORDER

1. **Field truth first**
   ```
   python3 tools/yt_search_terms.py --days 90 --type YT_SEARCH
   python3 tools/yt_search_terms.py --days 90 --type RELATED_VIDEO
   ```
   These are the **real** terms people arrive through, and the videos
   suggesting yours. Not an estimate. Starting here rather than with the proxy
   is what separates this skill from a generic keyword generator.

2. **Expand with the proxy**
   `python3 tools/kw_research.py --kw "seed 1; seed 2" --deep`
   `--deep` expands with the alphabet: 26 more autocomplete calls, no API quota
   cost. `heuristic`.

3. **Competitive gap**
   `python3 tools/yt_search.py --query "candidate keyword"`
   **Costs 100 quota units per query.** Cached for 24 h. Look at the median age
   of the results: an old top is a refresh opportunity.

4. Tags and description, crossing the real data from step 1 with the expansion
   from step 2.

## SOURCES

Step 1 `youtube_api` — the only hard data in this skill. Steps 2 and 3
`heuristic` and `derived`. When giving a score, say it is your own.

## OUTPUT

- Main keyword, with the evidence for it (preferably from step 1).
- 8-12 tags.
- A 120-180 word description with the keywords woven in naturally.
- Any keyword that comes only from the proxy and not from real traffic is
  flagged as such.
