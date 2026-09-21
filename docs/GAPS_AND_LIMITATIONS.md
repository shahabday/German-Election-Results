# Gaps, Precision, and Honest Caveats

## What's genuinely missing from this package

1. **House purchase prices.** Rent is covered (INKAR `Mietpreise_inkar` / `rent_level`,
   county level, and `avg_rent_per_m2_census22`, municipality 2022 snapshot). Sale prices
   are not — Germany doesn't centralize these the way it does rent or income. Official
   source: regional Gutachterausschüsse (expert appraisal committees) publish
   Bodenrichtwerte (standard land values), but each of the ~380 committees publishes
   independently, often through paid portals (BORIS-D is the nominal federal umbrella,
   https://www.bodenrichtwerte-boris.de, but coverage/pricing varies by state). For
   national coverage you're realistically looking at a private vendor (empirica-systeme,
   vdpResearch, ImmoScout24's own index).
2. **Migration background as a time series.** You have one clean cross-section: 2022. The
   2011 census also asked this, so a two-point comparison (2011 vs 2022) is possible in
   principle, but I did not find a pre-extracted, ready-to-join 2011 municipality file in
   the sources I could reach from here — you'd need to pull it from the Zensus 2011 portal
   (https://ergebnisse.zensus2011.de) directly.
3. **Anything below municipality level.** No layer here goes finer than the ~10,800
   municipalities (for demographics) or 299 constituencies (for votes). This is not a gap
   in the harvest — it reflects Germany's actual disclosure rules: statistical offices
   suppress small-area figures below a population threshold specifically to prevent
   identifying individuals, so a polling-station-level migration-background figure simply
   does not exist publicly, full stop.
4. **Full historical municipal (Kommunalwahlen) coverage for all city-level detail.**
   GERDA's `municipal_harm.csv` covers 1990-2026 and is the best single source available,
   but by GERDA's own documentation, some states' pre-2006 municipal results were procured
   by direct email request to the state statistical office rather than from a public
   dataset — so there may be state/year gaps for the earliest years. Check the `state`
   and `election_year` combinations you actually need before assuming complete coverage.

## Precision, by data type

- **Election results**: exact counts from official certified tallies. No sampling, no
  estimation. As precise as data gets.
- **Harmonized ("harm") election files**: votes from merged/split municipalities are
  reallocated using population weights or (for split mail-in districts) proportional
  allocation by polling-card voters. This is a very good approximation but not literally
  the original certified number for any single reconstructed unit — GERDA's own
  documentation flags "rounding errors" of a handful of votes in some cases.
- **INKAR county covariates**: official annual statistics (income, unemployment, GDP,
  rent, cars), not survey estimates — but several variables have real missing-data rates
  (see the `missing_pct` column in `county_covariates_bonus_codebook.csv`; some run 50-70%
  missing in early years because the underlying series didn't start until later).
- **Census 2022 municipality file**: register-based census methodology (not a full manual
  count, not a small-sample survey) — high precision, but it is a single 2022 snapshot,
  not a trend.
- **Zeit Online 1949-2001 constituency file**: explicitly the least precise thing in this
  package. Vote totals themselves are official, but the *geographic assignment* to modern
  constituency boundaries is approximate for two independent reasons: (a) it assumes the
  2022 population distribution within old constituencies also held decades earlier, which
  is false wherever an area grew or shrank unevenly, and (b) pre-1998 constituency
  boundaries were hand-vectorized from scanned paper maps, with the Zeit Online team's own
  estimate of positional error running from a few hundred meters up to a few kilometers in
  some cases. Use this file for broad historical trend lines, not precise small-area claims.

## The ecological fallacy, restated for this specific dataset

Every non-election layer here is an **area-level** statistic (county or municipality
averages), never an individual-level one. If a county shows both a high vote share for
some party and a high migration-background share, that tells you the two co-occur
spatially — it does not tell you how people with a migration background actually voted.
Germany's ballot secrecy makes individual-level linkage impossible by design; the closest
official approximation is the Bundeswahlleiterin's "repräsentative Wahlstatistik" (a
sampled, anonymized age/gender breakdown from marked ballots), which is a completely
separate data product not included in this package — see the earlier conversation for
where to find it if you want that specific angle.
