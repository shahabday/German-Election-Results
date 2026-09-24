"""
Build the demographics/economics dataset: two independent resolutions, since the two
source families don't share one.

1. Municipality (~10,800 Gemeinden, single snapshot): Zensus 2022 age structure,
   migration background, housing. Reuses map-all-elections's gemeinden.geojson boundary
   exactly (same AGS keys) - no new boundary needed.
2. County (~400 Kreise, multi-year 1995-2021 depending on metric): income (VGRdL wage
   and household income series) plus a curated subset of INKAR indicators. INKAR has
   ~55 columns per file and most are either redundant, too sparse before ~2005, or not
   obviously interesting - only a well-covered, interpretable subset is included (see
   COUNTY_METRICS below). Boundary is m-ad/geofeatures-ags-germany's counties.json
   (already fetched to data/boundaries/counties_raw.geojson), same source family as
   map-trends' state_outlines.geojson.

Every metric carries TWO descriptions: a short one-sentence definition (shown inline
in the tool's panel) and a longer one (source, exact calculation, caveats, regional
color) that only appears on the metrics glossary page (about/metrics.html, built by
scripts/build_metrics_glossary.py from this file's and map-society's manifests). The
in-tool panel links out to the glossary anchor for the full version.

This script only reads from processed/covariates/ and map-all-elections/data/prepared/ -
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
MUNI_SRC = ROOT / "map-all-elections" / "data" / "prepared"
OUT = Path(__file__).resolve().parent / "data" / "prepared"
BOUNDARIES = Path(__file__).resolve().parent / "data" / "boundaries"

SOURCE_LABEL = {
    "county_gross_income.csv": "Regional accounts (VGRdL), via processed/covariates/county_gross_income.csv",
    "county_household_income.csv": "Regional accounts (VGRdL), via processed/covariates/county_household_income.csv",
    "county_inkar_indicators.csv": "INKAR (BBSR), via processed/covariates/county_inkar_indicators.csv",
    "county_inkar_additional.csv": "INKAR (BBSR), via processed/covariates/county_inkar_additional.csv",
    "county_covariates_bonus.csv": "INKAR/Zensus-derived, via processed/covariates/county_covariates_bonus.csv",
}


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
# (output key, label, unit, category, short description, full description)
MUNICIPALITY_METRICS = [
    ("population_census22", "Population", "residents", "Demographics",
     "Total resident population at the 2022 census.",
     "Total resident population at the 2022 census. The baseline denominator behind every share metric in this dataset, and useful on its own for spotting which places are growing vs. shrinking. Source: Zensus 2022 (German federal census), municipality resolution."),
    ("share_under18_census22", "Under 18", "%", "Demographics",
     "Share of residents younger than 18.",
     "Share of residents younger than 18. A rough proxy for local demand on schools and childcare, and for how much of a place's future population growth will come from residents already living there. Source: Zensus 2022."),
    ("share_18to29_census22", "Age 18-29", "%", "Demographics",
     "Share of residents aged 18 to 29.",
     "Share of residents aged 18 to 29. Tends to run high in university towns and career-starter hubs, and low in retirement-heavy or rural areas young adults leave for education or work. Source: Zensus 2022."),
    ("share_30to49_census22", "Age 30-49", "%", "Demographics",
     "Share of residents aged 30 to 49.",
     "Share of residents aged 30 to 49 - roughly the family-formation and peak-earning years, so this tracks how many prime-working-age households a place has, not just its population size. Source: Zensus 2022."),
    ("share_50to59_census22", "Age 50-59", "%", "Demographics",
     "Share of residents aged 50 to 59.",
     "Share of residents aged 50 to 59, the pre-retirement cohort. A rising share here is a leading indicator of where the 60+ share (below) is headed next. Source: Zensus 2022."),
    ("share_60plus_census22", "Age 60+", "%", "Demographics",
     "Share of residents aged 60 and older.",
     "Share of residents aged 60 and older. High values signal aging/retirement pressure on local services, and tend to correlate with lower population turnover than younger, more mobile areas. Source: Zensus 2022."),
    ("share_foreign_census22", "Foreign nationals", "%", "Demographics",
     "Share of residents who are not German citizens.",
     "Share of residents who are not German citizens. This is citizenship-based only - a person born in Germany to immigrant parents, or a naturalized citizen, is NOT counted here even though they would be under migration background (below). Source: Zensus 2022."),
    ("share_migration_bg_census22", "Migration background", "%", "Demographics",
     "Share of residents with a migration background.",
     "Share of residents with a migration background - includes naturalized citizens and their children, so it's broader than (and always ≥) foreign-national share. Source: Zensus 2022."),
    ("avg_household_size_census22", "Avg. household size", "persons", "Demographics",
     "Average number of people living in the same household.",
     "Average number of people living in the same household. Smaller households mean more housing units are needed per resident, and a falling average over time is often an early sign of an aging or increasingly single-person population. Source: Zensus 2022."),
    ("share_single_family_census22", "Single/two-family homes", "%", "Housing",
     "Share of residential buildings that are single- or two-family houses.",
     "Share of residential buildings that are single- or two-family houses, rather than larger apartment blocks - a rough density/urbanization proxy. Source: Zensus 2022."),
    ("total_dwellings_census22", "Total dwellings", "count", "Housing",
     "Total number of housing units (not people).",
     "Total number of housing units (not people). A raw stock size, not a rate - compare across similarly-sized places rather than reading it directly against a much larger or smaller municipality. Source: Zensus 2022."),
    ("vacancy_rate_census22", "Vacancy rate", "%", "Housing",
     "Share of dwellings standing empty.",
     "Share of dwellings standing empty. High vacancy can mean a shrinking or unattractive local housing market, but can also just reflect a lot of second homes or units mid-renovation - read it alongside the population trend before assuming decline. Source: Zensus 2022."),
    ("share_owner_occupied_census22", "Owner-occupied", "%", "Housing",
     "Share of dwellings lived in by their owner.",
     "Share of dwellings lived in by their owner, as opposed to rented out. Renter-heavy places tend to see more population turnover and are more directly exposed to swings in asking rents than owner-heavy ones. Source: Zensus 2022."),
    ("avg_rent_per_m2_census22", "Avg. rent", "€/m²", "Housing",
     "Average asking rent per square meter, cold.",
     "Average asking rent per square meter, cold (excluding utilities/heating). This is a snapshot of what's currently being advertised, not what sitting tenants pay on older leases - in fast-growing cities it can run well above the typical rent actually being paid across all existing tenancies. Source: Zensus 2022."),
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
# (output key, label, unit, category, short description, full description, source file, source column)
COUNTY_METRICS = [
    ("gross_wage", "Avg. gross wage", "€/year", "Income & Economy",
     "Average gross wage per employee (VGRdL), before tax.",
     "Average gross wage per employee, from official regional accounts (VGRdL) - before tax, and averaged across full- and part-time work. This is a workplace-based figure (where people work, not where they live), so in commuter-heavy counties it can diverge noticeably from what residents actually take home - compare against household income below.",
     "county_gross_income.csv", "gross_avg_wage_vgrdl"),
    ("hh_income", "Avg. household income", "€/year", "Income & Economy",
     "Average disposable household income after taxes and transfers (VGRdL).",
     "Average disposable household income (after taxes and transfers), from official regional accounts (VGRdL). Unlike gross wage or GDP, this is what actually funds local consumption - it isn't inflated by commuters' workplace earnings or by capital-intensive industry that employs relatively few local residents.",
     "county_household_income.csv", "hh_income_vgrdl"),
    ("median_income", "Median income (INKAR)", "€ (period as reported by INKAR)", "Income & Economy",
     "The middle income value - half earn more, half less (INKAR).",
     "The middle income value (half earn more, half less) - less skewed by very high earners than an average, so it's generally a better read on a \"typical\" resident's income than the average figures above. Exact income concept/period not confirmed against a codebook, see README.",
     "county_inkar_indicators.csv", "Medianeinkommen_inkar"),
    ("gdp_percap", "GDP per capita", "€ thousand", "Income & Economy",
     "Total economic output per resident (GDP per capita).",
     "Total economic output produced in the county, divided by its population - a measure of local economic activity, not resident income (commuters can inflate it).",
     "county_inkar_indicators.csv", "Bruttoinlandsprodukt_je_Einwohner_inkar"),
    ("tax_capacity", "Tax capacity (Steuerkraft)", "€ per capita", "Income & Economy",
     "A county's own-source tax revenue capacity per resident.",
     "A municipality's own-source tax revenue capacity per resident - used in Germany's fiscal equalization system between richer and poorer areas.",
     "county_inkar_indicators.csv", "Steuerkraft_inkar"),
    ("unemployment_rate", "Unemployment rate", "%", "Labor market",
     "Share of the civilian labor force registered as unemployed.",
     "Share of the civilian labor force registered as unemployed. The standard headline labor-market number, but it doesn't distinguish short-term frictional unemployment from entrenched long-term joblessness - the two metrics right below break out exactly those two distinctions.",
     "county_inkar_additional.csv", "Arbeitslosenquote_inkar"),
    ("youth_unemployment_rate", "Youth unemployment rate (under 25)", "%", "Labor market",
     "Unemployment rate among residents under 25.",
     "Unemployment rate among residents under 25, as opposed to the civilian labor force overall above. Runs both higher and more volatile than the headline rate almost everywhere, since younger workers are the first let go in a downturn and the last hired in a recovery - so a county's YEAR-OVER-YEAR swing here is usually more informative than its level in any single year. Coverage is sparser than the headline rate (missing in roughly half of county-years).",
     "county_covariates_bonus.csv", "youth_unemployment_rate"),
    ("share_longterm_unemployed", "Long-term unemployed", "% of all unemployed", "Labor market",
     "Share of unemployed residents out of work for more than 12 months.",
     "Share of the county's unemployed who have been out of work for more than 12 months - the entrenched-joblessness component the headline unemployment rate mixes in with short-term frictional unemployment (someone between jobs for a few weeks). Two counties with the same overall unemployment rate can look very different here: one mostly short spells (a healthy, fluid labor market), the other mostly long spells (structural joblessness that a rate alone hides).",
     "county_covariates_bonus.csv", "share_longterm_unemployed"),
    ("industry_share", "Industry employment share", "%", "Labor market",
     "Share of employment in manufacturing/industry.",
     "Share of employment in manufacturing/industry, as opposed to services or agriculture - a deindustrialization proxy when tracked over time.",
     "county_inkar_indicators.csv", "Industriequote_inkar"),
    ("commuter_balance", "Commuter balance", "per 1,000 residents (+ = net inflow)", "Labor market",
     "Net commuters per 1,000 residents (+ = net inflow).",
     "Net commuters per 1,000 residents. Positive means more people commute IN for work than commute out (a job center); negative means the reverse (a bedroom community).",
     "county_inkar_indicators.csv", "Pendlersaldo_inkar"),
    ("foreign_share", "Foreign national share", "%", "Migration & Diversity",
     "Share of residents who are not German citizens (county-level).",
     "Share of residents who are not German citizens (county-level, INKAR source - compare with the municipality-level Zensus figure, which may differ slightly in methodology).",
     "county_inkar_indicators.csv", "Ausländeranteil_inkar"),
    ("migration_in_rate", "In-migration rate", "per 1,000 residents", "Migration & Diversity",
     "People moving into the county per 1,000 residents per year.",
     "People moving INTO the county per 1,000 residents, per year (from elsewhere in Germany or abroad). This is gross inflow only - a county can score high here and still be shrinking overall if out-migration (below) is even higher.",
     "county_inkar_additional.csv", "Zuzugsrate_inkar"),
    ("migration_out_rate", "Out-migration rate", "per 1,000 residents", "Migration & Diversity",
     "People moving out of the county per 1,000 residents per year.",
     "People moving OUT of the county per 1,000 residents, per year. High out-migration paired with low in-migration is the classic signature of a declining rural county losing working-age residents.",
     "county_inkar_additional.csv", "Fortzugsrate_inkar"),
    ("asylum_seeker_share", "Asylum seekers", "per 1,000 residents", "Migration & Diversity",
     "Asylum seekers registered in the county, per 1,000 residents.",
     "Asylum seekers registered in the county, per 1,000 residents. Reflects where asylum seekers are officially allocated/housed under Germany's state-quota distribution system (Koenigsteiner Schluessel) as much as it reflects where people ultimately choose to settle long-term.",
     "county_inkar_additional.csv", "Asylbewerber_inkar"),
    ("rent_price", "Rent price", "€/m²", "Cost of living",
     "Average rent per square meter (INKAR).",
     "Average rent per square meter (INKAR source - compare with the municipality-level Zensus rent figure, which may differ slightly in methodology).",
     "county_inkar_indicators.csv", "Mietpreise_inkar"),
    ("debtor_quota", "Over-indebtedness rate (Schuldnerquote)", "%", "Cost of living",
     "Share of adults with unmanageable debt.",
     "Share of adults with unmanageable debt (more liabilities than they can realistically repay) - a financial-distress indicator distinct from income level: a county can have modest but stable income and low debt distress, or higher income with more households overextended.",
     "county_inkar_indicators.csv", "Schuldnerquote_inkar"),

    # ---- added later: columns that were already sitting in county_covariates_bonus.csv
    # and county_inkar_indicators.csv from earlier data pulls, but never surfaced here ----
    ("purchasing_power", "Purchasing power (Kaufkraft)", "€ per capita", "Income & Economy",
     "Purchasing power (Kaufkraft) per resident.",
     "GfK-style purchasing power per resident - a broader spending-capacity measure than disposable income alone, since it's built to capture what households actually have available to spend, not just wages before taxes and transfers.",
     "county_covariates_bonus.csv", "purchasing_power"),
    ("share_low_income_hh", "Low-income households", "%", "Income & Economy",
     "Share of households below 60% of median income.",
     "Share of households with income below 60% of the median - the standard EU at-risk-of-poverty threshold. Because it's relative to that year's OWN median, it stays meaningful even as overall income levels rise over time, unlike a fixed euro poverty line would.",
     "county_covariates_bonus.csv", "share_low_income_hh"),

    ("physician_density", "Physicians", "per 10,000 residents", "Healthcare",
     "Physicians per 10,000 residents.",
     "All physicians (all specialties) per 10,000 residents, regardless of whether they practice at a hospital, private clinic, or elsewhere. A county with a large specialist hospital can score high here even if everyday primary care is thin - see general practitioners below for that specifically.",
     "county_covariates_bonus.csv", "physician_density"),
    ("gp_density", "General practitioners", "per 10,000 residents", "Healthcare",
     "General practitioners per 10,000 residents.",
     "General practitioners (Hausaerzte) specifically, per 10,000 residents - a primary-care access measure distinct from physician density overall, and generally the better indicator of how easy it is for an ordinary resident to see a doctor nearby.",
     "county_covariates_bonus.csv", "gp_density"),
    ("hospital_beds_per_capita", "Hospital beds", "per 1,000 residents", "Healthcare",
     "Hospital beds per 1,000 residents.",
     "Inpatient hospital beds per 1,000 residents. Reflects local inpatient capacity, not quality of care or travel distance - a rural county can show zero beds and still be well served by a hospital just across the county line.",
     "county_covariates_bonus.csv", "hospital_beds_per_capita"),

    ("childcare_under3", "Childcare rate (under 3)", "%", "Childcare",
     "Share of children under 3 in daycare.",
     "Share of children under 3 enrolled in daycare (Kita/Tagespflege). A strong predictor of maternal labor-force participation locally - where availability is low, one parent (usually the mother) tends to stay out of paid work longer.",
     "county_covariates_bonus.csv", "childcare_under3"),
    ("childcare_3to6", "Childcare rate (3-6)", "%", "Childcare",
     "Share of children aged 3-6 in daycare.",
     "Share of children aged 3-6 enrolled in daycare. Coverage here runs much higher nationwide than under-3 care, since most German states guarantee a Kita place from age 3 onward - so the gaps BETWEEN counties are more informative than the level of any one county.",
     "county_covariates_bonus.csv", "childcare_3to6"),

    ("cars_per_capita", "Cars", "per 1,000 residents", "Transport",
     "Registered cars per 1,000 residents.",
     "Registered passenger cars per 1,000 residents. High values often reflect poor public-transit access as much as affluence - rural counties commonly outrank wealthier but transit-rich cities on this metric.",
     "county_covariates_bonus.csv", "cars_per_capita"),

    ("building_permits_per_capita", "Building permits", "per 10,000 residents", "Housing",
     "New residential building permits per 10,000 residents.",
     "New residential building permits issued per 10,000 residents that year - a leading indicator of housing construction, not completions.",
     "county_covariates_bonus.csv", "building_permits_per_capita"),
    ("living_space_per_capita", "Living space per capita", "m²", "Housing",
     "Average residential floor space per resident.",
     "Average residential floor space per resident. This rises mechanically as household size falls, even with zero new construction - read it alongside average household size (municipality view) before treating a high value as pure housing abundance.",
     "county_covariates_bonus.csv", "living_space_per_capita"),
    ("municipal_debt_per_capita", "Municipal debt per capita", "€", "Housing",
     "Local government debt per resident.",
     "Local government debt per resident - a fiscal-strain measure at the municipal level, distinct from tax capacity.",
     "county_covariates_bonus.csv", "municipal_debt_per_capita"),

    ("share_micro_enterprises", "Micro enterprises", "%", "Business",
     "Share of local enterprises with under 10 employees.",
     "Share of local enterprises with fewer than 10 employees. A high share isn't inherently a bad sign - it's the norm in tourism-, retail-, and craft-heavy local economies, quite different from a share driven by economic distress.",
     "county_covariates_bonus.csv", "share_micro_enterprises"),
    ("share_large_enterprises", "Large enterprises", "%", "Business",
     "Share of local enterprises with 250+ employees.",
     "Share of local enterprises with 250 or more employees. A county can score low here and still be prosperous if its economy runs on many strong small/medium firms rather than a few big employers - classic Mittelstand-heavy regions often look this way.",
     "county_covariates_bonus.csv", "share_large_enterprises"),
    ("business_insolvencies", "Business insolvencies (INKAR)", "per 10,000 enterprises (unconfirmed unit, see README)", "Business",
     "Corporate insolvencies (INKAR, unit unconfirmed).",
     "Corporate insolvencies - INKAR convention is typically per 10,000 enterprises, but this hasn't been confirmed against a codebook (same caveat as median_income), so treat the exact unit with caution. Best read as a multi-year trend (rising vs. falling) rather than compared as a precise single-year level.",
     "county_inkar_indicators.csv", "Unternehmensinsolvenzen_inkar"),

    ("trade_tax_revenue", "Trade tax revenue (Gewerbesteuer, INKAR)", "€ per capita (unconfirmed unit, see README)", "Public Finances",
     "Local trade tax revenue (Gewerbesteuer, INKAR).",
     "Local trade tax revenue - likely € per capita given the value range, but not confirmed against a codebook. Negative values in some county-years reflect real refunds/corrections, not a data error. Because each municipality sets its own Gewerbesteuer multiplier (Hebesatz), part of what this measures is local tax POLICY, not purely how much business activity exists.",
     "county_inkar_indicators.csv", "Gewerbesteuer_inkar"),
    ("municipal_staff", "Municipal staff (Personal der Kommunen, INKAR)", "per 10,000 residents (unconfirmed unit, see README)", "Public Finances",
     "Local government staffing levels (INKAR).",
     "Local government employment - likely per 10,000 residents given the value range, but not confirmed against a codebook. More staff isn't automatically \"better government\" - it can also reflect a more fragmented municipal structure (many small Gemeinden each running their own administration) rather than service quality.",
     "county_inkar_indicators.csv", "Personal_der_Kommunen_inkar"),

    ("expert_jobs_share", "Expert-level jobs (INKAR)", "% (unconfirmed unit, see README)", "Knowledge Economy",
     "Share of jobs at the highest skill tier (INKAR).",
     "Share of employees whose job is classified at the highest INKAR skill-requirement tier (Experte) - a proxy for high-skill local labor demand.",
     "county_inkar_indicators.csv", "Beschäftigte_mit_Anforderungsniveau_Experte_inkar"),
    ("knowledge_industry_share", "Knowledge-intensive industry jobs (INKAR)", "% (unconfirmed unit, see README)", "Knowledge Economy",
     "Share of employment in knowledge-intensive industries (INKAR).",
     "Share of employment in INKAR-classified knowledge-intensive industries. Tends to cluster around universities and major metro areas - a useful counterpoint to industry_share (Labor market) when distinguishing \"old\" from \"new\" economy counties.",
     "county_inkar_indicators.csv", "Beschäftigte_in_wissensintensiven_Industrien_inkar"),
    ("creative_industry_share", "Creative industries jobs (INKAR)", "% (unconfirmed unit, see README)", "Knowledge Economy",
     "Share of employment in creative industries (INKAR).",
     "Share of employment in INKAR-classified creative industries (Kreativbranchen). Usually concentrated in large cities - values much above roughly 5% are rare outside of them.",
     "county_inkar_indicators.csv", "Beschäftigte_in_Kreativbranchen_inkar"),
    ("craft_trades_share", "Craft trades jobs (Handwerk, INKAR)", "% (unconfirmed unit, see README)", "Knowledge Economy",
     "Share of employment in craft trades / Handwerk (INKAR).",
     "Share of employment in craft trades (Handwerk) - a traditional-economy counterpoint to the knowledge-economy metrics above, and often strongest in exactly the mid-sized towns and rural counties where the others are weakest.",
     "county_inkar_indicators.csv", "Beschäftigte_im_Handwerk_inkar"),
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
    for out_key, label, unit, category, short_desc, full_desc, filename, col in COUNTY_METRICS:
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
                if year.endswith(".0"):
                    year = year[:-2]
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
                {"key": k, "label": label, "unit": unit, "category": cat, "description": short_desc,
                 "description_full": full_desc, "source": "Zensus 2022 (German federal census)"}
                for k, label, unit, cat, short_desc, full_desc in MUNICIPALITY_METRICS
            ],
        },
        "county": {
            "years": years,
            "metrics": [
                {"key": k, "label": label, "unit": unit, "category": cat, "description": short_desc,
                 "description_full": full_desc, "source": f"{SOURCE_LABEL[filename]}, column \"{col}\"",
                 "years": year_index[k], "global_domain": global_domain[k], "global_delta_cap": global_delta_cap[k]}
                for k, label, unit, cat, short_desc, full_desc, filename, col in COUNTY_METRICS
            ],
        },
    }
    dump(OUT / "metrics_manifest.json", manifest)
    print("wrote metrics_manifest.json")


if __name__ == "__main__":
    main()
