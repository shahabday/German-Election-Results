"""
Build the dataset for map-election-timeseries: pick any set of areas (states,
counties, or specific municipalities) and compare a party's vote share, or turnout,
across every election of one type. Fifth independent app - reads from
map-municipality/data/prepared/ (per-year municipality-level results, already built),
map-demographics/data/prepared/counties.geojson (county boundary) and
map-trends/data/prepared/state_outlines.geojson (state boundary), never writes to any
of them.

No new per-year/per-metric files are computed here, unlike map-demographics/
map-timeseries - a "metric" here is just "this party's share" or "turnout", both
already present in every map-municipality per-year file
(ags -> {w, s, b: [[party,share],...top5], t: turnout}). State/county rollups (simple
unweighted means, same limitation as map-timeseries) are computed client-side on
demand from whichever year files are already loaded, since there's no fixed small set
of "metrics" to precompute against like map-demographics had.

Run from the repo root or map-election-timeseries/, after map-municipality/,
map-demographics/ and map-trends/ have already been built:
    python map-election-timeseries/build_election_timeseries_data.py
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUNI_SRC = ROOT / "map-municipality" / "data" / "prepared"
MUNI_SPECIAL_SRC = ROOT / "map-municipality" / "data" / "special"
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
    shutil.copyfile(MUNI_SRC / "gemeinden.geojson", OUT / "gemeinden.geojson")
    shutil.copyfile(DEMO_SRC / "counties.geojson", OUT / "counties.geojson")
    shutil.copyfile(TRENDS_SRC / "state_outlines.geojson", OUT / "state_outlines.geojson")

    print("copying per-year election results (all 4 types)...")
    for type_key in ("federal", "european", "landtag", "kommunal"):
        src = MUNI_SRC / type_key
        dst = OUT / type_key
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    # Berlin's Landtag (Abgeordnetenhaus) is one municipality (AGS 11000000) everywhere
    # else in this dataset, so its own Landtag time series is a single flat line - the
    # 2026 election is the one exception, with a real 78-Wahlkreis breakdown scraped
    # from wahlen-berlin.de (see map-municipality/build_berlin_2026.py). Copying just
    # those two small files lets the frontend offer Berlin's districts as click targets,
    # even though only the 2026 point will have data - every other year stays blank for
    # those areas, which the frontend explains inline.
    print("copying Berlin 2026 Wahlkreis special layer...")
    berlin_out = OUT / "special" / "berlin_2026"
    berlin_out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MUNI_SPECIAL_SRC / "berlin_2026" / "wahlkreise.geojson", berlin_out / "wahlkreise.geojson")
    shutil.copyfile(MUNI_SPECIAL_SRC / "berlin_2026" / "muni_format.json", berlin_out / "muni_format.json")

    muni_manifest = load(MUNI_SRC / "manifest.json")
    manifest = {
        "federal": muni_manifest["federal"],
        "european": muni_manifest["european"],
        "landtag": muni_manifest["landtag"],
        "kommunal": muni_manifest["kommunal"],
        "state_bounds": muni_manifest["state_bounds"],
        "party_info": muni_manifest["party_info"],
    }
    dump(OUT / "manifest.json", manifest)
    print("wrote manifest.json")


if __name__ == "__main__":
    main()
