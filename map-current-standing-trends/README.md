# Germany's Current Standing — Trends

A ninth, fully independent visualization alongside [`map`](../map/), [`map-all-elections`](../map-all-elections/),
[`map-trends`](../map-trends/), [`map-demographics`](../map-demographics/), [`map-timeseries`](../map-timeseries/),
[`map-election-timeseries`](../map-election-timeseries/), [`map-election-profile`](../map-election-profile/) and
[`map-current-standing`](../map-current-standing/) - none of those are touched by this one.

Same idea as `map-current-standing` (a rolling "each area's most recent applicable election" composite, refreshed
nationwide by Bundestag/Europawahl and per-state by Landtag/Kommunalwahl), but as a click-to-compare trend line
instead of a map - reusing the area-picking UI from `map-election-timeseries`.

Run locally:
```
python build_current_standing_trends_data.py   # reads map-current-standing/ output, which must already be built
python -m http.server 8429 --directory map-current-standing-trends
```
(or use the `election-map-current-standing-trends` entry in `.claude/launch.json`.)

## Why this looks different from every other line chart in this project

`map-election-timeseries` plots a party's share only at the years that specific election type actually happened for
that area - sparse points, real gaps between them. This tool instead plots the **current-standing composite**
directly: a value for literally every year 1990-2026, because the composite always has *something* to show (either
a fresh result or a carried-forward one). The result is a deliberate step shape - flat while an area's number is
just being carried forward, then a sharp jump the instant that area gets its own next election. A dot marks only
the years a line actually changed, so you can tell "stayed exactly the same" from "coincidentally polled the same
number twice."

This is most interesting for single-area, single-party views (e.g. the built-in Sample: AfD's current standing in
Baden-Württemberg vs. Saxony-Anhalt) - the jumps land at genuinely different years for the two states, because they
vote on independent schedules, and that's the whole point.

## No new computation

This reads `map-current-standing`'s already-built yearly composite files directly (same `{w,s,b,t,y,src}` shape) and
copies them wholesale, plus the county/state boundary layers `map-election-timeseries` already established for
area-picking. All ~37 years (~65MB) are fetched once up front at load, exactly like `map-election-profile`, so
every click/search afterward is instant with no further network round-trips.
