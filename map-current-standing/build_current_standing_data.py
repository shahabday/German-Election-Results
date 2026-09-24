"""
Build map-current-standing: for every year 1990-2026, show each municipality's
MOST RECENT applicable election result as of that year - a continuously
updated "best current picture of the whole country," not a blend/average.

The logic, year by year:
  - A nationwide election (Bundestag, or Europawahl when no Bundestag that
    year) refreshes EVERY municipality in the country to that year's result.
    If both happen the same year, Bundestag wins ("the most important").
  - A state-scheduled election (Landtag, or Kommunalwahl when no Landtag that
    year, in that state) refreshes only THAT state's municipalities. If both
    happen in the same state/year, Landtag wins.
  - If a nationwide election ALSO happens that same year, it overwrites
    everything afterward (nationwide is authoritative when both a nationwide
    and a local election land in the same year) - so local updates are
    applied first, then nationwide overwrites on top.
  - A municipality untouched by any election in a given year just keeps
    carrying forward whatever it last showed - it is NOT blanked out.

Each output record keeps the usual {w,s,b,t} shape (same as every other app
here) plus two extra fields so the frontend can show exactly where a result
actually came from: "y" (the real source year) and "src" (federal / european /
landtag / kommunal) - since at any given slider year, different municipalities
can legitimately be showing data from different source years.

Run from the repo root, after map-all-elections/ has been built:
    python map-current-standing/build_current_standing_data.py
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUNI_SRC = ROOT / "map-all-elections" / "data" / "prepared"
TRENDS_SRC = ROOT / "map-trends" / "data" / "prepared"
OUT = Path(__file__).resolve().parent / "data" / "prepared"

STATE_SLUG_TO_CODE = {
    "schleswig_holstein": "01", "hamburg": "02", "niedersachsen": "03", "bremen": "04",
    "north_rhine_westphalia": "05", "hesse": "06", "rhineland_palatinate": "07",
    "baden_wuerttemberg": "08", "bavaria": "09", "saarland": "10", "berlin": "11",
    "brandenburg": "12", "mecklenburg_vorpommern": "13", "saxony": "14",
    "saxony_anhalt": "15", "thuringia": "16",
}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def main():
    manifest = load(MUNI_SRC / "manifest.json")

    federal_years = set(manifest["federal"]["years"])
    european_years = set(manifest["european"]["years"])
    landtag_years = {slug: set(info["years"]) for slug, info in manifest["landtag"]["states"].items()}
    kommunal_years = {slug: set(info["years"]) for slug, info in manifest["kommunal"]["states"].items()}

    all_years = set(federal_years) | set(european_years)
    for ys in landtag_years.values():
        all_years |= ys
    for ys in kommunal_years.values():
        all_years |= ys
    all_years = sorted(all_years, key=int)

    file_cache = {}

    def load_type_year(type_key, year, state_slug=None):
        key = (type_key, state_slug, year)
        if key in file_cache:
            return file_cache[key]
        path = (MUNI_SRC / type_key / state_slug / f"{year}.json") if state_slug else (MUNI_SRC / type_key / f"{year}.json")
        data = load(path) if path.exists() else {}
        file_cache[key] = data
        return data

    current = {}  # ags -> {w,s,b,t,y,src}
    year_events = {}  # year -> {"nationwide": src|None, "states": {slug: src}}

    for year in all_years:
        events = {"nationwide": None, "states": {}}

        # --- local (state-scheduled) refresh first ---
        for slug in STATE_SLUG_TO_CODE:
            local_src = None
            if year in landtag_years.get(slug, ()):
                local_src = "landtag"
            elif year in kommunal_years.get(slug, ()):
                local_src = "kommunal"
            if not local_src:
                continue
            data = load_type_year(local_src, year, slug)
            for ags, rec in data.items():
                current[ags] = {**rec, "y": year, "src": local_src}
            events["states"][slug] = local_src

        # --- nationwide refresh second (overwrites local for this year) ---
        nation_src = "federal" if year in federal_years else ("european" if year in european_years else None)
        if nation_src:
            data = load_type_year(nation_src, year)
            for ags, rec in data.items():
                current[ags] = {**rec, "y": year, "src": nation_src}
            events["nationwide"] = nation_src

        year_events[year] = events
        dump(OUT / f"{year}.json", current)
        print(f"{year}: {len(current)} municipalities known "
              f"(nationwide={nation_src}, local states={len(events['states'])})")

    print("copying boundaries...")
    shutil.copyfile(MUNI_SRC / "gemeinden.geojson", OUT / "gemeinden.geojson")
    shutil.copyfile(TRENDS_SRC / "state_outlines.geojson", OUT / "state_outlines.geojson")

    out_manifest = {
        "years": all_years,
        "year_events": year_events,
        "party_info": manifest["party_info"],
        "default_fallback": manifest["default_fallback"],
        "state_labels": {slug: manifest["landtag"]["states"][slug]["label"] for slug in STATE_SLUG_TO_CODE},
    }
    dump(OUT / "manifest.json", out_manifest)
    print("wrote manifest.json")


if __name__ == "__main__":
    main()
