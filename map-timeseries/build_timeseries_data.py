"""
Build the dataset for map-timeseries: pick any set of states and/or counties and
compare their metrics as line-vs-year plots. Fourth independent app - reads from
map-demographics/data/prepared/ (county-level income/INKAR time series, already built
by map-demographics/build_demographics_data.py) and map-trends/data/prepared/ (the real
Bundesland outlines), never writes to either.

State-level lines are a simple (unweighted) mean of that state's counties for whichever
counties have data for that metric/year - NOT population-weighted, since there's no
consistent multi-year county population figure in this project (the only population
data is the single-year 2022 census snapshot, which can't retroactively weight a 1995
value). This is flagged in the UI, not just here.

Run from the repo root or map-timeseries/, after map-demographics/build_demographics_data.py
and map-trends/build_trends_data.py have already produced their output:
    python map-timeseries/build_timeseries_data.py
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEMO_SRC = ROOT / "map-demographics" / "data" / "prepared"
TRENDS_SRC = ROOT / "map-trends" / "data" / "prepared"
OUT = Path(__file__).resolve().parent / "data" / "prepared"

STATE_CODE_TO_SLUG = {
    "01": "schleswig_holstein", "02": "hamburg", "03": "niedersachsen", "04": "bremen",
    "05": "north_rhine_westphalia", "06": "hesse", "07": "rhineland_palatinate",
    "08": "baden_wuerttemberg", "09": "bavaria", "10": "saarland", "11": "berlin",
    "12": "brandenburg", "13": "mecklenburg_vorpommern", "14": "saxony",
    "15": "saxony_anhalt", "16": "thuringia",
}
STATE_LABELS = {
    "schleswig_holstein": "Schleswig-Holstein", "hamburg": "Hamburg",
    "niedersachsen": "Niedersachsen", "bremen": "Bremen",
    "north_rhine_westphalia": "North Rhine-Westphalia", "hesse": "Hesse",
    "rhineland_palatinate": "Rhineland-Palatinate", "baden_wuerttemberg": "Baden-Württemberg",
    "bavaria": "Bavaria", "saarland": "Saarland", "berlin": "Berlin",
    "brandenburg": "Brandenburg", "mecklenburg_vorpommern": "Mecklenburg-Vorpommern",
    "saxony": "Saxony", "saxony_anhalt": "Saxony-Anhalt", "thuringia": "Thuringia",
}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def build_state_rollups(metric_keys):
    county_dir = DEMO_SRC / "county"
    state_years_by_metric = {k: [] for k in metric_keys}
    for path in sorted(county_dir.glob("*.json")):
        year = path.stem
        counties = load(path)
        sums = {}   # slug -> metric -> [sum, count]
        for county_code, rec in counties.items():
            slug = STATE_CODE_TO_SLUG.get(county_code[:2])
            if not slug:
                continue
            bucket = sums.setdefault(slug, {})
            for metric, value in rec.items():
                s, c = bucket.get(metric, (0.0, 0))
                bucket[metric] = (s + value, c + 1)
        out = {}
        for slug, metrics in sums.items():
            out[slug] = {m: round(s / c, 4) for m, (s, c) in metrics.items()}
            for m in metrics:
                state_years_by_metric[m].append(year) if m in state_years_by_metric else None
        dump(OUT / "state" / f"{year}.json", out)
    for m in state_years_by_metric:
        state_years_by_metric[m] = sorted(set(state_years_by_metric[m]))
    print(f"state/<year>.json: {len(list(county_dir.glob('*.json')))} years, 16 states each (mean of counties)")
    return state_years_by_metric


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    print("copying county time series + boundaries...")
    shutil.copytree(DEMO_SRC / "county", OUT / "county", dirs_exist_ok=True)
    shutil.copyfile(DEMO_SRC / "counties.geojson", OUT / "counties.geojson")
    shutil.copyfile(TRENDS_SRC / "state_outlines.geojson", OUT / "state_outlines.geojson")

    demo_manifest = load(DEMO_SRC / "metrics_manifest.json")
    county_metrics = demo_manifest["county"]["metrics"]
    metric_keys = [m["key"] for m in county_metrics]

    print("building state rollups (simple mean of counties)...")
    state_years_by_metric = build_state_rollups(metric_keys)

    all_years = sorted({y.stem for y in (OUT / "county").glob("*.json")})
    manifest = {
        "years": all_years,  # every year that has a county/<year>.json AND state/<year>.json file
        "metrics": [
            {**m, "state_years": state_years_by_metric.get(m["key"], [])}
            for m in county_metrics
        ],
        "states": [
            {"slug": slug, "code": code, "label": STATE_LABELS[slug]}
            for code, slug in sorted(STATE_CODE_TO_SLUG.items(), key=lambda kv: kv[1])
        ],
    }
    dump(OUT / "manifest.json", manifest)
    print(f"wrote manifest.json: {len(metric_keys)} metrics, 16 states")


if __name__ == "__main__":
    main()
