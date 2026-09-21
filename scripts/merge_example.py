"""
Worked example: join Bundestag county-level election results to INKAR county
covariates (income, migration/foreigner share, rent, cars, unemployment).

Run from the project root:
    python3 scripts/merge_example.py

Requires: pandas
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ELECTIONS = ROOT / "processed" / "elections"
COVARS = ROOT / "processed" / "covariates"

# 1. Load federal election results harmonized to 2021 county boundaries.
elec = pd.read_csv(ELECTIONS / "federal_county_1990_2025_harm2021.csv", low_memory=False)
elec["county_code"] = elec["county_code"].astype(str).str.zfill(5)

# 2. Load INKAR covariates (income, migration, rent, cars, unemployment - long format,
#    one row per county-year).
inkar = pd.read_csv(COVARS / "county_inkar_indicators.csv", low_memory=False)
inkar["county"] = inkar["county"].astype(str).str.zfill(5)
inkar = inkar.rename(columns={"county": "county_code"})

inkar_extra = pd.read_csv(COVARS / "county_inkar_additional.csv", low_memory=False)
inkar_extra["county"] = inkar_extra["county"].astype(str).str.zfill(5)
inkar_extra = inkar_extra.rename(columns={"county": "county_code"})

covars = inkar.merge(inkar_extra, on=["county_code", "year"], how="outer")

# 3. Join on (county_code, year). INKAR data isn't published every year for every
#    variable, so an election year with no exact covariate year will not match here -
#    for real analysis, consider matching each election to the *nearest available* INKAR
#    year instead of an exact year match.
merged = elec.merge(
    covars,
    left_on=["county_code", "election_year"],
    right_on=["county_code", "year"],
    how="left",
)

print(f"Election rows: {len(elec)}")
print(f"Merged rows: {len(merged)}")
print(f"Rows with a matched covariate year: {merged['year'].notna().sum()}")

# 4. Simple illustration: correlate AfD vote share with foreigner share, most recent
#    year where both are available.
cols_needed = ["afd", "Ausländeranteil_inkar"]
available = [c for c in cols_needed if c in merged.columns]
if len(available) == 2:
    sample = merged.dropna(subset=available)
    if len(sample):
        corr = sample[available[0]].corr(sample[available[1]])
        print(f"\nCorrelation between AfD vote share and foreigner share "
              f"(n={len(sample)} county-years): {corr:.3f}")
        print("Remember: this is an ECOLOGICAL correlation (area-level), not an "
              "individual-level finding. See docs/GAPS_AND_LIMITATIONS.md.")

# 5. Attach the 2022 Census snapshot (municipality-level) to a municipality election file
#    for demographics/housing, aggregating up to county level first.
census = pd.read_csv(COVARS / "census2022_municipality_demographics_housing.csv")
census["county_code"] = census["ags"].astype(str).str.zfill(8).str[:5]

share_cols = [c for c in census.columns if c.startswith("share_") or c.startswith("avg_") or "vacancy_rate" in c]
count_cols = ["population_census22", "total_dwellings_census22"]

def weighted_mean(df, col, weight_col="population_census22"):
    w = df[weight_col]
    return (df[col] * w).sum() / w.sum()

county_census = census.groupby("county_code").apply(
    lambda g: pd.Series({**{c: weighted_mean(g, c) for c in share_cols},
                          **{c: g[c].sum() for c in count_cols}})
).reset_index()

merged2 = merged.merge(county_census, on="county_code", how="left")
print(f"\nAfter attaching 2022 Census demographics/housing: {merged2.shape}")
print("Columns now include, e.g.: share_migration_bg_census22, share_owner_occupied_census22, "
      "avg_rent_per_m2_census22")

out_path = ROOT / "processed" / "example_merged_federal_county_with_covariates.csv"
merged2.to_csv(out_path, index=False)
print(f"\nWrote example merged file to {out_path}")
