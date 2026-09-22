"""
Build the dataset for map-election-profile: blend all four election types (Bundestag,
Europawahl, Landtag, Kommunalwahl) into one "who does this place really vote for"
picture per municipality, over a user-adjustable year window (the whole point being
that a fixed all-time blend would average together genuinely different eras - a place
solidly SPD in the 90s and solidly AfD now would look like neither).

No new per-window files are precomputed here - the blend depends on an arbitrary
year-range the user picks at runtime, so it's computed client-side from the same
already-built map-municipality per-year files this app copies in wholesale (same
approach as map-election-timeseries). This script is just that copy step + a manifest.

Run from the repo root or map-election-profile/, after map-municipality/ has been built:
    python map-election-profile/build_election_profile_data.py
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUNI_SRC = ROOT / "map-municipality" / "data" / "prepared"
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

    print("copying municipality boundary...")
    shutil.copyfile(MUNI_SRC / "gemeinden.geojson", OUT / "gemeinden.geojson")

    print("copying per-year election results (all 4 types, all states)...")
    for type_key in ("federal", "european", "landtag", "kommunal"):
        src = MUNI_SRC / type_key
        dst = OUT / type_key
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    muni_manifest = load(MUNI_SRC / "manifest.json")
    manifest = {
        "federal": muni_manifest["federal"],
        "european": muni_manifest["european"],
        "landtag": muni_manifest["landtag"],
        "kommunal": muni_manifest["kommunal"],
        "party_info": muni_manifest["party_info"],
    }
    dump(OUT / "manifest.json", manifest)
    print("wrote manifest.json")


if __name__ == "__main__":
    main()
