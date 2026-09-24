# Source Catalog

## Primary source: GERDA (German Election Database)

Heddesheimer, V., Hilbig, H., Sichart, F., & Wiedemann, A. (2025). *GERDA: The German
Election Database*. Scientific Data, 12, 618. https://www.nature.com/articles/s41597-025-04811-5

Repository: https://github.com/awiedem/german_election_data (MIT license)
R package: https://github.com/hhilbig/gerda
Download page: https://www.german-elections.com/election-data/

GERDA itself sources from:
- **Federal elections**: Bundeswahlleiterin (Federal Returning Officer), https://www.bundeswahlleiterin.de
- **State elections**: Regionaldatenbank Deutschland (joint federal/state statistical database),
  via the DESTATIS SOAP web service
- **Municipal elections**: each state's own statistical office, procured individually
  (see full per-state list in the GERDA README — some via public websites, some by direct
  email request to the state office, since not all states publish machine-readable municipal
  results)
- **Boundary crosswalks**: BBSR (Bundesinstitut für Bau-, Stadt- und Raumforschung) official
  "Umsteigeschlüssel" (transition keys) for consistent time series
- **Shapefiles**: BKG (Federal Agency for Cartography and Geodesy), VG250

Files pulled directly, with the exact GERDA identifier in parentheses:

| Our filename | GERDA name | Level | Years | Harmonized to |
|---|---|---|---|---|
| federal_wahlkreis_2002_2025.csv | federal_wkr_unharm | Constituency | 2002-2025 | — |
| federal_county_1953_2025.csv | federal_cty_unharm | County | 1953-2025 | — |
| federal_county_1990_2025_harm2021.csv | federal_cty_harm | County | 1990-2025 | 2021 boundaries |
| federal_municipality_1990_2025_harm2025.csv | federal_muni_harm_25 | Municipality | 1990-2025 | 2025 boundaries |
| state_municipality_1990_2026_harm2025.csv | state_harm_25 | Municipality | 1990-2026 | 2025 boundaries |
| state_constituency_1980_2026.csv | ltw_wkr_unharm | Constituency | 1980-2026 | — |
| municipal_1990_2026_harm.csv | municipal_harm | Municipality | 1990-2026 | 2021 boundaries |
| european_1990_2024_harm.csv | european_muni_harm | Municipality | 2009-2024 | 2021 boundaries |
| county_inkar_indicators.csv | (bundled INKAR covariates) | County | 1995-2022 | 2021 boundaries |
| county_inkar_additional.csv | (bundled INKAR covariates) | County | 1995-2022 | 2021 boundaries |
| county_gross_income.csv, county_household_income.csv | (bundled INKAR) | County | varies | 2021 boundaries |
| county_employment.csv, county_unemployment.csv | (bundled INKAR) | County | varies | 2021 boundaries |
| county_covariates_bonus.csv | (R package `county_covariates_internal`) | County | 1995-2022 | 2021 boundaries |
| census2022_municipality_demographics_housing.csv | (R package `census_2022_internal`) | Municipality | 2022 snapshot | — |
| ags_1990_to_2025_crosswalk.csv, county_crosswalks_1990_2021.csv, wahlkreis_2021_to_2025_crosswalk.csv | GERDA crosswalks | — | — | — |
| municipality_area_pop_employment_1990_2023.csv, county_area_pop_employment_1990_2023.csv | (bundled covariates) | Muni/County | 1990-2023 | 2021 boundaries |

INKAR itself (the underlying source for most covariates) is run by the BBSR:
https://www.inkar.de — a German federal spatial-planning research institute. The INKAR
variable names (German) are preserved with an `_inkar` suffix in the two `county_inkar_*`
files; `county_covariates_bonus.csv` has the same data under cleaner English names, with
the INKAR variable code in `county_covariates_bonus_codebook.csv` for cross-reference.

## Secondary source: Zeit Online historical constituency data

https://github.com/ZeitOnline/bundestagswahl-historische-wahlkreis-daten (CC BY-SA 4.0)

Covers Bundestag elections 1949-2021 by constituency, hand-normalized to 2025 constituency
boundaries. Zeit Online built this because no official geographic data exists for
constituency boundaries before 1998 — they digitized historical paper maps by hand. **This
file is less precise than the GERDA files** for exactly that reason; see
`docs/GAPS_AND_LIMITATIONS.md` for the specific caveats they document (their own README
is copied into `raw/elections/zeitonline_btw_historical/README.md` if you want the full
methodology).

## What I could not pull directly into this sandbox

This working environment's network access is restricted to GitHub and package registries;
direct downloads from destatis.de, regionalstatistik.de, bbsr.bund.de, and similar German
government domains are blocked at the network level here. Everything above came from
GitHub-hosted mirrors of that same official data. Two things I could not get this way:

- **House purchase prices** (as opposed to rent) — not bundled in GERDA/INKAR at fine
  geography. Official source: regional Gutachterausschüsse (expert appraisal committees)
  publish Bodenrichtwerte; private aggregators (empirica-systeme, vdpResearch) have more
  current data but it isn't uniformly free or standardized in geography.
- **Full time series of migration background** (only a single 2022 snapshot is bundled;
  the 2011 census exists too but I didn't find a clean pre-extracted municipality file
  for it in the sources I could reach).

`scripts/fetch_remaining.py` has the exact URLs for both, to run from a machine with
normal internet access.

## Third source: regionalstatistik.de + smaller German sources, pulled for the map-society / map-population-pyramid tools

Regionalstatistik.de's GENESIS web GUI (https://www.regionalstatistik.de/genesis/online),
fetched by hand table-by-table (registration is required for its web SERVICE/API as of
May 2025, but not for the ordinary browser table-builder), plus a few smaller
non-GENESIS sources for indicators GENESIS doesn't carry (church membership, sports club
membership, life satisfaction, volunteering - see each file's row below).

These were originally pulled as JSON for two specific map tools and lived only inside
`map-society/data/raw/` and `map-population-pyramid/data/raw/`. `scripts/export_raw_to_csv.py`
exports plain CSV copies of every one of those files to `processed/society/` and
`processed/population_age/`, next to this project's other `processed/` tables, so they're
usable independent of those two tools. Each folder has its own `CODEBOOK.csv` (one row per
output file: geography, years, columns, unit, exact GENESIS table code or document). Every
CSV is keyed by `ags` (5-digit county code, join against `processed/crosswalks/county_crosswalks_1990_2021.csv`
or `map-society/data/prepared/counties.geojson` for names) or `state` (German state name,
spelled exactly as in `map-society/data/prepared/counties.geojson`'s `state` property).

Re-run `python scripts/export_raw_to_csv.py` from the repo root after any new pull into
either tool's `data/raw/` to refresh these exports.

A handful of source files aren't JSON and are copied into `processed/society/originals/`
unchanged rather than re-parsed: the BKA's original crime-statistics workbooks (`pks_*.xlsx/.csv`,
behind `crime_haeufigkeitszahl.csv`), the EKD/fowid church-membership workbooks (behind
`church_membership_by_state.csv`), and two PDFs whose one relevant table was hand-transcribed
(DOSB's sports-membership report, behind `sports_club_members_by_state.csv`; the 5th
Freiwilligensurvey's Laenderbericht, behind `volunteering_rate_by_state.csv`).
