"""
Build per-year GeoJSON files for the federal Bundestag Wahlkreis map.

Joins processed/elections/federal_wahlkreis_2002_2025.csv (real vote counts,
2002-2025) against Wahlkreis boundary GeoJSON files (one per election year,
matching that year's actual constituency map) and writes one compact
GeoJSON per year to map/data/prepared/, plus a meta.json with party
colors/labels for the frontend.

Run from the repo root:
    python map/build_federal_wahlkreis_data.py
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ELECTIONS = ROOT / "processed" / "elections"
BOUNDARIES = ROOT / "map" / "data" / "boundaries"
OUT_DIR = ROOT / "map" / "data" / "prepared"
OUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = ["2002", "2005", "2009", "2013", "2017", "2021", "2025"]

META_COLS = {
    "flag_no_valid_votes", "flag_naive_turnout_above_1", "election_year",
    "election_date", "wkr_nr", "wkr_name", "state", "state_name", "stimme",
    "eligible_voters", "number_voters", "valid_votes", "invalid_votes",
    "turnout", "elected_party",
}

# Party display names + official/conventional brand colors.
# "other" is the fallback for any party not listed here.
PARTY_INFO = {
    "cdu_csu": {"label": "CDU/CSU", "color": "#4D4D52"},
    "cdu": {"label": "CDU", "color": "#4D4D52"},
    "csu": {"label": "CSU", "color": "#4D4D52"},
    "spd": {"label": "SPD", "color": "#E3000F"},
    "gruene": {"label": "Grüne", "color": "#46962B"},
    "fdp": {"label": "FDP", "color": "#FFED00"},
    "linke_pds": {"label": "Die Linke", "color": "#BE3075"},
    "afd": {"label": "AfD", "color": "#009EE0"},
    "bsw": {"label": "BSW", "color": "#7D2E68"},
    "npd": {"label": "NPD", "color": "#8B4513"},
    "die_rechte": {"label": "Die Rechte", "color": "#6B3E26"},
    "rep": {"label": "REP", "color": "#6E6E96"},
    "freie_wahler": {"label": "Freie Wähler", "color": "#FF8C00"},
    "piraten": {"label": "Piraten", "color": "#F57900"},
    "volt": {"label": "Volt", "color": "#582C83"},
    "ssw": {"label": "SSW", "color": "#003C8F"},
    "die_partei": {"label": "Die PARTEI", "color": "#A6192E"},
    "other": {"label": "Sonstige", "color": "#999999"},
}


def to_float(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def load_election_rows():
    with open(ELECTIONS / "federal_wahlkreis_2002_2025.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        party_cols = [c for c in reader.fieldnames if c not in META_COLS and c != "cdu_csu"]
        rows = list(reader)
    return rows, party_cols


def party_shares(row, party_cols):
    shares = {}
    for p in party_cols:
        v = to_float(row.get(p))
        if v is not None and v > 0:
            shares[p] = round(v, 4)
    return shares


def top_n(shares, n=6):
    ranked = sorted(shares.items(), key=lambda kv: kv[1], reverse=True)
    return ranked[:n]


def party_style(party):
    info = PARTY_INFO.get(party)
    return info if info else {"label": party, "color": PARTY_INFO["other"]["color"]}


def main():
    rows, party_cols = load_election_rows()

    by_year_wkr = {}
    for row in rows:
        year = row["election_year"]
        wkr_nr = int(row["wkr_nr"])
        key = (year, wkr_nr)
        entry = by_year_wkr.setdefault(key, {})
        shares = party_shares(row, party_cols)
        if row["stimme"] == "erststimme":
            entry["erststimme_shares"] = shares
            entry["elected_party"] = row.get("elected_party") or None
            entry["turnout"] = to_float(row.get("turnout"))
            entry["eligible_voters"] = to_float(row.get("eligible_voters"))
            entry["valid_votes"] = to_float(row.get("valid_votes"))
            entry["wkr_name"] = row.get("wkr_name")
            entry["state_name"] = row.get("state_name")
        else:
            entry["zweitstimme_shares"] = shares

    parties_seen = set()
    year_stats = {}

    for year in YEARS:
        boundary_path = BOUNDARIES / f"wkr_{year}.geojson"
        with open(boundary_path, encoding="utf-8") as f:
            boundary = json.load(f)

        features_out = []
        matched, unmatched = 0, []
        for feat in boundary["features"]:
            props = feat["properties"]
            wkr_nr = props.get("WKR_NR")
            if wkr_nr is None:
                continue
            wkr_nr = int(wkr_nr)
            entry = by_year_wkr.get((year, wkr_nr))
            if entry is None:
                unmatched.append(wkr_nr)
                continue
            matched += 1

            erst = entry.get("erststimme_shares", {})
            zweit = entry.get("zweitstimme_shares", {})
            elected = entry.get("elected_party")
            erst_winner_share = erst.get(elected) if elected else None
            zweit_top = top_n(zweit, 1)
            zweit_top_party, zweit_top_share = (zweit_top[0] if zweit_top else (None, None))

            for p in (elected, zweit_top_party):
                if p:
                    parties_seen.add(p)

            out_props = {
                "wkr_nr": wkr_nr,
                "wkr_name": entry.get("wkr_name") or props.get("WKR_NAME"),
                "state_name": entry.get("state_name") or props.get("LAND_NAME"),
                "elected_party": elected,
                "elected_party_share": erst_winner_share,
                "zweitstimme_top_party": zweit_top_party,
                "zweitstimme_top_share": zweit_top_share,
                "turnout": entry.get("turnout"),
                "eligible_voters": entry.get("eligible_voters"),
                "erststimme_top6": top_n(erst, 6),
                "zweitstimme_top6": top_n(zweit, 6),
            }
            features_out.append({
                "type": "Feature",
                "properties": out_props,
                "geometry": feat["geometry"],
            })

        fc = {"type": "FeatureCollection", "features": features_out}
        out_path = OUT_DIR / f"wkr_{year}.geojson"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(fc, f, ensure_ascii=False, separators=(",", ":"))

        year_stats[year] = {
            "matched": matched,
            "unmatched_boundary_wkr": sorted(set(unmatched)),
            "size_kb": round(out_path.stat().st_size / 1024, 1),
        }
        print(f"{year}: matched {matched} Wahlkreise, "
              f"{len(set(unmatched))} boundary features unmatched, "
              f"wrote {out_path.name} ({year_stats[year]['size_kb']} KB)")

    all_parties = parties_seen | (set(PARTY_INFO.keys()) - {"other"})
    meta = {
        "years": YEARS,
        "party_info": {p: party_style(p) for p in sorted(all_parties)},
        "default_fallback": PARTY_INFO["other"],
    }
    with open(OUT_DIR / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"\nWrote meta.json with {len(meta['party_info'])} parties seen as a plurality winner.")


if __name__ == "__main__":
    main()
