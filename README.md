# German Elections + Socioeconomic Data — Working Dataset

Prepared September 2026. This is raw material for you to build your own dataset from —
cleaned, sourced, and documented, but deliberately left as separate files rather than
one pre-merged table, so you can decide how to join and weight things yourself.

## What's in here

```
processed/
  elections/      8 election result files, federal/state/municipal/EU, 1949-2026
  covariates/     Income, rent, migration, cars, housing, employment — by county/municipality
  crosswalks/     Geographic ID mappings so you can join everything together
docs/
  SOURCES.md              Every dataset: origin, license, exact provenance
  GEOGRAPHIC_KEYS.md       How AGS / county / Wahlkreis codes work and how to join on them
  GAPS_AND_LIMITATIONS.md  What's NOT in here, and how precise what IS in here really is
  CODEBOOKS/               Column-level dictionaries for the less self-explanatory files
scripts/
  merge_example.py        Worked example: join election results to covariates and plot it
  fetch_remaining.py      Ready-to-run downloader for the pieces this sandbox couldn't reach
```

## Coverage at a glance

| Level | Elections | Years |
|---|---|---|
| Federal (Bundestag), by constituency | `federal_wahlkreis_2002_2025.csv` | 2002-2025 |
| Federal (Bundestag), by constituency, longer run | `federal_wahlkreis_1949_2021_zeitonline_normalized2025.csv` | 1949-2021 (see caveats below) |
| Federal, by county | `federal_county_1953_2025.csv` / `federal_county_1990_2025_harm2021.csv` | 1953-2025 |
| Federal, by municipality | `federal_municipality_1990_2025_harm2025.csv` | 1990-2025 |
| State (Landtag), by municipality | `state_municipality_1990_2026_harm2025.csv` | 1990-2026 |
| State (Landtag), by constituency | `state_constituency_1980_2026.csv` | 1980-2026 |
| Municipal/local council (Kommunalwahlen) | `municipal_1990_2026_harm.csv` | 1990-2026 |
| European Parliament | `european_1990_2024_harm.csv` | 2009-2024 |

Covariates: income (gross + household, by county, annual), rent levels, migration
background and foreign-national share, car ownership, unemployment, homeownership rate,
age structure, household size, dwelling vacancy — see `docs/SOURCES.md` for which file
has which, and at what geography.

## The single most important thing to know before you use this

Election results here are almost all **real vote counts** — exact, not estimates. The
covariates split into two very different kinds of precision:

- County-level covariates (`county_inkar_*.csv`, income, rent, cars, unemployment) are an
  **annual time series, 1995-2022** — genuinely comparable year to year.
- The Census file (`census2022_municipality_demographics_housing.csv`) is a **single
  snapshot for 2022** — migration background, homeownership, rent per m², age structure —
  at municipality level, but it does not move through time. If you attach it to a 1994
  election, you're describing that place with 2022 demographics, not 1994 ones.

Full detail, including the ecological-fallacy caveat for anyone correlating area-level
vote share with area-level demographics, is in `docs/GAPS_AND_LIMITATIONS.md`.

## Where this came from

Almost everything here is drawn from **GERDA (German Election Database)**, a peer-reviewed
academic dataset (Heddesheimer, Hilbig, Sichart & Wiedemann, 2025, *Nature Scientific Data*)
that already harmonizes federal, state, municipal, and EU election results across 76 years
of German boundary changes, plus bundled INKAR and Census 2022 covariates. I pulled its
underlying files directly rather than reproducing that harmonization work myself — see
`docs/SOURCES.md` for exact provenance and citation. The 1949-2001 federal series comes
from a separate Zeit Online project that geo-referenced historical constituency maps by hand.

## What's missing, and why

Full municipal (Kommunalwahlen) history is actually included here via GERDA — better
coverage than I expected to be able to assemble. What's genuinely not included: house
*purchase* prices (as opposed to rent), and any demographic variable finer than
municipality level (i.e., nothing at the individual polling-station level, for privacy
and small-sample reasons that are structural to how Germany publishes this data, not a
limitation of this harvest). See `docs/GAPS_AND_LIMITATIONS.md` for sourcing suggestions
if you want to chase those down yourself.
