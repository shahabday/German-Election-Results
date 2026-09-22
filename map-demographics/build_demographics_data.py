"""
Build the demographics/economics dataset: two independent resolutions, since the two
source families don't share one.

1. Municipality (~10,800 Gemeinden, single snapshot): Zensus 2022 age structure,
   migration background, housing. Reuses map-municipality's gemeinden.geojson boundary
   exactly (same AGS keys) - no new boundary needed.
2. County (~400 Kreise, multi-year 1995-2021 depending on metric): income (VGRdL wage
   and household income series) plus a curated subset of INKAR indicators. INKAR has
   ~55 columns per file and most are either redundant, too sparse before ~2005, or not
   obviously interesting - only a well-covered, interpretable subset is included (see
   COUNTY_METRICS below). Boundary is m-ad/geofeatures-ags-germany's counties.json
   (already fetched to data/boundaries/counties_raw.geojson), same source family as
   map-trends' state_outlines.geojson.

This script only reads from processed/covariates/ and map-municipality/data/prepared/ -
it never writes to either.

Run from the repo root or map-demographics/:
    python map-demographics/build_demographics_data.py
"""
import csv
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COVAR_DIR = ROOT / "processed" / "covariates"
MUNI_SRC = ROOT / "map-municipality" / "data" / "prepared"
OUT = Path(__file__).resolve().parent / "data" / "prepared"
BOUNDARIES = Path(__file__).resolve().parent / "data" / "boundaries"


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def to_float(s):
    if s is None or s in ("", "NA", "NaN"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Municipality resolution: Zensus 2022, single snapshot
# ---------------------------------------------------------------------------
# (output key, label, unit, category, one-sentence explanation)
MUNICIPALITY_METRICS = [
    ("population_census22", "Population", "residents", "Demographics",
     "Total resident population at the 2022 census."),
    ("share_under18_census22", "Under 18", "%", "Demographics",
     "Share of residents younger than 18."),
    ("share_18to29_census22", "Age 18-29", "%", "Demographics",
     "Share of residents aged 18 to 29."),
    ("share_30to49_census22", "Age 30-49", "%", "Demographics",
     "Share of residents aged 30 to 49."),
    ("share_50to59_census22", "Age 50-59", "%", "Demographics",
     "Share of residents aged 50 to 59."),
    ("share_60plus_census22", "Age 60+", "%", "Demographics",
     "Share of residents aged 60 and older."),
    ("share_foreign_census22", "Foreign nationals", "%", "Demographics",
     "Share of residents who are not German citizens."),
    ("share_migration_bg_census22", "Migration background", "%", "Demographics",
     "Share of residents with a migration background - includes naturalized citizens and their children, so it's broader than (and always ≥) foreign-national share."),
    ("avg_household_size_census22", "Avg. household size", "persons", "Demographics",
     "Average number of people living in the same household."),
    ("share_single_family_census22", "Single/two-family homes", "%", "Housing",
     "Share of residential buildings that are single- or two-family houses, rather than larger apartment blocks - a rough density/urbanization proxy."),
    ("total_dwellings_census22", "Total dwellings", "count", "Housing",
     "Total number of housing units (not people)."),
    ("vacancy_rate_census22", "Vacancy rate", "%", "Housing",
     "Share of dwellings standing empty."),
    ("share_owner_occupied_census22", "Owner-occupied", "%", "Housing",
     "Share of dwellings lived in by their owner, as opposed to rented out."),
    ("avg_rent_per_m2_census22", "Avg. rent", "€/m²", "Housing",
     "Average asking rent per square meter, cold (excluding utilities/heating)."),
]


def build_municipality():
    path = COVAR_DIR / "census2022_municipality_demographics_housing.csv"
    out = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ags = row["ags"]
            rec = {}
            for key, *_ in MUNICIPALITY_METRICS:
                v = to_float(row.get(key))
                if v is not None:
                    rec[key] = v
            if rec:
                out[ags] = rec
    dump(OUT / "municipality_2022.json", out)
    print(f"municipality_2022.json: {len(out)} areas")


# ---------------------------------------------------------------------------
# County resolution: income (VGRdL) + curated INKAR indicators, by year
# ---------------------------------------------------------------------------
# (output key, label, unit, category, one-sentence explanation, source file, source column)
COUNTY_METRICS = [
    ("gross_wage", "Avg. gross wage", "€/year", "Income & Economy",
     "Average gross wage per employee, from official regional accounts (VGRdL) - before tax, and averaged across full- and part-time work.",
     "county_gross_income.csv", "gross_avg_wage_vgrdl"),
    ("hh_income", "Avg. household income", "€/year", "Income & Economy",
     "Average disposable household income (after taxes and transfers), from official regional accounts (VGRdL).",
     "county_household_income.csv", "hh_income_vgrdl"),
    ("median_income", "Median income (INKAR)", "€ (period as reported by INKAR)", "Income & Economy",
     "The middle income value (half earn more, half less) - less skewed by very high earners than an average. Exact income concept/period not confirmed against a codebook, see README.",
     "county_inkar_indicators.csv", 38),
    ("gdp_percap", "GDP per capita", "€ thousand", "Income & Economy",
     "Total economic output produced in the county, divided by its population - a measure of local economic activity, not resident income (commuters can inflate it).",
     "county_inkar_indicators.csv", 27),
    ("tax_capacity", "Tax capacity (Steuerkraft)", "€ per capita", "Income & Economy",
     "A municipality's own-source tax revenue capacity per resident - used in Germany's fiscal equalization system between richer and poorer areas.",
     "county_inkar_indicators.csv", 54),
    ("unemployment_rate", "Unemployment rate", "%", "Labor market",
     "Share of the civilian labor force registered as unemployed.",
     "county_inkar_additional.csv", 2),
    ("industry_share", "Industry employment share", "%", "Labor market",
     "Share of employment in manufacturing/industry, as opposed to services or agriculture - a deindustrialization proxy when tracked over time.",
     "county_inkar_indicators.csv", 36),
    ("commuter_balance", "Commuter balance", "per 1,000 residents (+ = net inflow)", "Labor market",
     "Net commuters per 1,000 residents. Positive means more people commute IN for work than commute out (a job center); negative means the reverse (a bedroom community).",
     "county_inkar_indicators.csv", 44),
    ("foreign_share", "Foreign national share", "%", "Migration & Diversity",
     "Share of residents who are not German citizens (county-level, INKAR source - compare with the municipality-level Zensus figure, which may differ slightly in methodology).",
     "county_inkar_indicators.csv", 7),
    ("migration_in_rate", "In-migration rate", "per 1,000 residents", "Migration & Diversity",
     "People moving INTO the county per 1,000 residents, per year (from elsewhere in Germany or abroad).",
     "county_inkar_additional.csv", 3),
    ("migration_out_rate", "Out-migration rate", "per 1,000 residents", "Migration & Diversity",
     "People moving OUT of the county per 1,000 residents, per year.",
     "county_inkar_additional.csv", 4),
    ("asylum_seeker_share", "Asylum seekers", "per 1,000 residents", "Migration & Diversity",
     "Asylum seekers registered in the county, per 1,000 residents.",
     "county_inkar_additional.csv", 6),
    ("rent_price", "Rent price", "€/m²", "Cost of living",
     "Average rent per square meter (INKAR source - compare with the municipality-level Zensus rent figure, which may differ slightly in methodology).",
     "county_inkar_indicators.csv", 39),
    ("debtor_quota", "Over-indebtedness rate (Schuldnerquote)", "%", "Cost of living",
     "Share of adults with unmanageable debt (more liabilities than they can realistically repay) - a financial-distress indicator distinct from income level.",
     "county_inkar_indicators.csv", 50),
]


def county_code(raw):
    return raw.strip().zfill(5)


def percentile(sorted_vals, p):
    if not sorted_vals:
        return None
    idx = min(len(sorted_vals) - 1, max(0, round(p * (len(sorted_vals) - 1))))
    return sorted_vals[idx]


def build_county_with_year_index():
    by_year = {}
    all_values = {out_key: [] for out_key, *_ in COUNTY_METRICS}
    for out_key, label, unit, category, description, filename, col in COUNTY_METRICS:
        path = COVAR_DIR / filename
        with open(path, encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            col_idx = header.index(col) if isinstance(col, str) else col
            for row in reader:
                if len(row) <= col_idx:
                    continue
                v = to_float(row[col_idx])
                if v is None:
                    continue
                county = county_code(row[0])
                year = row[1].strip()
                by_year.setdefault(year, {}).setdefault(county, {})[out_key] = v
                all_values[out_key].append(v)

    for year, counties in by_year.items():
        dump(OUT / "county" / f"{year}.json", counties)

    years = sorted(by_year.keys())
    year_index = {}
    # A single fixed domain per metric (5th/95th percentile across EVERY county-year on
    # record, not just the currently-viewed year) - lets the frontend offer "fixed scale"
    # coloring so a place's color is comparable across years, not just its rank within
    # one year. See map-demographics' "Fixed (whole period)" toggle.
    global_domain = {}
    for out_key, *_ in COUNTY_METRICS:
        year_index[out_key] = [y for y in years if any(out_key in rec for rec in by_year[y].values())]
        vals = sorted(all_values[out_key])
        global_domain[out_key] = [percentile(vals, 0.05), percentile(vals, 0.95)]

    # Same idea, but for the Growth view's cap: without this, the diverging scale
    # recomputes its cap from just the currently-shown year pair, so a given € or pp
    # change can look "hot" in a calm year and "mild" in a volatile one. This computes
    # one cap per metric from every year-over-year delta across the whole series (using
    # each metric's own available-year list, not raw year-1, since coverage has gaps),
    # so the same magnitude of change always reads the same color regardless of year.
    global_delta_cap = {}
    for out_key, *_ in COUNTY_METRICS:
        deltas = []
        yrs = year_index[out_key]
        for prev_y, y in zip(yrs, yrs[1:]):
            prev_recs, curr_recs = by_year[prev_y], by_year[y]
            for county, curr in curr_recs.items():
                if out_key not in curr:
                    continue
                prev = prev_recs.get(county)
                if prev is None or out_key not in prev:
                    continue
                deltas.append(abs(curr[out_key] - prev[out_key]))
        deltas.sort()
        global_delta_cap[out_key] = percentile(deltas, 0.95) or 1

    print(f"county/<year>.json: {len(years)} years ({years[0]}-{years[-1]}), "
          f"{sum(len(c) for c in by_year.values())} county-year rows")
    return years, year_index, global_domain, global_delta_cap


def build_boundaries():
    print("copying municipality boundary...")
    shutil.copyfile(MUNI_SRC / "gemeinden.geojson", OUT / "gemeinden.geojson")

    print("cleaning county boundary...")
    with open(BOUNDARIES / "counties_raw.geojson", encoding="utf-8") as f:
        raw = json.load(f)
    out = {"type": "FeatureCollection", "features": []}
    for feat in raw["features"]:
        p = feat["properties"]
        out["features"].append({
            "type": "Feature",
            "properties": {
                "county": feat["id"],
                "name": p.get("name"),
                "state": p.get("state"),
                "district_type": p.get("districtType"),
            },
            "geometry": feat["geometry"],
        })
    dump(OUT / "counties.geojson", out)
    print(f"counties.geojson: {len(out['features'])} counties")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    build_boundaries()
    build_municipality()
    years, year_index, global_domain, global_delta_cap = build_county_with_year_index()

    manifest = {
        "municipality": {
            "year": 2022,
            "metrics": [
                {"key": k, "label": label, "unit": unit, "category": cat, "description": desc}
                for k, label, unit, cat, desc in MUNICIPALITY_METRICS
            ],
        },
        "county": {
            "years": years,
            "metrics": [
                {"key": k, "label": label, "unit": unit, "category": cat, "description": desc, "years": year_index[k],
                 "global_domain": global_domain[k], "global_delta_cap": global_delta_cap[k]}
                for k, label, unit, cat, desc, *_ in COUNTY_METRICS
            ],
        },
    }
    dump(OUT / "metrics_manifest.json", manifest)
    print("wrote metrics_manifest.json")


if __name__ == "__main__":
    main()
