# Geographic Keys — How to Join Everything

Germany's official geographic hierarchy runs: **Gemeinde (municipality) → Kreis (county) →
Bundesland (state)**. Bundestag constituencies (Wahlkreise) are a separate, election-specific
layer that cuts across municipalities but not across states.

## The codes you'll see in these files

- **`ags`** — 8-digit Amtlicher Gemeindeschlüssel (official municipality code). First 2
  digits = state, digits 3-5 = county, digits 6-8 = municipality within county. This is
  the standard key for municipality-level joins.
- **`county_code`** — 5-digit code, the first 5 digits of an AGS. Standard key for
  county-level joins.
- **`wkr_nr`** — constituency number (1-299 for the current Bundestag map). Not
  hierarchically nested inside county boundaries — a constituency can span parts of
  multiple counties, especially in cities.

## Why there are both "harm" and "unharm" versions of the same election

German municipalities merge, split, and get renamed constantly — there were roughly 24,000
in 1990 and about 10,800 today. A raw ("unharm") file uses whatever boundaries existed at
the time of that specific election, so an AGS code in the 1994 file might not exist at all
in the 2021 file, or might refer to a different area. The "harm" (harmonized) files have
already been re-aggregated by GERDA onto one fixed boundary set (usually 2021 or 2025), so
every year uses the *same* AGS code for the *same* area, and you can safely build a time
series. Use the harmonized files unless you specifically need original historical boundaries.

## Joining election results to covariates

- County-level covariates (`county_inkar_*.csv`, `county_covariates_bonus.csv`, income and
  employment files) join on `county_code` (5 digits) to any of the `_harm2021.csv` /
  `_harm2025.csv` election files, or to `federal_county_*` directly.
- The Census 2022 file joins on `ags` (8 digits) to any municipality-level election file.
  To attach it to a county-level file, aggregate first (population-weighted mean for
  shares, sum for counts) — the GERDA R package's `add_gerda_census()` function does
  exactly this if you have R available; `scripts/merge_example.py` shows the pandas
  equivalent.
- If you need to join across *different* boundary vintages (e.g. an "unharm" file to a
  2025-harmonized one), use `ags_1990_to_2025_crosswalk.csv` or
  `wahlkreis_2021_to_2025_crosswalk.csv` as the bridge.

## Party names

Party columns are lowercase English-ish slugs (`cdu_csu`, `spd`, `gruene`, `afd`, `linke_pds`,
`fdp`, etc.) as vote shares or vote counts — check each file's header, some report shares
(0-1) and some report absolute counts. `party_abbreviation_crosswalk_zeitonline.tsv` maps
smaller party abbreviations to full names for the Zeit Online historical file specifically.
