"""
Integrate the 2026 Landtag elections for Mecklenburg-Vorpommern (2026-09-20) and
Saxony-Anhalt (2026-09-06) at municipality resolution. Like Berlin (see
build_berlin_2026.py), these postdate GERDA's snapshot and are sourced live from each
state's own official results portal instead:

- MV:  https://wahlen.mvnet.de/dateien/ergebnisse.2026/landtagswahl/csv/l_gemeinden.csv
- LSA: https://wahlergebnisse.sachsen-anhalt.de/wahlen/lt26/downloads/Ergebnisse_Gemeinden_LT_2026.csv

Unlike Berlin, both of these publish real per-Gemeinde results with the standard 8-digit
AGS - no special boundary layer needed, they join straight onto the shared
map-municipality/data/prepared/gemeinden.geojson used by everything else. So this script
writes directly into the same landtag/<state>/<year>.json shape build_municipality_data.py
produces, and patches manifest.json's `years` list for each state (NOT the `special` key -
that's Berlin-only).

Run from the repo root, after build_municipality_data.py:
    python map-municipality/build_state_elections_2026.py
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "map-municipality" / "data" / "special"
OUT_DIR = ROOT / "map-municipality" / "data" / "prepared" / "landtag"
MANIFEST_PATH = ROOT / "map-municipality" / "data" / "prepared" / "manifest.json"

# party column label (as published) -> our internal key. Falls back to a slugified
# version of the label for anything not listed (kept in sync loosely with
# build_municipality_data.py / build_berlin_2026.py's PARTY_INFO keys where they overlap).
PARTY_KEY_MAP = {
    "SPD": "spd", "AfD": "afd", "CDU": "cdu", "Die Linke": "linke_pds",
    "GRÜNE": "gruene", "FDP": "fdp", "Tierschutzpartei": "tierschutzpartei",
    "FREIE WÄHLER": "freie_wahler", "Die PARTEI": "die_partei", "PIRATEN": "piraten",
    "ÖDP": "oedp", "Bündnis C": "bundnis_c", "BSW": "bsw",
    "Handwerker Partei Deutschland": "handwerker_partei", "KPD": "kpd", "PdF": "pdf",
    "Team Freiheit": "team_freiheit", "Volt": "volt", "WLD": "wld", "LfK": "lfk",
    "Einzelbewerber": "other", "dieBasis": "diebasis", "Gartenpartei": "gartenpartei",
    "TIERSCHUTZALLIANZ": "tierschutzallianz", "HEIMAT": "heimat", "EB": "other",
}

PARTY_LABELS = {
    "bundnis_c": "Bündnis C", "handwerker_partei": "Handwerker Partei Deutschland",
    "kpd": "KPD", "team_freiheit": "Team Freiheit", "wld": "WLD", "lfk": "LfK",
    "diebasis": "dieBasis", "gartenpartei": "Gartenpartei",
    "tierschutzallianz": "TIERSCHUTZALLIANZ",
}


def to_float_de(s):
    if s is None:
        return None
    s = s.strip()
    if s in ("", "x", "-"):
        return None
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def top5(shares):
    ranked = sorted(((p, v) for p, v in shares.items() if v is not None and v > 0),
                     key=lambda kv: kv[1], reverse=True)
    return [[p, round(v, 4)] for p, v in ranked[:5]]


def build_mv():
    """MV's own export: 'Ausgabe' A (absolute)/P (percent) row pairs per Gemeinde,
    'Erst-/Zweitstimme' 1/2. Uses the P rows directly (already a %). Amt-collective
    municipalities' postal votes are rolled into a separate Amt-level pseudo-row per the
    file's own note - those pseudo-rows aren't real Gemeinden with boundaries, so they're
    dropped; the true per-Gemeinde figures below are Urne-only for those places."""
    path = RAW_DIR / "mv_2026" / "l_gemeinden.csv"
    with open(path, encoding="cp1252") as f:
        lines = f.readlines()
    header_idx = next(i for i, l in enumerate(lines) if l.startswith("Berechnungsdatum"))
    reader = csv.DictReader(lines[header_idx:], delimiter=";")
    party_cols = [c for c in reader.fieldnames
                  if c not in ("Berechnungsdatum", "Ausgabe", "Kreis", "Kreisname", "Amt",
                               "Amtsname", "Gemeinde", "Gemeindename", "Wahlbezirke insg.",
                               "Erf. Wahlbezirke", "Wahlberechtigte", "Wähler",
                               "Wahlbeteiligung", "Erst-/Zweitstimme", "Ungültige Stimmen",
                               "Gültige Stimmen")]

    by_gem = {}
    for row in reader:
        ags = row["Gemeinde"].strip()
        if len(ags) != 8 or not ags.isdigit():
            continue  # skip Amt-level pseudo-rows etc.
        entry = by_gem.setdefault(ags, {})
        turnout = to_float_de(row["Wahlbeteiligung"])
        if turnout is not None:
            entry["turnout"] = round(turnout / 100, 4)
        if row["Ausgabe"] != "P":
            continue
        shares = {}
        for col in party_cols:
            key = PARTY_KEY_MAP.get(col.strip(), col.strip().lower().replace(" ", "_"))
            v = to_float_de(row[col])
            if v is not None:
                shares[key] = v / 100
        stimme = row["Erst-/Zweitstimme"]
        if stimme == "2":  # Zweitstimme = party-list vote, our primary metric
            entry["shares"] = shares

    out = {}
    for ags, entry in by_gem.items():
        shares = entry.get("shares")
        if not shares:
            continue
        b = top5(shares)
        if not b:
            continue
        out[ags] = {"w": b[0][0], "s": b[0][1], "b": b, "t": entry.get("turnout")}
    return out


def build_sachsen_anhalt():
    """LSA's export: one row per (Gemeinde, Wahllokal in {'', 'U', 'B'}) with raw vote
    counts (not percentages) - '' is the combined Urne+Briefwahl total, which is what we
    want. F0x.* columns are Zweitstimme (party list, our primary metric)."""
    path = RAW_DIR / "sachsen_anhalt_2026" / "gemeinden.csv"
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    out = {}
    for row in rows:
        if row["Wahllokal"] != "" or row["Satzart"] != "GEM":
            continue
        ags = row["Schlüsselnummer"].strip()
        if len(ags) != 8 or not ags.isdigit():
            continue
        valid = to_float_de(row["F.Gültige.Zweitstimmen"])
        if not valid:
            continue
        shares = {}
        for col, val in row.items():
            if not col.startswith("F") or "." not in col or col in (
                    "F.Ungültige.Zweitstimmen", "F.Gültige.Zweitstimmen"):
                continue
            label = col.split(".", 1)[1]
            key = PARTY_KEY_MAP.get(label, label.lower().replace(" ", "_"))
            count = to_float_de(val)
            if count:
                shares[key] = count / valid
        b = top5(shares)
        if not b:
            continue
        wahlberechtigte = to_float_de(row["A.Wahlberechtigte"])
        waehler = to_float_de(row["B.Wähler"])
        turnout = round(waehler / wahlberechtigte, 4) if wahlberechtigte and waehler else None
        out[ags] = {"w": b[0][0], "s": b[0][1], "b": b, "t": turnout}
    return out


def patch_manifest(states_added):
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)
    for slug in states_added:
        years = manifest["landtag"]["states"][slug]["years"]
        if "2026" not in years:
            years.append("2026")
            years.sort()
    for key, label in PARTY_LABELS.items():
        manifest["party_info"].setdefault(key, {"label": label, "color": manifest["default_fallback"]["color"]})
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, separators=(",", ":"))


def main():
    mv_data = build_mv()
    (OUT_DIR / "mecklenburg_vorpommern").mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "mecklenburg_vorpommern" / "2026.json", "w", encoding="utf-8") as f:
        json.dump(mv_data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Mecklenburg-Vorpommern 2026: {len(mv_data)} Gemeinden")

    lsa_data = build_sachsen_anhalt()
    (OUT_DIR / "saxony_anhalt").mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "saxony_anhalt" / "2026.json", "w", encoding="utf-8") as f:
        json.dump(lsa_data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Saxony-Anhalt 2026: {len(lsa_data)} Gemeinden")

    patch_manifest(["mecklenburg_vorpommern", "saxony_anhalt"])
    print("patched manifest.json: added 2026 to both states' Landtag years")


if __name__ == "__main__":
    main()
