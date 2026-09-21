# Interactive Election Map — Federal Bundestag, by Wahlkreis

`index.html` is a standalone Leaflet map of every Bundestag election from 2002 to 2025,
at constituency (Wahlkreis) resolution — the finest level where "which party won" has a
real electoral meaning (the direct-mandate winner), rather than being an aggregation
artifact.

## Running it

Any static file server works, since the page fetches its data files over HTTP:

```bash
python -m http.server 8420 --directory map
```

Then open `http://localhost:8420`.

## What it shows

- **Year slider**: 2002, 2005, 2009, 2013, 2017, 2021, 2025 — each using that election's
  *actual* constituency boundaries (redistricting happens almost every cycle), not a
  boundary set from a different year.
- **Color by, toggle**:
  - *Direct mandate winner* — who won the constituency seat (Erststimme / first vote,
    first-past-the-post). This is the real electoral outcome for that district.
  - *Party-list plurality* — which party got the most Zweitstimme (second vote, the one
    that actually determines each party's seat count nationally) in that district. This
    can differ from the direct-mandate winner (a district can elect an SPD MP by
    Erststimme while the Greens top the party-list vote there).
- **Fill opacity** scales with the winning party's vote share, so close races read visibly
  paler than landslides.
- **Hover tooltip**: constituency name, state, winning share, top-5 parties for whichever
  metric is selected, turnout.

## Data

- Vote data: `processed/elections/federal_wahlkreis_2002_2025.csv` (see the repo root
  [README](../README.md) and [docs/SOURCES.md](../docs/SOURCES.md) — this is GERDA's
  `federal_wkr_unharm`, real certified vote counts, each year on that year's real
  boundaries).
- Boundaries: `map/data/boundaries/wkr_<year>.geojson`, one file per election year,
  sourced from:
  - 1998–2017: [okfde/wahldaten](https://github.com/okfde/wahldaten) (converted from
    Bundeswahlleiter official shapefiles)
  - 2021: official KML from
    [bundeswahlleiterin.de](https://www.bundeswahlleiterin.de/bundestagswahlen/2021/wahlkreiseinteilung/downloads.html)
  - 2025: [linusha/wahlkreise-25-geometry](https://github.com/linusha/wahlkreise-25-geometry)
    (converted from official shapefiles)
- `build_federal_wahlkreis_data.py` joins the two and writes the per-year GeoJSON the
  page actually loads (`map/data/prepared/wkr_<year>.geojson`) plus `meta.json` (party
  colors/labels). Re-run it after touching the source CSV or the boundary files:

  ```bash
  python map/build_federal_wahlkreis_data.py
  ```

## Known limitations

- The `cdu_csu` combined column in the source CSV is dropped in favor of tracking `cdu`
  and `csu` separately (they never run in the same district, so this loses nothing, and
  avoids double-counting the "Union" bloc in the top-parties breakdown).
- 2009's boundary file has 339 polygon *features* for 299 constituencies — a handful of
  districts are split into multiple polygon pieces (exclaves). Each piece is styled from
  its shared `wkr_nr`, so this doesn't affect correctness, just feature count.
- No Wahlkreis-level map exists for pre-1998 elections (no official geographic data exists
  that far back — see the root [docs/GAPS_AND_LIMITATIONS.md](../docs/GAPS_AND_LIMITATIONS.md)
  on the Zeit Online 1949–2001 file, which is normalized to *modern* boundaries and could
  be added as an "approximate" historical layer later).

## Not yet built

This covers federal Bundestag elections only. State (Landtag), municipal, and European
elections are in `processed/elections/` but aren't wired into this map yet:

- State elections have their own Wahlkreis boundaries, redrawn independently by each of
  the 16 states on their own schedules — sourcing 16 states × several redistricting
  cycles each is a much bigger boundary-hunting effort than the single federal map above.
- Municipal and European elections don't have a constituency layer at all in Germany
  (EU is one national list; Kommunalwahlen are municipal-council elections) — the natural
  "highest resolution" view for those is a municipality-level choropleth instead, which
  would reuse a single VG250 municipality boundary set (matching the 2025-harmonized
  election files) rather than per-year constituency files.
