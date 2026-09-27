---
name: channel-kickoff
description: Build the channel's strategy from zero, or evaluate the strategy of an existing channel — business and objective, audience profile, adjacent interests, provisional content pillars and differentiation. Guided for someone who knows nothing about YouTube strategy. Triggered by "/kickoff", "start the channel", "I'm new, where do I begin", "build my strategy", "evaluate my channel's strategy". In Spanish, "empezar el canal", "soy nuevo, por dónde empiezo", "hazme la estrategia", "evalúa la estrategia de mi canal".
---

# Channel kickoff: the strategy

## WHEN

The first thing anyone does with this harness, and whenever the creator wants
the strategy rebuilt. `tools/init.py` points here while `memory/strategy.md`
says `NOT POPULATED`.

It covers **strategy only**: what the channel is for and who it speaks to.
Competitors come after, in `/competitors`, validated channel by channel with
the creator. Ideas, titles, thumbnails and scripts are flows the creator starts
on their own. Do not drift into them here, however tempting.

## THE METHOD

Strategy runs in one direction: **what you sell → who buys it → what that
person wants → what you will talk about**. Every later decision — which
competitor to watch, which idea to record — is checked against these four
answers. A channel with views from people who will never buy has a strategy
problem, not a growth problem.

## HOW TO TALK TO THE CREATOR

They may know nothing about strategy. So:

- **One question at a time**, in plain words, never a form.
- **Offer options with an example each**, plus "something else". Nobody
  answers "what is your awareness level?"; everybody answers "does your viewer
  already know they have this problem?".
- **Say in one line why you are asking.** People answer better when they know
  what the answer changes.
- **Propose, then confirm.** When you can infer a sensible answer, offer it as
  a proposal ("From what you said, I would put the audience at 25-45. Right?").
  Never write it down unconfirmed.
- **"I don't know" is a valid answer.** Record it as unknown; do not invent it.

## EXECUTION ORDER

**0. Pick the mode — measure, do not ask**
```
python3 tools/yt_channel_stats.py
python3 tools/yt_recent_videos.py --limit 50 --stats
```
- Fewer than 5 long-form videos, or no channel yet → **new channel**: the
  audience profile is a declared hypothesis.
- 5 or more → **existing channel**: everything the creator says is checked
  against data, and the kickoff ends with an evaluation (step 7).
- No OAuth token → own analytics are unavailable. Say so, work as a new
  channel, and note that the evaluation needs `data/auth/` set up.

**1. Business and objective**
Ask what the channel sells: a course or community, a service, a product, or
nothing (audience, sponsors, authority). Then who pays (consumers, small
businesses, large companies) and roughly what it costs (tens, hundreds,
thousands). Then the single objective: leads, authority, reach for sponsors,
or sales. Why it matters: a high-ticket B2B service needs few, qualified
viewers; a low-ticket community needs volume.

**2. Audience profile** — seven fields, one question each:
gender, age range, geography (and the vocabulary of that market: words, money,
references that make that viewer feel spoken to), awareness level (does not
know the problem / knows it / is comparing solutions), goals (what they want
to become or achieve), pains (what stops them), and who the channel is NOT for.

In **existing** mode, measure before asking and show the contrast:
```
python3 tools/yt_demographics.py --days 90
python3 tools/yt_geography.py --days 90
```
The gap between the audience the creator believes they have and the one they
have is usually the first finding. Record both.

**3. Adjacent interests**
Propose 5-8 topics outside the core niche that the same viewer already cares
about (someone into running also cares about nutrition, injuries, gear), and
let the creator keep, drop or add. These feed the market map in
`/competitors` as search terms, so write each one the way a viewer would type
it — **in the audience's language and in English**, and in the language of any
other market that is ahead in this niche. Other markets are not noise: a topic
already winning abroad and absent at home is the best opportunity this map can
find.

**4. Provisional pillars**
Four umbrellas, drawn from the core niche plus the strongest adjacent
interests, and checked against goals and pains:
- Distinct from each other — a video fits one pillar, not two.
- Named by what the viewer walks away with, **never by a tool**: the tool is a
  topic inside the pillar and goes stale first.
- Each one must serve the objective from step 1. A pillar that brings the
  wrong viewer is dropped, however popular.

They stay **provisional**: the market has not backed them yet. `/competitors`
will.

In **existing** mode, hand the catalogue to the `youtube-strategist` agent:
it classifies the last 50 long-form videos into these four pillars and returns
views, retention and mismatch per pillar. That measurement goes into step 7.

**5. Differentiation**
One question: "What can you say that others in your niche cannot, or will
not?" — experience, results, a stance, a format. If the answer is "nothing",
say so plainly: it is the most important gap to close, and `/competitors`
helps find it.

**6. Write it down**
- `memory/strategy.md`: every section, dated, each audience line marked
  **measured** or **hypothesis**, and `**Stage:** strategy`. Delete the
  `NOT POPULATED` line.
- `CLAUDE.md` section 1: fill the brackets from steps 1-2 and delete the
  "FILL THIS IN" quote, if it is still there.
- `config/config.json`: `channel_context` as a consultant's brief (who, what
  they sell, what sets them apart), and `language` / `region`.
Show the creator the diff before writing, and write only what they approve.

**7. Evaluation — existing channels only**
Put what the channel does next to what the strategy says it should do. Write
it to `memory/strategy_eval.md`, dated:

| Dimension | What there is (measured) | What would be right | Gap | Action |
|---|---|---|---|---|
| Objective | Who the content attracts today | Who the objective needs | | |
| Audience | Demographics and geography from Studio | Profile from step 2 | | |
| Market vocabulary | What titles and topics sound like today | The audience's words | | |
| Pillars | Catalogue split and mismatch per pillar | The four pillars | | |
| Awareness | Level the current topics assume | Level the audience is at | | |
| Differentiation | What the channel offers today | Step 5 | | |

Every cell in "what there is" carries its source and date. A dimension that
could not be measured says so instead of guessing. End with the three gaps
that matter most, in order.

## SOURCES

Everything the creator says is `config`-grade: their declaration, not a
measurement. Studio demographics and geography are `youtube_api`. The pillar
split from the strategist is `derived`. The evaluation never mixes them
without labelling which is which.

## OUTPUT

1. A short summary of the strategy in five lines: sells, to whom, objective,
   the four provisional pillars, differentiation.
2. The files written, and what each one now says.
3. In existing mode, the evaluation table and the three gaps that matter most.
4. One next step: "Run `/competitors` to map the channels already winning
   with this audience and back the pillars with real videos."
