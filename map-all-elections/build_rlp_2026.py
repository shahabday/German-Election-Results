"""
Integrate the 2026 Rhineland-Palatinate (RLP) Landtag election, held 2026-03-22, at
municipality resolution. Unlike Berlin/MV/Saxony-Anhalt, this is the CERTIFIED FINAL
result (festgestellt 2026-04-02), not a preliminary count - it's just missing from GERDA.

Source: https://www.wahlen.rlp.de (Landeswahlleiter RLP), per-Stimmbezirk-and-above
Excel export, which conveniently already includes one row per individual municipality
(kennzeichen "GD" = Ortsgemeinde, "VF" = Verbandsfreie Gemeinde, "KS" = Kreisfreie
Stadt) - no precinct-level aggregation needed, unlike the Berlin/MV/LSA scripts.

The file has no AGS column, only RLP's own internal "Identifikationsschlüssel" and a
name ("Bezeichnung"). Matched to our municipality boundary (data/prepared/gemeinden.geojson)
by normalized name instead - unambiguous single matches only, anything else is logged
and left out (shows as "no data" on the map for that one municipality) rather than guessed.

Run from the repo root, after build_municipality_data.py:
    python map-all-elections/build_rlp_2026.py
"""
import json
import re
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
XLSX_PATH = ROOT / "map-all-elections" / "data" / "special" / "rlp_2026" / "stimmbezirke.xlsx"
BOUNDARY_PATH = ROOT / "map-all-elections" / "data" / "prepared" / "gemeinden.geojson"
OUT_PATH = ROOT / "map-all-elections" / "data" / "prepared" / "landtag" / "rhineland_palatinate" / "2026.json"
MANIFEST_PATH = ROOT / "map-all-elections" / "data" / "prepared" / "manifest.json"

MUNICIPALITY_KENNZEICHEN = {"GD", "VF", "KS"}
NAME_SUFFIXES = [", Stadt", ", Verbandsfreie Gemeinde", ", Kreisfreie Stadt"]

# Landesstimme (party-list vote, our primary metric everywhere else) columns: label -> count col index
ZWEIT_PARTY_COLS = {
    "SPD": 121, "CDU": 123, "GRÜNE": 125, "AfD": 127, "FDP": 129,
    "FREIE WÄHLER": 131, "Die Linke": 133, "Tierschutzpartei": 135, "Volt": 137,
    "ÖDP": 139, "BSW": 141, "PdH": 143, "Bastian Ruhl": 145,
    "Team Todenhöfer": 147, "Yunus Emre": 149, "Die PARTEI": 151,
}
PARTY_KEY_MAP = {
    "SPD": "spd", "CDU": "cdu", "GRÜNE": "gruene", "AfD": "afd", "FDP": "fdp",
    "FREIE WÄHLER": "freie_wahler", "Die Linke": "linke_pds",
    "Tierschutzpartei": "tierschutzpartei", "Volt": "volt", "ÖDP": "oedp",
    "BSW": "bsw", "PdH": "pdh", "Bastian Ruhl": "other", "Team Todenhöfer": "other",
    "Yunus Emre": "other", "Die PARTEI": "die_partei",
}
PARTY_LABELS = {"pdh": "PdH (Partei der Humanisten)"}

VALID_LANDESSTIMMEN_COL = 119
ELIGIBLE_COL = 6
VOTERS_COL = 10


def normalize_name(name):
    for suf in NAME_SUFFIXES:
        if name.endswith(suf):
            name = name[: -len(suf)]
    return name.strip()


def load_boundary_names():
    with open(BOUNDARY_PATH, encoding="utf-8") as f:
        d = json.load(f)
    by_name = {}
    for feat in d["features"]:
        p = feat["properties"]
        if not p["ags"].startswith("07"):
            continue
        by_name.setdefault(p["name"], []).append(p["ags"])
    return by_name


def top5(shares):
    ranked = sorted(((p, v) for p, v in shares.items() if v is not None and v > 0),
                     key=lambda kv: kv[1], reverse=True)
    return [[p, round(v, 4)] for p, v in ranked[:5]]


def main():
    name_index = load_boundary_names()
    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True, data_only=True)
    ws = wb.active

    out = {}
    unmatched, ambiguous = [], []
    for row in ws.iter_rows(min_row=4, values_only=True):
        kennzeichen = row[2]
        if kennzeichen not in MUNICIPALITY_KENNZEICHEN:
            continue
        raw_name = row[3]
        name = normalize_name(raw_name)
        candidates = name_index.get(name)
        if not candidates:
            unmatched.append(raw_name)
            continue
        if len(candidates) > 1:
            ambiguous.append(raw_name)
            continue
        ags = candidates[0]

        valid = row[VALID_LANDESSTIMMEN_COL]
        if not valid:
            continue
        shares = {}
        for label, col in ZWEIT_PARTY_COLS.items():
            count = row[col]
            if count:
                key = PARTY_KEY_MAP[label]
                shares[key] = shares.get(key, 0) + count / valid
        b = top5(shares)
        if not b:
            continue
        eligible = row[ELIGIBLE_COL]
        voters = row[VOTERS_COL]
        turnout = round(voters / eligible, 4) if eligible and voters else None
        out[ags] = {"w": b[0][0], "s": b[0][1], "b": b, "t": turnout}

    print(f"matched {len(out)} municipalities, {len(unmatched)} unmatched, {len(ambiguous)} ambiguous")
    if unmatched:
        print("unmatched sample:", unmatched[:15])
    if ambiguous:
        print("ambiguous sample:", ambiguous[:15])

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {OUT_PATH.relative_to(ROOT)}")

    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)
    years = manifest["landtag"]["states"]["rhineland_palatinate"]["years"]
    if "2026" not in years:
        years.append("2026")
        years.sort()
    for key, label in PARTY_LABELS.items():
        manifest["party_info"].setdefault(key, {"label": label, "color": manifest["default_fallback"]["color"]})
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, separators=(",", ":"))
    print("patched manifest.json: added 2026 to Rhineland-Palatinate Landtag years")


if __name__ == "__main__":
    main()
