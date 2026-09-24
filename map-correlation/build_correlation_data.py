"""Builds map-correlation's dataset: one flat {ags: {metric_key: value}} record per
county, combining every metric map-society has built (each metric's own MOST RECENT
available year, since different metrics cover different year ranges) with two headline
age-group shares computed from map-population-age's county age-band data.

This is a scatterplot/correlation tool, not a map, so it needs exactly one number per
county per metric rather than a full time series - "most recent year available" is the
natural choice, and each metric's dataset entry records which year that was so the UI
can disclose it (some metrics are 2025, others are a lone 2019 or 2023 survey year, so
two variables plotted against each other are not always the same reference year).

Sources: reuses map-society/data/prepared (no new fetch) and
map-population-age/data/prepared/age_*/2025.json (no new fetch) - both already built by
their own tools' pipelines.
"""
import json
import os

SOCIETY_COUNTY = "../map-society/data/prepared/county"
SOCIETY_MANIFEST = "../map-society/data/prepared/metrics_manifest.json"
SOCIETY_GEOJSON = "../map-society/data/prepared/counties.geojson"
AGE_DIR = "../map-population-age/data/prepared"
OUT = "data/prepared"

CHILD_BANDS = ["00-04", "05-09", "10-14"]
ELDERLY_BANDS = ["65-69", "70-74", "75-79", "80-84", "85-89", "90-94", "95+"]


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def latest_value_per_metric(manifest, county_dir):
    """For each metric, walk its years newest-first and take the first value found
    per county - metrics have different year coverage, so this can pick a different
    reference year per metric."""
    year_cache = {}

    def year_data(year):
        if year not in year_cache:
            path = os.path.join(county_dir, f"{year}.json")
            year_cache[year] = load(path) if os.path.exists(path) else {}
        return year_cache[year]

    out = {}  # key -> {ags: value}
    year_used = {}  # key -> year string
    for m in manifest["county"]["metrics"]:
        key = m["key"]
        years_desc = sorted(m["years"], reverse=True)
        values = {}
        chosen_year = None
        for year in years_desc:
            yd = year_data(year)
            found_any = False
            for ags, rec in yd.items():
                if key in rec and ags not in values:
                    values[ags] = rec[key]
                    found_any = True
            if found_any and chosen_year is None:
                chosen_year = year
        out[key] = values
        year_used[key] = chosen_year
    return out, year_used


def age_group_shares(county_ags_list):
    def sum_share(bands):
        totals = {}
        for band in bands:
            path = os.path.join(AGE_DIR, f"age_{band}", "2025.json")
            if not os.path.exists(path):
                continue
            data = load(path)
            for ags, rec in data.items():
                share = rec.get("share")
                if share is None:
                    continue
                totals[ags] = totals.get(ags, 0) + share
        return {ags: round(v, 2) for ags, v in totals.items()}

    return sum_share(CHILD_BANDS), sum_share(ELDERLY_BANDS)


def main():
    manifest = load(SOCIETY_MANIFEST)
    geojson = load(SOCIETY_GEOJSON)
    county_names = {}
    county_states = {}
    for feat in geojson["features"]:
        props = feat["properties"]
        county_names[props["county"]] = props["name"]
        county_states[props["county"]] = props["state"]

    society_values, society_years = latest_value_per_metric(manifest, SOCIETY_COUNTY)
    under15_share, over65_share = age_group_shares(county_names.keys())

    variables = []
    for m in manifest["county"]["metrics"]:
        variables.append({
            "key": m["key"],
            "label": m["label"],
            "unit": m["unit"],
            "category": m["category"],
            "description": m["description"],
            "source": m["source"],
            "year": society_years[m["key"]],
        })
    variables.append({
        "key": "age_under15_share", "label": "Population under 15", "unit": "%",
        "category": "Demographics",
        "description": "Share of county residents younger than 15.",
        "source": "regionalstatistik.de, table 12411-09-01-4, sum of the 0-4/5-9/10-14 age bands",
        "year": "2025",
    })
    variables.append({
        "key": "age_65plus_share", "label": "Population 65 and older", "unit": "%",
        "category": "Demographics",
        "description": "Share of county residents 65 or older.",
        "source": "regionalstatistik.de, table 12411-09-01-4, sum of the 65-69 through 95+ age bands",
        "year": "2025",
    })

    all_values = dict(society_values)
    all_values["age_under15_share"] = under15_share
    all_values["age_65plus_share"] = over65_share

    counties = {}
    for ags, name in county_names.items():
        record = {"name": name, "state": county_states[ags]}
        for key, values in all_values.items():
            if ags in values and values[ags] is not None:
                record[key] = values[ags]
        counties[ags] = record

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "correlation_data.json"), "w", encoding="utf-8") as f:
        json.dump({"variables": variables, "counties": counties}, f, ensure_ascii=False, separators=(",", ":"))

    print(f"variables: {len(variables)}")
    print(f"counties: {len(counties)}")
    coverage = {v['key']: sum(1 for c in counties.values() if v['key'] in c) for v in variables}
    for k, n in sorted(coverage.items(), key=lambda kv: kv[1]):
        print(f"  {k}: {n} counties")


if __name__ == "__main__":
    main()
