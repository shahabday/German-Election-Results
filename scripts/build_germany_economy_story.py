"""Builds the compact, self-contained dataset for story/germany-is-not-one-economy.html.

Same pattern as scripts/build_germany_not_one_story.py: this doesn't fetch
anything new, it repackages county-level fields already computed and used by
map-demographics's own prepared county/<year>.json output (INKAR + VGRdL
sourced), plus the state-level Gini series already used by map-society, into
one small bundle scoped to this story.

Run from the repo root:
    python scripts/build_germany_economy_story.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOCIETY = ROOT / "map-society" / "data"
DEMO_PREPARED = ROOT / "map-demographics" / "data" / "prepared"
OUT = ROOT / "story" / "data" / "germany-is-not-one-economy"


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


def county_series_from_prepared(prepared_dir, key, years_wanted, scale=1):
    data = {}
    for y in years_wanted:
        p = prepared_dir / "county" / f"{y}.json"
        if not p.exists():
            continue
        rec = load(p)
        vals = {ags: r[key] * scale for ags, r in rec.items() if r.get(key) is not None}
        if vals:
            data[y] = vals
    years = sorted(data.keys(), key=int)
    all_vals = [v for y in years for v in data[y].values()]
    return {"resolution": "county", "type": "continuous", "years": years, "domain": domain(all_vals), "data": data}


def gini_series(years_wanted):
    raw = load(SOCIETY / "raw" / "gini_income_inequality_by_state.json")
    by_year = {}
    for state, years in raw.items():
        for y, v in years.items():
            gini = v.get("gini")
            if gini is not None:
                by_year.setdefault(y, {})[state] = gini
    years = [y for y in years_wanted if y in by_year]
    all_vals = [v for y in years for v in by_year[y].values()]
    return {"resolution": "state", "type": "continuous", "years": years, "domain": domain(all_vals), "data": {y: by_year[y] for y in years}}


def main():
    boundary = load(SOCIETY / "prepared" / "counties.geojson")
    dump(OUT / "counties.geojson", boundary)

    metrics = {
        "income": county_series_from_prepared(DEMO_PREPARED, "hh_income", [str(y) for y in range(2001, 2022)]),
        "gdp_per_capita": county_series_from_prepared(DEMO_PREPARED, "gdp_percap", [str(y) for y in range(2000, 2021)], scale=1000),
        "low_income_hh": county_series_from_prepared(DEMO_PREPARED, "share_low_income_hh", [str(y) for y in range(2013, 2022)]),
        "unemployment_rate": county_series_from_prepared(DEMO_PREPARED, "unemployment_rate", [str(y) for y in range(1998, 2021)]),
        "foreign_share": county_series_from_prepared(DEMO_PREPARED, "foreign_share", [str(y) for y in range(1995, 2021)]),
        "rent_price": county_series_from_prepared(DEMO_PREPARED, "rent_price", [str(y) for y in range(2010, 2022)]),
        "living_space_per_capita": county_series_from_prepared(DEMO_PREPARED, "living_space_per_capita", [str(y) for y in range(2011, 2023)]),
        "gini": gini_series(["2021", "2022", "2023", "2024", "2025"]),
    }

    dump(OUT / "metrics.json", metrics)

    print("wrote", OUT / "metrics.json")
    for key, m in metrics.items():
        print(f"  {key}: {m['resolution']}, {m['type']}, {len(m['years'])} years "
              f"({m['years'][0] if m['years'] else '-'}-{m['years'][-1] if m['years'] else '-'}), domain={m['domain']}")


if __name__ == "__main__":
    main()
