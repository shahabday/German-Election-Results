"""Builds the compact, self-contained dataset for story/germany-is-not-one.html.

Ten metrics, each already fetched and used by map-society and map-demographics -
this script doesn't fetch anything new, it just repackages a curated subset into
one small bundle scoped to this story, the same pattern scripts/build_home_story_data.py
uses for home.html.

State-level metrics (religion_pct, sports_rate, happiness, volunteering,
life_expectancy, health_personnel_density) are stored keyed by STATE NAME (16
entries), not broadcast to all ~400 counties - the frontend looks values up via
each county polygon's own "state" property instead. This is a size optimization
only; map-society's own tool broadcasts these to county level for a different
reason (a uniform choropleth schema across all its metrics).

County-level metrics (crime_rate, welfare_rate, foreign_share, asylum_seeker_share)
are stored keyed by county AGS, read straight from map-society's and
map-demographics' own prepared county/<year>.json output - this script must be
run AFTER both of those tools' build scripts.

Run from the repo root:
    python scripts/build_germany_not_one_story.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOCIETY = ROOT / "map-society" / "data"
DEMO = ROOT / "map-demographics" / "data"
AGE = ROOT / "map-population-age" / "data" / "prepared"
OUT = ROOT / "story" / "data" / "germany-is-not-one"

# The source (map-population-age) publishes fixed 5-year bands. Two of this
# story's age metrics are the share of population in one specific custom band
# (28-35 doesn't land on a 5-year edge), built by prorating each overlapping
# raw band assuming its population is spread evenly across its own single
# years of age - a standard, if approximate, re-binning technique. 100 stands
# in for "no upper bound" on the raw 95+ band and the 65+ share, so the
# open-ended top of each lines up exactly with no special-casing needed.
RAW_AGE_BANDS = [
    ("00-04", 0, 5), ("05-09", 5, 10), ("10-14", 10, 15), ("15-19", 15, 20),
    ("20-24", 20, 25), ("25-29", 25, 30), ("30-34", 30, 35), ("35-39", 35, 40),
    ("40-44", 40, 45), ("45-49", 45, 50), ("50-54", 50, 55), ("55-59", 55, 60),
    ("60-64", 60, 65), ("65-69", 65, 70), ("70-74", 70, 75), ("75-79", 75, 80),
    ("80-84", 80, 85), ("85-89", 85, 90), ("90-94", 90, 95), ("95+", 95, 100),
]
AGE_YEARS = ["2011", "2014", "2017", "2020", "2023", "2025"]


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def domain(values):
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return [0, 1]
    def pct(p):
        idx = min(len(vals) - 1, max(0, round(p * (len(vals) - 1))))
        return vals[idx]
    return [pct(0.03), pct(0.97)]


def state_series(years_wanted, series_by_state):
    """series_by_state is {state_name: {year: value}} - transposed here to the
    same year-major {year: {key: value}} shape county_series_from_prepared
    produces, just keyed by state name instead of county AGS."""
    by_year = {}
    for state, years in series_by_state.items():
        for y, v in years.items():
            if v is not None:
                by_year.setdefault(y, {})[state] = v
    years = [y for y in years_wanted if y in by_year]
    all_vals = [v for y in years for v in by_year[y].values()]
    return {"resolution": "state", "type": "continuous", "years": years, "domain": domain(all_vals), "data": {y: by_year[y] for y in years}}


def county_series_from_prepared(prepared_dir, key, years_wanted):
    data = {}
    for y in years_wanted:
        p = prepared_dir / "county" / f"{y}.json"
        if not p.exists():
            continue
        rec = load(p)
        vals = {ags: r[key] for ags, r in rec.items() if key in r}
        if vals:
            data[y] = vals
    years = sorted(data.keys(), key=int)
    all_vals = [v for y in years for v in data[y].values()]
    return {"resolution": "county", "type": "continuous", "years": years, "domain": domain(all_vals), "data": data}


def load_raw_age_bands():
    raw = {}  # raw band slug -> year -> {ags: count}
    for slug, _, _ in RAW_AGE_BANDS:
        raw[slug] = {}
        for y in AGE_YEARS:
            p = AGE / f"age_{slug}" / f"{y}.json"
            if not p.exists():
                continue
            rec = load(p)
            raw[slug][y] = {ags: v["count"] for ags, v in rec.items() if v.get("count") is not None}
    return raw


def age_band_share(raw, lo, hi):
    """{year: {ags: that band's share of the county's population, %}} - a
    plain, directly-comparable number (like every other metric in this
    story), found to actually divide East from West clearly (unlike a
    "which band is locally densest" categorical map, which didn't)."""
    data = {}
    for y in AGE_YEARS:
        total_pop, band_pop = {}, {}
        for slug, rlo, rhi in RAW_AGE_BANDS:
            overlap = max(0, min(hi, rhi) - max(lo, rlo))
            rwidth = rhi - rlo
            for ags, count in raw[slug].get(y, {}).items():
                total_pop[ags] = total_pop.get(ags, 0) + count
                if overlap > 0:
                    band_pop[ags] = band_pop.get(ags, 0) + count * (overlap / rwidth)
        year_out = {ags: round(band_pop.get(ags, 0) / tot * 100, 2) for ags, tot in total_pop.items() if tot}
        if year_out:
            data[y] = year_out
    years = [y for y in AGE_YEARS if y in data]
    all_vals = [v for y in years for v in data[y].values()]
    return {"resolution": "county", "type": "continuous", "years": years, "domain": domain(all_vals), "data": data}


def average_age(raw):
    """{year: {ags: population-weighted mean age}}, using each raw band's own
    midpoint as its representative age. The open-ended 95+ band has no
    natural midpoint - 82 stands in as its effective mean, since remaining
    life expectancy at 95 is only a few more years, not enough to matter at
    this precision."""
    data = {}
    for y in AGE_YEARS:
        weighted, total_pop = {}, {}
        for slug, lo, hi in RAW_AGE_BANDS:
            mid = 82.0 if slug == "95+" else (lo + hi) / 2
            for ags, count in raw[slug].get(y, {}).items():
                weighted[ags] = weighted.get(ags, 0) + count * mid
                total_pop[ags] = total_pop.get(ags, 0) + count
        year_out = {ags: round(weighted[ags] / tot, 1) for ags, tot in total_pop.items() if tot}
        if year_out:
            data[y] = year_out
    years = [y for y in AGE_YEARS if y in data]
    all_vals = [v for y in years for v in data[y].values()]
    return {"resolution": "county", "type": "continuous", "years": years, "domain": domain(all_vals), "data": data}


def main():
    boundary = load(SOCIETY / "prepared" / "counties.geojson")
    dump(OUT / "counties.geojson", boundary)
    county_to_state = {f["properties"]["county"]: f["properties"]["state"] for f in boundary["features"]}

    population = load(SOCIETY / "raw" / "population_2018_2025.json")
    state_pop = {}
    for ags, years in population.items():
        st = county_to_state.get(ags)
        if not st:
            continue
        for y, p in years.items():
            if p is None:
                continue
            state_pop.setdefault(st, {}).setdefault(y, 0)
            state_pop[st][y] += p

    religion = load(SOCIETY / "raw" / "religion_2001_2022.json")
    sports_members = load(SOCIETY / "raw" / "sports_membership_2017_2025.json")
    sports_rate = {}
    for st, years in sports_members.items():
        sports_rate[st] = {}
        for y, members in years.items():
            pop = state_pop.get(st, {}).get(y)
            if pop:
                sports_rate[st][y] = round(members / pop * 100, 1)

    happiness = load(SOCIETY / "raw" / "happiness_by_state.json")
    volunteering = load(SOCIETY / "raw" / "volunteering_by_state.json")

    life_expectancy_raw = load(SOCIETY / "raw" / "life_expectancy_by_state.json")
    life_expectancy = {}
    for st, years in life_expectancy_raw.items():
        for y, mf in years.items():
            life_expectancy.setdefault(st, {})[y] = round((mf["m"] + mf["f"]) / 2, 1)

    health_personnel = load(SOCIETY / "raw" / "health_personnel_density_by_state.json")

    crime_years = ["2020", "2021", "2022", "2023", "2024"]
    welfare_years = ["2018", "2019", "2020", "2021", "2022", "2023", "2024"]
    foreign_years = [str(y) for y in range(1995, 2021)]
    asylum_years = [str(y) for y in range(2010, 2021)]

    raw_age = load_raw_age_bands()

    metrics = {
        "senior_share": age_band_share(raw_age, 65, 100),
        "late20s_share": age_band_share(raw_age, 28, 35),
        "avg_age": average_age(raw_age),
        "religion_pct": state_series([str(y) for y in range(2001, 2023)], religion),
        "sports_rate": state_series([str(y) for y in range(2017, 2026)], sports_rate),
        "happiness": state_series(["2019", "2021", "2024", "2025"], happiness),
        "volunteering": state_series(["2019"], volunteering),
        "crime_rate": county_series_from_prepared(SOCIETY / "prepared", "crime_rate", crime_years),
        "welfare_rate": county_series_from_prepared(SOCIETY / "prepared", "welfare_rate", welfare_years),
        "life_expectancy": state_series(["2023"], life_expectancy),
        "health_personnel_density": state_series([str(y) for y in range(2008, 2025)], health_personnel),
        "foreign_share": county_series_from_prepared(DEMO / "prepared", "foreign_share", foreign_years),
        "asylum_seeker_share": county_series_from_prepared(DEMO / "prepared", "asylum_seeker_share", asylum_years),
    }

    dump(OUT / "metrics.json", metrics)

    print("wrote", OUT / "metrics.json")
    for key, m in metrics.items():
        extra = f"domain={m['domain']}" if m["type"] == "continuous" else f"categories={[c['slug'] for c in m['categories']]}"
        print(f"  {key}: {m['resolution']}, {m['type']}, {len(m['years'])} years "
              f"({m['years'][0] if m['years'] else '-'}-{m['years'][-1] if m['years'] else '-'}), {extra}")


if __name__ == "__main__":
    main()
