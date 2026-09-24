# German Election Trends — Swing Map

A companion visualization to [`map-all-elections`](../map-all-elections/), built on the
same election-type coverage (Bundestag, Europawahl, Landtag, Kommunalwahl) but focused
on *change between consecutive elections* rather than a single snapshot. Fully separate
app — no files in `map/` or `map-all-elections/` are touched; this only *reads* from
`map-all-elections/data/prepared/` at build time.

Run locally:
```
python build_trends_data.py   # from repo root or map-trends/, reads ../map-all-elections/data/prepared
python -m http.server 8422 --directory map-trends
```
(or use the `election-map-trends` entry in `.claude/launch.json`.)

## What it shows

Four metrics, selectable per election type/state/year-pair:

1. **Party growth** — percentage-point (pp) swing for a chosen party, area by area.
   Diverging color scale: white at 0, the party's own color for gains, muted red for
   losses.
2. **Flipped areas** — which municipalities/Wahlkreise changed their plurality winner
   between the two elections, colored by the new winner, with the exact previous→current
   winner in the tooltip. Areas that didn't flip are dimmed out.
3. **At risk** — municipalities that *didn't* flip, but where a non-winning party is
   rising fast enough that, if the same swing repeated next time, the margin would close
   to ≤5pp (configurable via `RISK_PROJECTED_GAP` in the build script). Already-flipped
   areas are shown in a separate muted blue so "about to flip" and "just flipped" aren't
   visually confused.
4. **Turnout Δ** — change in turnout, same diverging-scale treatment.

A small stats strip (flipped / at risk / total areas) gives an at-a-glance read for
whatever type/state/year-pair is selected, independent of which of the four metrics is
currently drawn on the map.

## The "new party = infinite growth" problem

Relative growth (e.g. "3x more votes than last time") is undefined when the previous
share was 0, and unstable when it was near 0. Rather than special-casing that, **pp
swing is the primary metric everywhere** — `current_share − previous_share` is always a
finite, well-defined number, including for a party that didn't exist or wasn't on the
ballot last time (its swing is just its current share). A relative-growth percentage is
still shown in tooltips, but only once the party clears a 1% baseline in the earlier
election; below that it's labeled **"new"** instead of a misleading multiplier.

## Data model and its limits

`build_trends_data.py` reads pairs of already-prepared per-year files from
`map-all-elections/data/prepared/<type>/[<state>/]<year>.json` — each one a dict of
`ags -> {w: winner, s: winner share, b: top-5 [party, share] pairs, t: turnout}` — and
for every consecutive pair of elections of the same type (and, for Landtag/Kommunalwahl,
the same state) computes a swing record per municipality. Output lands in
`map-trends/data/prepared/`, in the same `<type>/[<state>/]<year>.json` shape, where the
year in the filename is the *later* election in the pair (e.g. `federal/2025.json` means
"swing from 2021 to 2025"). `gemeinden.geojson` and `state_outlines.geojson` are copied
in once so this app has no runtime dependency on `map-all-elections/`.

Two structural caveats, inherited from the underlying per-year files:

- **Top-5 truncation.** Each year's file only keeps an area's top 5 parties by share. If
  a party is top-5 in one year but falls out of the top 5 in the other, its share in the
  year it's missing is treated as 0 — understating small/fading parties' swing slightly.
  This is the same resolution the rest of the app already works at.
- **No population weighting.** There's no vote-count field in the per-year files (only
  shares), so there's no vote-weighted statewide swing here — the stats strip is a
  straight area count, not a population-weighted aggregate. A genuinely population-
  weighted rollup would need the raw per-area vote counts, which aren't currently kept
  in `map-all-elections`'s prepared format.
- **"At risk" is a linear one-step projection**, not a real forecast: it just asks "if
  the *same* pp swing happened again, would the gap close?" It's meant as a quick way to
  spot places worth a closer look, not a prediction.
