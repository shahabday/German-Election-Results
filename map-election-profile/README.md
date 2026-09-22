# German Voting Profile — All Elections Blended

A sixth, fully independent visualization alongside [`map`](../map/), [`map-municipality`](../map-municipality/),
[`map-trends`](../map-trends/), [`map-demographics`](../map-demographics/),
[`map-timeseries`](../map-timeseries/) and [`map-election-timeseries`](../map-election-timeseries/) -
none of those are touched by this one. Where the other election apps look at one
election type at a time, this blends **all four** (Bundestag, Europawahl, Landtag,
Kommunalwahl) into one picture per municipality: which party has this place *actually*
supported, once you stop looking at any single vote in isolation - and do the four
election types even agree with each other?

Run locally:
```
python build_election_profile_data.py   # reads map-municipality/ output, which must already be built
python -m http.server 8426 --directory map-election-profile
```
(or use the `election-map-election-profile` entry in `.claude/launch.json`.)

## The year window is the whole point

A single fixed all-time blend (1990-2026) would average together genuinely different
eras - a place that was solidly SPD in the 90s and is solidly AfD now would come out
looking like neither, which is actively misleading, not just imprecise. So the year
window is a first-class control here, not an afterthought:

- Two sliders (**From** / **To**) let you pick any window
- Presets: **All time**, **Last 10y**, **Last 5y**, **Latest only** (just the most
  recent election of each type)

Scrubbing the window changes the picture dramatically and correctly: the full 1990-2026
blend shows the long-run CDU/CSU-vs-SPD map most people expect: shrink the window to the
last 10 years and the AfD's rise across the former East becomes visible; shrink further
to "Last 5y" and it dominates almost the entire East, matching the real 2024 state
election results in Thuringia/Saxony/Brandenburg.

## How the blend works

For each municipality, for each of the 4 election types, first average that party's
share **across every election of that type inside the window** - then average those
(up to 4) type-level numbers together. This two-step average is deliberate: Bundestag
has run ~9 times since 1990, Europawahl only ~4 times, and Landtag/Kommunalwahl run on
each state's own schedule - a single flat average across every individual election
would let whichever type happens to have more historical elections dominate the result
just by having more data points, not because it's more electorally important.

Two views:
- **Dominant party** - color = the area's single best-supported party in the blend
- **Consistency** - color = how much the 4 election types actually agree with each
  other on that party (bright = they agree; dim = split-ticket - see below)

## What "consistency" surfaces

Hovering any area shows exactly which party each contributing election type favored,
e.g. *"Bundestag: CDU · Europawahl: CDU · Landtag: CDU · Kommunalwahl: Sonstige /
lokale Listen"*. Kommunalwahl (local council elections) commonly diverge from the other
three because independent/local lists (Freie Wähler, "Sonstige / lokale Listen") are
far more competitive at the purely local level than in Bundestag or Landtag races -
this is a real, well-documented feature of German local politics, not noise. Because of
this, literal unanimous 4/4 agreement across the whole 1990-2026 window is genuinely
rare (~3% of municipalities) even though most areas still look solidly consistent
(3-of-4, rendered as a bright-but-not-maximal teal) - the "Fully agree" stat and the
continuous color gradient are measuring different things and will legitimately disagree
with each other; that's not a bug.

## A party outside the local top 5 counts as 0, not blank - the opposite choice from `map-election-timeseries`

Each area's source file only keeps its top 5 parties per year (the same resolution
every app in this project works at). For a plain absolute-level line chart
(`map-election-timeseries`), the honest choice was to leave those points blank rather
than guess. Here, computing an *average*, the opposite choice is more honest: a party
that only occasionally cracks the top 5 should pull the average down toward its
typical (low) support, not get excluded from the years it under-performed and so look
artificially strong. Both scripts document this explicitly rather than picking silently.

## No new data prep

Like `map-election-timeseries`, this reads `map-municipality`'s already-built per-year
files directly (`ags -> {w, s, b: [[party,share],...top5], t: turnout}`) and computes
the blend entirely client-side, since the window is arbitrary and user-chosen - there's
nothing meaningful to precompute in Python beyond copying the source files in.
`build_election_profile_data.py` copies all 4 election types (all states, all years) and
the municipality boundary, then writes one manifest. On load, the app fetches roughly
260 small per-year files up front (a few seconds once, locally) so the map and every
slider move afterward are instant - no re-fetching mid-interaction.
