"""
Build map-current-standing-trends: the same "rolling most-recent-election
composite" as map-current-standing, but as click-to-compare line charts
instead of a map - pick any states, counties, or municipalities and watch
their CURRENT STANDING (not raw election-by-election results) trend from
1990 to 2026.

Because the underlying value only changes when that specific area actually
gets a fresh election (nationwide, or its own state's Landtag/Kommunalwahl),
and otherwise just carries forward, the resulting lines are naturally
step-shaped: flat between an area's own elections, then jumping the moment
new data arrives - which is the whole point of pairing "current standing"
with a trend view: it shows exactly when a place's picture actually updated,
not just its results at fixed shared election years.

No new computation happens here - this reads map-current-standing's already-
built composite files (one full country snapshot per year, 1990-2026)
directly, copies them wholesale, and adds the boundary layers
map-election-timeseries already established for area picking.

Run from the repo root, after map-current-standing/ has been built:
    python map-current-standing-trends/build_current_standing_trends_data.py
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STANDING_SRC = ROOT / "map-current-standing" / "data" / "prepared"
DEMO_SRC = ROOT / "map-demographics" / "data" / "prepared"
TRENDS_SRC = ROOT / "map-trends" / "data" / "prepared"
OUT = Path(__file__).resolve().parent / "data" / "prepared"


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    print("copying boundaries...")
    shutil.copyfile(STANDING_SRC / "gemeinden.geojson", OUT / "gemeinden.geojson")
    shutil.copyfile(DEMO_SRC / "counties.geojson", OUT / "counties.geojson")
    shutil.copyfile(TRENDS_SRC / "state_outlines.geojson", OUT / "state_outlines.geojson")

    standing_manifest = load(STANDING_SRC / "manifest.json")
    years = standing_manifest["years"]

    print(f"copying {len(years)} yearly composite snapshots...")
    for year in years:
        shutil.copyfile(STANDING_SRC / f"{year}.json", OUT / f"{year}.json")

    manifest = {
        "years": years,
        "party_info": standing_manifest["party_info"],
        "default_fallback": standing_manifest["default_fallback"],
    }
    dump(OUT / "manifest.json", manifest)
    print("wrote manifest.json")


if __name__ == "__main__":
    main()
