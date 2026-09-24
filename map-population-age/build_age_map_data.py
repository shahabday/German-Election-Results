"""Builds the county-level age-group choropleth dataset from regionalstatistik.de pulls.

Raw files (../map-population-pyramid/data/raw/population_by_age_sex_county_<year>.json)
were fetched by hand through the regionalstatistik.de GENESIS web GUI - table
12411-04-02-4 became too large for the county+single-year-of-age+sex combination,
so this uses the pre-grouped 20-band table instead: 12411-09-01-4 ("Bevoelkerung
nach Geschlecht und Altersgruppen (20)", Stichtag 31.12.). Reuses the same raw pull
the population-pyramid tool made (that tool needed state-level single-year-of-age
data and hit the same size wall, landing on this county+20-band table as a
byproduct), rather than fetching twice. Each raw file is
{ags: {age_band_label: {"m": count, "f": count}}} for one Stichtag, full 490-county
coverage (this is complete registry data, not survey-based, so no suppression).

Covers the same six years as the population pyramid (2011, 2014, 2017, 2020, 2023,
2025) - one GENESIS Werteabruf per year, so kept in sync with that tool's year set
rather than fetching the full 2011-2025 annual series.

Output: for each year, for each of the 20 age bands, a county->total-population
{ags: count} map plus a share-of-county-population version, written as
data/prepared/age_<band-slug>/<year>.json, so the map tool can reuse the exact
same "one flat county->value JSON per year" shape as the other map-* tools' county
data files.
"""
import json
import re
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "map-population-pyramid" / "data" / "raw"
OUT = Path(__file__).resolve().parent / "data" / "prepared"
YEARS = ["2011", "2014", "2017", "2020", "2023", "2025"]


def band_slug(label):
    if label == "unter 5 Jahre":
        return "00-04"
    if label == "95 Jahre und mehr":
        return "95+"
    m = re.match(r"(\d+) bis unter (\d+) Jahre", label)
    lo, hi = int(m.group(1)), int(m.group(2)) - 1
    return f"{lo:02d}-{hi:02d}"


def band_sort_key(slug):
    return 999 if slug == "95+" else int(slug.split("-")[0])


def main():
    with open(RAW / "population_by_age_sex_county_2025.json", encoding="utf-8") as f:
        sample = json.load(f)
    any_county = next(iter(sample.values()))
    bands = sorted({band_slug(lbl) for lbl in any_county}, key=band_sort_key)

    manifest_bands = []
    for year in YEARS:
        with open(RAW / f"population_by_age_sex_county_{year}.json", encoding="utf-8") as f:
            data = json.load(f)

        county_totals = {}
        band_totals = {slug: {} for slug in bands}
        for ags, ages in data.items():
            # Skip nested/duplicate entities (e.g. Berlin's 12 boroughs, each an
            # 8-digit sub-code of "11000") - their populations are already counted
            # in their parent county's row, so including them too double-counts.
            if not (len(ags) == 5 and ags.isdigit()):
                continue
            total = 0
            for label, sexes in ages.items():
                slug = band_slug(label)
                m, fem = sexes.get("m"), sexes.get("f")
                count = (m or 0) + (fem or 0)
                band_totals[slug][ags] = count
                total += count
            county_totals[ags] = total

        for slug in bands:
            out_dir = OUT / f"age_{slug}"
            out_dir.mkdir(parents=True, exist_ok=True)
            record = {}
            for ags, count in band_totals[slug].items():
                total = county_totals.get(ags, 0)
                record[ags] = {
                    "count": count,
                    "share": round(count / total * 100, 2) if total else None,
                }
            with open(out_dir / f"{year}.json", "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, separators=(",", ":"))

    for slug in bands:
        lo = slug.split("-")[0] if "-" in slug else "95"
        label = f"{int(lo)}+" if slug == "95+" else f"{int(slug.split('-')[0])}–{int(slug.split('-')[1])}"
        manifest_bands.append({"slug": slug, "label": label})

    manifest = {"years": YEARS, "bands": manifest_bands}
    with open(OUT / "age_map_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, separators=(",", ":"))

    print(f"bands: {[b['slug'] for b in manifest_bands]}")
    print(f"years: {YEARS}")
    # sanity: national total for 2025, band 00-04
    with open(OUT / "age_00-04" / "2025.json", encoding="utf-8") as f:
        d = json.load(f)
    total_00_04 = sum(v["count"] for v in d.values())
    print(f"2025 age 0-4 total across counties: {total_00_04:,}")


if __name__ == "__main__":
    main()
