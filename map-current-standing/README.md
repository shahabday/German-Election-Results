# Germany's Current Standing — Rolling Election Composite

An eighth, fully independent visualization alongside [`map`](../map/), [`map-all-elections`](../map-all-elections/),
[`map-trends`](../map-trends/), [`map-demographics`](../map-demographics/), [`map-timeseries`](../map-timeseries/),
[`map-election-timeseries`](../map-election-timeseries/) and [`map-election-profile`](../map-election-profile/) -
none of those are touched by this one.

Where `map-election-profile` *blends* all four election types together into an average, this one does something
different: for a given year, it shows each municipality's **single most recent applicable result**, updated
continuously as you move the year slider - a rolling "best current picture of the whole country," not an average
and not one simultaneous vote.

Run locally:
```
python build_current_standing_data.py   # reads map-all-elections/ output, which must already be built
python -m http.server 8428 --directory map-current-standing
```
(or use the `election-map-current-standing` entry in `.claude/launch.json`.)

## The update rule

For each year from 1990 to 2026:

- A **nationwide** election (Bundestag, or Europawahl in a year with no Bundestag) refreshes **every**
  municipality in the country to that year's result. If both happen the same year (only 2009 in this dataset),
  Bundestag wins - it's "the most important."
- A **state-scheduled** election (Landtag, or Kommunalwahl in a state/year with no Landtag) refreshes only
  *that state's* municipalities. If both happen in the same state/year, Landtag wins.
- If a nationwide election **also** lands in that year, it overwrites everything afterward - nationwide is
  authoritative over a same-year local result.
- A municipality untouched by any election that year simply **keeps carrying forward** whatever it last showed.
  It is never blanked out just because nothing happened there this year.

Because Landtag elections alone already cover almost every calendar year somewhere in Germany, the year slider
runs continuously 1990-2026, not just the years an election happened everywhere.

## The tooltip is the point

Since different municipalities can legitimately be showing results from different source years at the very same
slider position, every municipality's hover tooltip states plainly **which** election its number actually comes
from - e.g. hovering a Brandenburg municipality while the slider sits on 2026 (a year Brandenburg had no election)
shows *"Data from: Bundestagswahl 2025"*, not 2026. Areas that changed in exactly the currently-selected year get
a white outline on the map itself, and a running list of "this year's" elections sits in the side panel.

## No new per-window precomputation, but real per-year materialization

Unlike `map-election-profile` (which computes its blend client-side because the window is arbitrary),
this composite only has 37 fixed candidate years, so `build_current_standing_data.py` fully materializes each
year's result client-side-ready: it walks 1990→2026 once, applying the update rule above and writing a complete
snapshot to `data/prepared/<year>.json` after each step. Every file uses the same `{w,s,b,t}` shape as every other
map in this project, plus two extra fields - `y` (the real source year) and `src` (federal/european/landtag/kommunal)
- that only this app needs, for the tooltip.

## Known caveat: a few municipalities can lag further behind than expected

A handful of municipalities (well under 1% of the total) occasionally show an older result than the rest of the
country even in a year that should have refreshed them nationwide - AGS codes shift slightly across election
years, because of real municipal mergers/boundary changes over three decades, and a shifted code doesn't get
matched by a later dataset's overwrite. This is a data-harmonization limitation shared with every other app in
this project (see `docs/GAPS_AND_LIMITATIONS.md`), not a bug in the update logic - and it's exactly the kind of
thing the tooltip's source-year label is there to surface honestly rather than hide.
