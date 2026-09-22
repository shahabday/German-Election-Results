# Interactive Election Map — Municipality Resolution, All Election Types

`index.html` is a standalone Leaflet map at **municipality (Gemeinde) resolution** —
~10,900 areas, the finest geography this repo has for any election type. It's a separate,
independent build from [`map/`](../map/README.md) (the federal Wahlkreis map) — different
directory, different data pipeline, own `.claude/launch.json` entry (port 8421) — so
changes here can't break that one.

## Running it

```bash
python -m http.server 8421 --directory map-municipality
```

Then open `http://localhost:8421`.

## "All of Germany" — the nationwide Landtag / Kommunalwahl aggregate

Bundestag and Europawahl are nationwide-simultaneous, so a single year already gives a
full national picture. Landtag and Kommunalwahl don't have that — each of the 16 states
runs on its own schedule — so there's no single year where "all of Germany voted." Select
**Landtag** or **Kommunalwahl**, then pick **★ All of Germany (current standing)** from
the state dropdown, and the map shows every state at its **own most recent election on or
before the selected year** — not a simultaneous vote, but "what did the political map of
Germany actually look like at this point in time," the way a map of state-governor party
control works in other countries. States that voted in *exactly* the selected year get a
single white outline drawn around the whole state, so you can still see an election
actually happening as you scrub the slider, even though the rest of the map stays fully
populated with carried-over results. That outline is the **real Bundesland boundary**
(`data/prepared/state_outlines.geojson`, 16 features, 2-digit AGS state codes) - not
something estimated from the municipality data. (An earlier version tried to derive the
outline by dissolving/hulling the state's own municipality polygons client-side; it
looked wrong - a dissolve fragmented into dozens of slivers since neighboring
municipalities in the Gemeinden boundary file don't share exact vertices, and a convex
hull was visibly just an approximation. Using the actual state boundary layer, sourced
separately the same way the municipality one was, is both simpler and correct.)

The year slider for this view runs over the **union of every real election year across
all 16 states** (computed client-side from the per-state year lists already in
`manifest.json`), not a generic decade grid — so every slider step is a real event
somewhere in the country. No new data or boundaries were needed: this reuses the
existing per-state-per-year files and the shared municipality boundary, merging up to 16
small JSON fetches client-side (cached, so scrubbing back to an already-seen year is
instant). The one exception is Berlin's 2026 entry — that's the Wahlkreis-resolution
special layer above, a different boundary/schema entirely, so the aggregate skips it and
correctly falls back to Berlin's 2023 municipality-level result instead.

Hovering a municipality in this view shows which state's data it's from and which year
that state's shown result is actually from, in addition to the usual party breakdown.

## Special case: 2026 Berlin Abgeordnetenhauswahl

Select **Landtag → Berlin → 2026** and the map swaps in a one-off, finer boundary layer:
Berlin's 78 Abgeordnetenhaus Wahlkreise, each with a real direct-mandate winner, instead
of Berlin's usual single municipality polygon. This election (2026-09-20) isn't in GERDA
yet — the repo's data predates it by about a day — so it's sourced live from
[wahlen-berlin.de](https://wahlen-berlin.de/wahlen/BE2026/Afspraes/AGH/ergebnisse.html)
(the Landeswahlleiterin's own results portal) instead. See
`map-municipality/build_berlin_2026.py` for the scraper/parser and
`map-municipality/data/special/berlin_2026/` for the raw pages, parsed results, and
boundary GeoJSON. **Results shown are the "Vorläufiges Ergebnis"** (preliminary count, as
published the morning after the election) **— not yet certified.** Re-run the script
against the same URLs later to pull the certified final count once published.

Primary coloring is Zweitstimme (party-list vote) plurality, consistent with every other
dataset in this map. The tooltip additionally shows the Erststimme (direct-mandate)
winner and candidate name — Berlin's Wahlkreise are the only Landtag-level areas in this
map with a genuine single-winner seat, the same way a Bundestag Wahlkreis does.

`build_berlin_2026.py` also sums all 78 Wahlkreise's full (not just top-5) party vote
counts into one citywide total and writes it as an ordinary municipality-schema file,
`data/prepared/landtag/berlin/2026.json` (AGS 11000000) — the same shape every other
state/year already has. This is a secondary rollup, not the primary view: selecting
**Landtag → Berlin → 2026** directly still shows the richer 78-Wahlkreis layer above (it
takes priority). The rollup exists so Berlin 2026 also shows up correctly in the **All of
Germany** national aggregate below, instead of being silently skipped there for lacking a
municipality-shaped file. Cross-checked against the citywide total wahlen-berlin.de itself
published: 25.65% Die Linke / 1,824,514 valid votes computed here vs. the site's own
25.7% / 1,824,514 — matches to within rounding.

## Special case: 2026 Berlin BVV elections (the Kommunalwahl equivalent)

Select **Kommunalwahl → Berlin → 2026** for the same treatment applied to the district
council (Bezirksverordnetenversammlungen) elections, held the same day as AGH. Berlin's
"Kommunalwahl" was a single citywide blob for every year before this, for the same
structural reason as Landtag: GERDA's municipal file has one AGS for all of Berlin. Now
2026 shows the real 12 Bezirke instead, each a genuine administrative unit (unlike AGH's
78 Wahlkreise, BVV is proportional-only — no direct mandate — so there's no finer layer
to build here; 12 Bezirke *is* the real resolution). Source: same site, `.../Afspraes/bvv/`
instead of `.../AGH/`; see `build_berlin_bvv_2026.py`. Same citywide-rollup trick as AGH
(`data/prepared/kommunal/berlin/2026.json`) so it shows up in the national aggregate too —
cross-checked against wahlen-berlin.de's own citywide figure: 24.1% Die Linke / 1,890,291
valid votes computed here, exact match to the site's own numbers.

## Also outside GERDA: Mecklenburg-Vorpommern and Saxony-Anhalt, 2026

Both states held their regular Landtag elections in September 2026 (MV on the 20th, the
same day as Berlin; Saxony-Anhalt on the 6th) — also too recent for GERDA. **Landtag →
Mecklenburg-Vorpommern → 2026** and **Landtag → Saxony-Anhalt → 2026** pull from each
state's own official results portal instead:

- MV: [wahlen.mvnet.de](https://wahlen.mvnet.de/dateien/ergebnisse.2026/landtagswahl/csv/l_gemeinden.csv)
  — a clean official per-Gemeinde CSV, "Vorläufiges Ergebnis" as of 2026-09-21.
- Saxony-Anhalt: [wahlergebnisse.sachsen-anhalt.de](https://wahlergebnisse.sachsen-anhalt.de/wahlen/lt26/downloads/Ergebnisse_Gemeinden_LT_2026.csv)
  — same, "Vorläufiges Ergebnis" as of 2026-09-07 (this one is a day-old-ish count, not
  literally hours-old like Berlin/MV, but still not the certified final).

Unlike Berlin, **both publish results with the standard 8-digit AGS** used everywhere
else in this map, so they join straight onto the existing shared municipality boundary —
no special boundary layer needed, and no frontend changes were required to wire them in.
See `map-municipality/build_state_elections_2026.py`.

One MV-specific precision caveat, stated openly in MV's own CSV: small municipalities
that belong to an "Amt" (a collective administrative unit covering several villages)
have their postal (Briefwahl) votes reported only at the Amt level, not attributed back
to the individual Gemeinde — so those villages' figures here are **Urne-votes only**.
Municipalities that aren't part of an Amt (cities like Rostock, Schwerin) are unaffected.

Neither of these two has a Wahlkreis-level (constituency) layer built yet, unlike Berlin
— both states do publish a Wahlkreis-level CSV too (36 areas for MV, 41 for Saxony-Anhalt)
with real direct-mandate winners, but wiring those in would need sourcing each state's own
Wahlkreis boundary geometry, which hasn't been done. Worth doing later if useful.

## Also outside GERDA: Rhineland-Palatinate, 2026

Rhineland-Palatinate voted 2026-03-22 — six months before this repo's data snapshot, so
unlike Berlin/MV/Saxony-Anhalt this is the **certified final result** (festgestellt by the
Landeswahlausschuss 2026-04-02), not a preliminary count. **Landtag → Rhineland-Palatinate
→ 2026** pulls from
[wahlen.rlp.de](https://www.wahlen.rlp.de/landtagswahl/ergebnisse)'s official Excel export,
which conveniently already has one row per individual municipality (no precinct-level
summing needed, unlike MV/Saxony-Anhalt) — see `build_rlp_2026.py`.

The catch: that file has no AGS column, only RLP's own internal ID and a name, so
municipalities are matched to our boundary **by normalized name** instead. 2,116 of 2,301
RLP municipalities (92%) matched unambiguously; the rest are either a name mismatch
(abbreviations, missing disambiguating suffixes like "(Sieg)"/"(Pfalz)") or a name that
exists more than once in the state and wasn't disambiguated by parent Kreis — both cases
are logged and left as "no data" rather than guessed, so you'll see a handful of blank
municipalities scattered around the state on this one. Improvable later (tracking the
Kreis hierarchy while parsing would resolve most of the ambiguous ones) if worth the effort.

## What it shows

Four election types, switchable from the top-left panel:

- **Bundestag** (federal) and **Europawahl** (EU Parliament) — nationwide, all
  municipalities vote the same day, so it's just a year slider.
- **Landtag** (state) and **Kommunalwahl** (municipal council) — each of the 16 states
  runs these independently on its own schedule, so picking one of these adds a state
  selector, and the year list + map view update to that state alone.

Color = the plurality party's municipal vote share (the party with the most votes in that
Gemeinde). Unlike the federal Wahlkreis map's "elected_party", **this is not a real
single-winner seat** — municipalities don't elect one representative by plurality the way
a Bundestag constituency does. It is an area-level statistic: which party's list got the
most votes there. Treat it as "where is party X strongest," not "who represents this
municipality." See the repo root
[docs/GAPS_AND_LIMITATIONS.md](../docs/GAPS_AND_LIMITATIONS.md) on the ecological-fallacy
caveat this implies.

Hover any municipality for its top-5 party breakdown and turnout.

## Architecture (why this map is structured differently from `map/`)

The federal Wahlkreis map bakes vote data directly into each year's boundary GeoJSON,
because it has ~300 areas and boundaries genuinely change every election. Here, doing that
would mean re-shipping the same ~11,000-polygon geometry dozens of times over (10 federal
years × 16 states × ~8 Landtag cycles each × ~8 Kommunalwahl cycles each...). Instead:

- **One boundary file**, `data/prepared/gemeinden.geojson` (~11k municipalities, all four
  election types are already harmonized to 2025 boundaries in the source CSVs — see the
  repo root [docs/GEOGRAPHIC_KEYS.md](../docs/GEOGRAPHIC_KEYS.md)), loaded once and never
  refetched.
- **Many small per-selection data files** — `data/prepared/<type>/<year>.json` for
  federal/European, `data/prepared/<type>/<state>/<year>.json` for Landtag/Kommunalwahl —
  each just `{ags: {winner, share, top5, turnout}}`, fetched on demand and used to restyle
  the one boundary layer in place.

## Data

- Vote data: `processed/elections/federal_municipality_1990_2025_harm2025.csv.zip`,
  `european_1990_2024_harm.csv.zip`, `state_municipality_1990_2026_harm2025.csv.zip`,
  `municipal_1990_2026_harm.csv` — all GERDA, real certified vote counts, see the repo
  root [docs/SOURCES.md](../docs/SOURCES.md).
- Boundaries: BKG VG250 municipality boundaries (Stand 31.12.2024), via a public
  [gist mirror](https://gist.github.com/gjrichter/29be18c38110b2b030d8e5a07f2243e9).
  Matched against the 2025-harmonized election files by AGS: 10,675 of 10,676 municipalities
  with 2025 federal election data matched a boundary (the one miss is likely a very recent
  boundary change not yet in this Dec-2024 boundary snapshot).
- State (Bundesland) boundaries: `data/prepared/state_outlines.geojson`, 16 features,
  sourced from [m-ad/geofeatures-ags-germany](https://github.com/m-ad/geofeatures-ags-germany)
  (derived from GADM), used only for the "just voted" outline in the national aggregate
  view above.
- `build_municipality_data.py` does the join and writes everything under
  `data/prepared/`. Re-run it after touching any source CSV or the boundary file:

  ```bash
  python map-municipality/build_municipality_data.py
  ```

## Known limitations

- **Party-column detection is heuristic.** Each source file has a different, large set of
  party columns (up to 352 for the state file, spanning decades of small/regional
  parties). `build_municipality_data.py` uses an explicit blacklist of known
  non-party/meta columns rather than a hand-maintained party list, and treats everything
  else as a party. One real bug this caught during development: `municipal_1990_2026_harm.csv`
  reports the CDU/CSU union bloc *only* as a combined `cdu_csu` column (no separate `cdu`/
  `csu`, unlike the other three files) — an early version of the blacklist dropped it
  everywhere, which silently erased the CDU/CSU from every Kommunalwahl result. Fixed by
  only excluding `cdu_csu` when `cdu` and `csu` also exist separately in that file.
- **The `other` column is real** (GERDA's own residual/local-list bucket), so in
  Kommunalwahl results especially, "Sonstige / lokale Listen" winning a municipality is
  a legitimate, common outcome (local independent voter associations are often the
  strongest force in small-town German municipal politics), not a data gap.
- **Boundary vintage is Dec 2024**, elections are harmonized to 2025 boundaries — a
  small number of municipalities (well under 1%) may not match for this reason.
- No "no-data" distinction is drawn between "this municipality didn't exist yet under
  these boundaries at this election" vs. "GERDA has no row for it" — both just render as
  unstyled grey.
