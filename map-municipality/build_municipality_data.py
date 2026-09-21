"""
Build municipality-level (Gemeinde) election data for the municipality choropleth map.

Unlike the federal Wahlkreis map (map/), this map has ONE shared boundary set (all the
election files here are harmonized to 2025 municipality boundaries) and MANY thin
per-election-per-year (or per-state-per-year) data files that get restyled onto it
client-side. This keeps the ~11k-polygon boundary layer loaded exactly once per session.

Covers four election types, each with a real but different "highest resolution" here:
- federal (Bundestag) and european (EU Parliament): nationwide, simultaneous
- landtag (state/Landtag) and kommunal (municipal council): each state votes on its own
  schedule, so these are organized per (state, year), not just per year.

"Winner" here means the plurality party's municipal vote share, an ecological/aggregate
statistic, not a real single-winner seat outcome (see docs/GAPS_AND_LIMITATIONS.md in the
repo root on the ecological-fallacy caveat).

Run from the repo root:
    python map-municipality/build_municipality_data.py
"""
import csv
import io
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ELECTIONS = ROOT / "processed" / "elections"
OUT_DIR = ROOT / "map-municipality" / "data" / "prepared"
BOUNDARY_IN = ROOT / "map-municipality" / "data" / "boundaries" / "gemeinden_2024.geojson"
BOUNDARY_OUT = ROOT / "map-municipality" / "data" / "prepared" / "gemeinden.geojson"

STATE_CODE_TO_NAME = {
    "01": "Schleswig-Holstein", "02": "Hamburg", "03": "Niedersachsen", "04": "Bremen",
    "05": "North Rhine-Westphalia", "06": "Hesse", "07": "Rhineland-Palatinate",
    "08": "Baden-Württemberg", "09": "Bavaria", "10": "Saarland", "11": "Berlin",
    "12": "Brandenburg", "13": "Mecklenburg-Vorpommern", "14": "Saxony",
    "15": "Saxony-Anhalt", "16": "Thuringia",
}


def slugify(name):
    return (name.lower()
            .replace("ü", "ue").replace("ö", "oe").replace("ä", "ae").replace("ß", "ss")
            .replace(" ", "_").replace("-", "_").replace("(", "").replace(")", ""))


PARTY_INFO = {
    "cdu": {"label": "CDU", "color": "#4D4D52"},
    "csu": {"label": "CSU", "color": "#4D4D52"},
    "cdu_csu": {"label": "CDU/CSU", "color": "#4D4D52"},
    "spd": {"label": "SPD", "color": "#E3000F"},
    "gruene": {"label": "Grüne", "color": "#46962B"},
    "fdp": {"label": "FDP", "color": "#FFED00"},
    "linke_pds": {"label": "Die Linke", "color": "#BE3075"},
    "die_linke": {"label": "Die Linke", "color": "#BE3075"},
    "afd": {"label": "AfD", "color": "#009EE0"},
    "bsw": {"label": "BSW", "color": "#7D2E68"},
    "npd": {"label": "NPD", "color": "#8B4513"},
    "die_rechte": {"label": "Die Rechte", "color": "#6B3E26"},
    "rep": {"label": "REP", "color": "#6E6E96"},
    "freie_wahler": {"label": "Freie Wähler", "color": "#FF8C00"},
    "freie_waehler": {"label": "Freie Wähler", "color": "#FF8C00"},
    "piraten": {"label": "Piraten", "color": "#F57900"},
    "volt": {"label": "Volt", "color": "#582C83"},
    "ssw": {"label": "SSW", "color": "#003C8F"},
    "die_partei": {"label": "Die PARTEI", "color": "#A6192E"},
    "other": {"label": "Sonstige / lokale Listen", "color": "#999999"},
}
FALLBACK = {"label": None, "color": "#6f7580"}  # label filled in per-party at runtime

# Columns that are never real party vote-share columns, across all four source files.
EXPLICIT_META = {
    "ags", "ags_name", "ags_21", "election_year", "election_date", "state", "state_name",
    "county", "eligible_voters", "eligible_voters_orig", "number_voters", "number_voters_orig",
    "valid_votes", "invalid_votes", "turnout", "turnout_wo_mailin", "unique_mailin",
    "unique_multi_mailin", "voters_wo_blockingnotice", "voters_blockingnotice", "voters_par25_2",
    "blocked_voters_orig", "voters_w_ballot", "pop_weight", "area_weight", "voters_weight",
    "blocked_weight", "voters_wo_sperrvermerk", "voters_w_sperrvermerk", "voters_par24_2",
    "voters_w_wahlschein",
    # Aggregate/duplicate columns that double-count when cdu/csu are ALSO broken out
    # separately (handled conditionally in party_columns() - "cdu_csu" is deliberately
    # NOT listed here, since some files, e.g. municipal_1990_2026_harm.csv, report Union
    # votes ONLY as this combined column with no separate cdu/csu to duplicate):
    "far_right", "far_left", "far_left_w_linke",
    # Misc meta / non-vote-share columns:
    "total_votes", "total_votes_incogruence", "perc_total_votes_incogruence",
    "total_vote_share", "flag_other_party_residual", "perc_total_votes_incongruence",
    "area_cw", "area", "population", "pop_cw", "weights", "area_ags", "population_ags",
    "employees_ags", "pop_density_ags", "election_type", "n_predecessors",
}
EXCLUDE_PREFIXES = ("flag_", "replaced_0_with_na_", "seats_")


def party_columns(fieldnames):
    cols = [c for c in fieldnames
            if c not in EXPLICIT_META and not c.startswith(EXCLUDE_PREFIXES)]
    # "cdu_csu" is a derived duplicate only when cdu and csu are ALSO present separately;
    # drop it in that case, otherwise it's the only Union column this file has - keep it.
    if "cdu_csu" in cols and "cdu" in cols and "csu" in cols:
        cols.remove("cdu_csu")
    return cols


def to_float(v):
    if v is None or v == "":
        return None
    try:
        f = float(v)
    except ValueError:
        return None
    return f


def read_rows(path):
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as z:
            with z.open(z.namelist()[0]) as f:
                text = f.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        return list(reader), reader.fieldnames
    else:
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader), reader.fieldnames


def top_shares(row, party_cols, n=5):
    shares = {}
    for p in party_cols:
        v = to_float(row.get(p))
        if v is not None and v > 0:
            shares[p] = round(v, 4)
    ranked = sorted(shares.items(), key=lambda kv: kv[1], reverse=True)
    return ranked[:n]


def record_for_row(row, party_cols):
    top = top_shares(row, party_cols, n=5)
    if not top:
        return None
    winner, share = top[0]
    turnout = to_float(row.get("turnout"))
    rec = {"w": winner, "s": share, "b": top}
    if turnout is not None:
        rec["t"] = round(turnout, 4)
    return rec


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def iter_coords(geometry):
    t = geometry["type"]
    coords = geometry["coordinates"]
    if t == "Polygon":
        for ring in coords:
            for lon, lat in ring:
                yield lon, lat
    elif t == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                for lon, lat in ring:
                    yield lon, lat


def build_boundary():
    with open(BOUNDARY_IN, encoding="utf-8") as f:
        d = json.load(f)
    features = []
    state_bounds = {}  # code -> [minlon, minlat, maxlon, maxlat]
    for feat in d["features"]:
        p = feat["properties"]
        ags = p.get("AGS")
        if not ags:
            continue
        features.append({
            "type": "Feature",
            "properties": {"ags": ags, "name": p.get("GEN"), "kind": p.get("BEZ")},
            "geometry": feat["geometry"],
        })
        code = ags[:2]
        b = state_bounds.setdefault(code, [180.0, 90.0, -180.0, -90.0])
        for lon, lat in iter_coords(feat["geometry"]):
            if lon < b[0]: b[0] = lon
            if lat < b[1]: b[1] = lat
            if lon > b[2]: b[2] = lon
            if lat > b[3]: b[3] = lat

    fc = {"type": "FeatureCollection", "features": features}
    write_json(BOUNDARY_OUT, fc)
    print(f"boundary: {len(features)} municipalities -> {BOUNDARY_OUT.name} "
          f"({BOUNDARY_OUT.stat().st_size / 1024 / 1024:.1f} MB)")

    bounds_by_slug = {
        slugify(STATE_CODE_TO_NAME[code]): [[b[1], b[0]], [b[3], b[2]]]
        for code, b in state_bounds.items() if code in STATE_CODE_TO_NAME
    }
    return bounds_by_slug


def build_national(dataset_key, filename, out_subdir):
    rows, fieldnames = read_rows(ELECTIONS / filename)
    party_cols = party_columns(fieldnames)
    years = sorted(set(r["election_year"] for r in rows))
    parties_seen = set()
    for year in years:
        year_rows = [r for r in rows if r["election_year"] == year]
        data = {}
        for row in year_rows:
            ags = row["ags"].zfill(8)
            rec = record_for_row(row, party_cols)
            if rec is None:
                continue
            data[ags] = rec
            parties_seen.add(rec["w"])
        write_json(OUT_DIR / out_subdir / f"{year}.json", data)
    print(f"{dataset_key}: years {years}, {len(rows)} rows, {len(party_cols)} party columns")
    return years, parties_seen


def build_per_state(dataset_key, filename, out_subdir):
    rows, fieldnames = read_rows(ELECTIONS / filename)
    party_cols = party_columns(fieldnames)
    by_state_year = {}
    for row in rows:
        state_name = row.get("state_name") or STATE_CODE_TO_NAME.get(row.get("state", ""), row.get("state"))
        year = row["election_year"]
        by_state_year.setdefault((state_name, year), []).append(row)

    states_out = {}
    parties_seen = set()
    for (state_name, year), year_rows in by_state_year.items():
        slug = slugify(state_name)
        data = {}
        for row in year_rows:
            ags = row["ags"].zfill(8)
            rec = record_for_row(row, party_cols)
            if rec is None:
                continue
            data[ags] = rec
            parties_seen.add(rec["w"])
        if not data:
            continue
        write_json(OUT_DIR / out_subdir / slug / f"{year}.json", data)
        states_out.setdefault(slug, {"label": state_name, "years": []})
        states_out[slug]["years"].append(year)

    for slug in states_out:
        states_out[slug]["years"] = sorted(states_out[slug]["years"])

    print(f"{dataset_key}: {len(states_out)} states, {len(rows)} rows, {len(party_cols)} party columns")
    return states_out, parties_seen


def party_style(party):
    info = PARTY_INFO.get(party)
    if info:
        return info
    return {"label": party, "color": FALLBACK["color"]}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    state_bounds = build_boundary()

    all_parties = set()

    federal_years, p1 = build_national("federal", "federal_municipality_1990_2025_harm2025.csv.zip", "federal")
    european_years, p2 = build_national("european", "european_1990_2024_harm.csv.zip", "european")
    landtag_states, p3 = build_per_state("landtag", "state_municipality_1990_2026_harm2025.csv.zip", "landtag")
    kommunal_states, p4 = build_per_state("kommunal", "municipal_1990_2026_harm.csv", "kommunal")

    all_parties = p1 | p2 | p3 | p4 | (set(PARTY_INFO.keys()) - {"other"})

    manifest = {
        "federal": {"scope": "national", "years": federal_years},
        "european": {"scope": "national", "years": european_years},
        "landtag": {"scope": "state", "states": landtag_states},
        "kommunal": {"scope": "state", "states": kommunal_states},
        "state_bounds": state_bounds,
        "party_info": {p: party_style(p) for p in sorted(all_parties)},
        "default_fallback": PARTY_INFO["other"],
    }
    write_json(OUT_DIR / "manifest.json", manifest)
    print(f"\nWrote manifest.json ({len(all_parties)} distinct parties across all datasets)")


if __name__ == "__main__":
    main()
