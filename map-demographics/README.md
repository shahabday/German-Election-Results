# German Demographics & Economy Map

A third, fully independent visualization alongside [`map`](../map/), [`map-municipality`](../map-municipality/)
and [`map-trends`](../map-trends/) - none of those are touched by this one. Where the
other three plot election results, this one plots the demographic and economic
covariate data harvested earlier in this project (`processed/covariates/`), as spatial
context for *why* the election patterns look the way they do (income, age structure,
migration, housing, unemployment, etc.).

Run locally:
```
python build_demographics_data.py   # reads processed/covariates/ and map-municipality/data/prepared/
python -m http.server 8423 --directory map-demographics
```
(or use the `election-map-demographics` entry in `.claude/launch.json`.)

## Two resolutions, because the two source families don't share one

- **Municipality (~10,800 Gemeinden), single snapshot: Zensus 2022.** Age structure,
  foreign nationals, migration background, household size, housing type, vacancy,
  owner-occupied share, rent. One point in time - the German census doesn't run
  annually, so there's no year slider here. Reuses `map-municipality`'s
  `gemeinden.geojson` boundary exactly (same AGS keys), copied in at build time so this
  app has no runtime dependency on that one.
- **County (~400 Kreise), multi-year: income + INKAR.** Average gross wage and household
  income (VGRdL, 2001-2021), plus a curated subset of INKAR indicators (unemployment,
  GDP/capita, median income, tax capacity, industry employment share, commuter balance,
  in/out-migration rates, asylum seekers, rent, over-indebtedness rate). Boundaries are
  `m-ad/geofeatures-ags-germany`'s `counties.json` (GADM-derived, same source family as
  `map-trends`' state outlines) - fetched once to `data/boundaries/counties_raw.geojson`
  and cleaned into `data/prepared/counties.geojson`.

Switching resolution swaps both the boundary layer and the metric list; the year slider
only appears for County mode, and only shows years the *currently selected metric*
actually has data for (each metric was built from a different source file with its own
coverage window - see below).

## Comparing across years: two things that sound similar but aren't

Toggling the year slider on its own only re-colors each county by its *rank within that
one year* - which hides real growth, because every year gets recolored dark-to-gold
across its own range regardless of the underlying numbers. Two separate controls fix
two separate parts of that:

- **Scale: "This year" vs. "Fixed (whole period)"** (Level view only). "This year"
  recomputes the color range from whatever's currently loaded - good for seeing spread
  *within* a year, useless for seeing growth *across* years. "Fixed" colors every year
  against one range computed once, from every county-year on record for that metric
  (`global_domain` in `metrics_manifest.json`, precomputed in the build script). Under
  "Fixed", the former East visibly darkens in 2000 and brightens by 2020 - real growth -
  while staying visibly behind the West's brightness the whole time, since both are
  judged against the same absolute yardstick.
- **View: "Growth vs. prev. year"** - a second, independent axis: instead of the level,
  shows the change since the last year that metric has data for (not always exactly one
  calendar year - some INKAR series have gaps). Diverging blue/red scale (blue = more,
  red = less), same delta-first convention as `map-trends`' swing maps, so a metric that
  didn't exist yet or was near zero doesn't produce a nonsensical infinite growth rate.
  Tooltip shows both the raw before/after values and the relative % change (only past a
  sane baseline, same guard as `map-trends`).

## Why only some INKAR columns

The raw INKAR indicator file has ~55 columns per county-year. Most are either
near-duplicates of something else already included, essentially empty before the
mid-2000s, or not obviously interesting for this project. Rather than dump all 55 into
a dropdown, `COUNTY_METRICS` in `build_demographics_data.py` picks 14 well-covered,
interpretable ones across four categories (Income & Economy, Labor market, Migration &
Diversity, Cost of living). Extending the list is a one-line addition per metric if
something specific is wanted later - the raw files aren't touched, just read.

## Caveats

- **`median_income` (INKAR)'s exact period (monthly vs. annual) isn't confirmed** - no
  codebook ships with the INKAR extract the way the Zensus columns have one
  (`docs/CODEBOOKS/census2022_codebook.csv`). The values (~€2,400-5,000) are labeled
  with a hedge in the metrics manifest rather than a guessed unit. Same caution applies
  to `migration_in_rate`/`migration_out_rate`/`asylum_seeker_share`, labeled "per 1,000
  residents" as the standard INKAR convention, but unverified against a codebook.
- **County boundaries are approximate** - `m-ad/geofeatures-ags-germany`'s counties are
  GADM-derived, not the official BKG VG250 line the other three apps use for
  municipalities/states. Good enough for a choropleth at this scale, not for precise
  border work.
- **Color scale is a straight percentile-clamped sequential ramp** (5th-95th percentile
  of whatever's currently loaded, dark = low, gold = high) - deliberately a different
  palette from `map-trends`' red/white/blue, since this app shows absolute *levels*, not
  signed *changes*, and mixing the two color languages would be misleading.
- **No cross-linking to election results yet** - this app stands alone; overlaying
  swing/vote-share data against a chosen demographic metric (e.g. "does rent price
  predict AfD growth") would be a natural next step but isn't built here.
