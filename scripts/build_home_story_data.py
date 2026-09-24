"""Builds the four election-type mosaics for the scroll-story landing page
(index.html): one flat {ags: winning_party} lookup per election type, each
showing every municipality's MOST RECENT result of that type.

Bundestag and Europawahl are simultaneous nationwide, so "most recent" is
just the single latest year file. Landtag and Kommunalwahl are staggered by
state (each state runs its own election calendar), so this walks each
state's own folder and takes its own latest available year - producing a
genuine mosaic where different states are shown as of different years,
which is the actual state of the country at any given moment, not an
approximation.

Run from the repo root:
    python scripts/build_home_story_data.py
"""
import json
from pathlib import Path

SRC = Path("map-all-elections/data/prepared")
OUT = Path("data/home_story")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def latest_year_file(dir_path):
    years = sorted(dir_path.glob("*.json"), key=lambda p: int(p.stem))
    return years[-1] if years else None


def simple_type(type_dir):
    """federal/ or european/: one folder of year files, nationwide at once."""
    f = latest_year_file(SRC / type_dir)
    data = load(f)
    return {ags: rec["w"] for ags, rec in data.items() if rec.get("w")}, f.stem


def staggered_type(type_dir):
    """landtag/ or kommunal/: one subfolder per state, each with its own years."""
    out = {}
    years_used = {}
    state_dir = SRC / type_dir
    for state_path in sorted(state_dir.iterdir()):
        if not state_path.is_dir():
            continue
        f = latest_year_file(state_path)
        if not f:
            continue
        data = load(f)
        for ags, rec in data.items():
            if rec.get("w"):
                out[ags] = rec["w"]
        years_used[state_path.name] = f.stem
    return out, years_used


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    federal, federal_year = simple_type("federal")
    with open(OUT / "federal.json", "w", encoding="utf-8") as f:
        json.dump(federal, f, ensure_ascii=False, separators=(",", ":"))
    print(f"federal: {len(federal)} municipalities, year {federal_year}")

    european, european_year = simple_type("european")
    with open(OUT / "european.json", "w", encoding="utf-8") as f:
        json.dump(european, f, ensure_ascii=False, separators=(",", ":"))
    print(f"european: {len(european)} municipalities, year {european_year}")

    landtag, landtag_years = staggered_type("landtag")
    with open(OUT / "landtag.json", "w", encoding="utf-8") as f:
        json.dump(landtag, f, ensure_ascii=False, separators=(",", ":"))
    print(f"landtag: {len(landtag)} municipalities, per-state years: {landtag_years}")

    kommunal, kommunal_years = staggered_type("kommunal")
    with open(OUT / "kommunal.json", "w", encoding="utf-8") as f:
        json.dump(kommunal, f, ensure_ascii=False, separators=(",", ":"))
    print(f"kommunal: {len(kommunal)} municipalities, per-state years: {kommunal_years}")


if __name__ == "__main__":
    main()
