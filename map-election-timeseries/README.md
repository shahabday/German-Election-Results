# German Election Results — Time Series Compare

A fifth, fully independent visualization alongside [`map`](../map/), [`map-all-elections`](../map-all-elections/),
[`map-trends`](../map-trends/), [`map-demographics`](../map-demographics/) and
[`map-timeseries`](../map-timeseries/) - none of those are touched by this one. Same
interaction model as `map-timeseries` (click/hover the mini map, or search, to build a
multi-line comparison), applied to election results instead of demographics: pick a
party (or turnout) and watch its trajectory across every election of one type, for
whichever states/counties/municipalities you pick.

Run locally:
```
python build_election_timeseries_data.py   # reads map-all-elections/, map-demographics/ and map-trends/ output, all three must already be built
python -m http.server 8425 --directory map-election-timeseries
```
(or use the `election-map-election-timeseries` entry in `.claude/launch.json`.)

## How it works

- **Election** - Bundestag, Europawahl, Landtag, or Kommunalwahl, same four types as
  every other app here.
- **State** (Landtag/Kommunalwahl only) - these are state-scheduled, not simultaneous
  nationwide votes, so picking one sets the data context for everything else: which
  years exist, which municipalities are searchable, and which parties show up in the
  dropdown. Switching election type or state clears the current comparison, since the
  underlying data source changes entirely and old picks may not resolve under the new one.
- **Metric** - a specific party's vote share, or turnout.
- **Mini map** (States or Counties - Counties only once a state is picked, since
  clicking a *different* state wouldn't make sense mid-comparison) - click to pin a
  line, hover for a temporary preview, exactly like `map-timeseries`.
- **Search** - finds a specific municipality by name (scoped to the selected state, for
  Landtag/Kommunalwahl).

Verified against real, independently-known political history: Munich's CSU Landtag vote
share traces the well-known 2008 collapse (CSU lost its statewide majority that year),
2013 partial recovery, and 2018 collapse (the Grüne surge) - exactly as expected,
end to end from raw data through this chart.

## No new data prep - unlike `map-demographics`/`map-timeseries`

There's no fixed small set of "metrics" here the way `map-demographics` had 14 curated
INKAR columns - the metric is "whichever party you pick," and every party's share for
every area/year is already sitting in `map-all-elections`'s per-year files
(`ags -> {w, s, b: [[party,share],...top5], t: turnout}`). So this app does no
Python-side aggregation at all beyond copying those files in and writing one manifest;
state/county rollups (simple unweighted means, same limitation as `map-timeseries`) are
computed client-side on demand from whichever year files are already loaded.

## A party's value is blank, not zero, outside its local top 5

Each area's file only keeps its top 5 parties per year (same resolution the rest of
this project uses). A party not in that top 5 could mean anywhere from just-under-5th-place
down to 0% - showing it as a flat 0% would claim precision that doesn't exist. This app
leaves those points blank (a gap in the line) rather than guessing, unlike `map-trends`'
swing calculation, which treats "outside the top 5" as 0 for a *delta* - a different,
already-documented tradeoff that doesn't apply to a plain absolute level like this.
