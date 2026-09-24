# German States & Counties — Time Series Compare

A fourth, fully independent visualization alongside [`map`](../map/), [`map-all-elections`](../map-all-elections/),
[`map-trends`](../map-trends/) and [`map-demographics`](../map-demographics/) - none of
those are touched by this one. Where `map-demographics` plots one metric on the whole
country for one year at a time, this plots one metric across *time* for whichever
specific areas you pick - built for questions like "how did Saxony-Anhalt's wages catch
up to Bavaria's" or "is Munich's rent growth actually different from Cologne's."

Run locally:
```
python build_timeseries_data.py   # reads map-demographics/ and map-trends/ output, both must already be built
python -m http.server 8424 --directory map-timeseries
```
(or use the `election-map-timeseries` entry in `.claude/launch.json`.)

## How it works

- **Metric dropdown** - the same 14 county-level income/INKAR metrics `map-demographics`
  has (the only ones with real multi-year data; the 2022 census is a single snapshot and
  can't make a line).
- **Mini map** (States or Counties toggle) - **click** an area to pin its line onto the
  chart, click again to remove it. **Hover** (without clicking) shows a temporary dashed
  preview line - lets you scan around without committing to the comparison.
- **Search box** - type a county or city name (or a state name) to add it directly,
  useful since picking one specific county out of ~400 tiny map polygons is fiddly.
  Matches on the county boundary's own name field, so it finds e.g. "München" as both
  the city itself (kreisfreie Stadt) and its surrounding Landkreis.
- **Comparing list** - doubles as the chart's legend and the removal UI (click the ×).
- Hovering the chart area itself shows a synced tooltip with every selected area's exact
  value at the nearest year, plus a vertical guide line.
- Lines break where a metric has no data for a given area/year rather than being bridged
  by a straight line across the gap - INKAR coverage especially has real holes, and
  drawing through them would imply data that doesn't exist.

## State lines are not population-weighted

Every "state" line here is a simple (unweighted) mean of that state's counties for
whichever counties have data - not weighted by population. A state line therefore treats
its smallest rural county exactly the same as its biggest city when it comes to pulling
the average. This is a real limitation, not just a caveat for the README: there's no
consistent multi-year county population figure in this project to weight by (the only
population data available is the single-year 2022 census snapshot, which can't
retroactively weight a 1995 value without assuming population never changed - false).
If a properly weighted state series is wanted later, it would need per-year county
population data sourced separately.

## Data

Reads `map-demographics/data/prepared/county/<year>.json` (already-built county-year
metric values) and copies them in as-is, adds one new thing: `build_state_rollups()` in
`build_timeseries_data.py` groups counties by their first two AGS digits (the state
code) and averages each metric per state per year, writing `data/prepared/state/<year>.json`.
County and Bundesland boundaries are copied from `map-demographics` and `map-trends`
respectively, so this app has no runtime dependency on either at request time.
