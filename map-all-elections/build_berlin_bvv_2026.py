"""
Integrate the 2026 Berlin BVV elections (Bezirksverordnetenversammlungen - district
councils, Berlin's "Kommunalwahl equivalent"), held 2026-09-20 alongside the AGH vote,
at Bezirk resolution (12 districts). Sibling script to build_berlin_2026.py (AGH) - same
site, same table markup, same reasoning for why this needs a special layer (Berlin is one
AGS in the municipal-level GERDA file, so "Kommunalwahl" for Berlin was a single blob
until now, just like Landtag was before build_berlin_2026.py). Unlike AGH, BVV is a
single proportional vote (no Erststimme/Wahlkreis direct mandate) at just 12 Bezirke,
not 78 Wahlkreise, so each Bezirk IS its own real administrative unit already, and the
results table has one vote-count set per party instead of two.

Source: https://wahlen-berlin.de/wahlen/BE2026/Afspraes/bvv/ - "Vorläufiges Ergebnis".

Inputs (already fetched - see data/special/berlin_bvv_2026/):
- Bezirk boundaries: bezirke_raw.geojson (the site's own m_307744_0_2_0_12.json map layer)
- Per-Bezirk result pages: raw_pages/<gebietNr>.html for all 12 Bezirke

Run from the repo root:
    python map-all-elections/build_berlin_bvv_2026.py
"""
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "map-all-elections" / "data" / "special" / "berlin_bvv_2026"
RAW_DIR = OUT_DIR / "raw_pages"
BOUNDARY_RAW = OUT_DIR / "bezirke_raw.geojson"
PREPARED_KOMMUNAL_DIR = ROOT / "map-all-elections" / "data" / "prepared" / "kommunal"
MANIFEST_PATH = ROOT / "map-all-elections" / "data" / "prepared" / "manifest.json"
BERLIN_AGS = "11000000"

SUMMARY_LABELS = {"Wahlberechtigte", "W\u00e4hlende", "Ung\u00fcltige Stimmen", "G\u00fcltige Stimmen"}

PARTY_KEY_MAP = {
    "CDU": "cdu_csu", "SPD": "spd", "GR\u00dcNE": "gruene", "Die Linke": "linke_pds",
    "AfD": "afd", "FDP": "fdp", "BSW": "bsw", "Volt": "volt",
    "Die PARTEI": "die_partei", "Tierschutzpartei": "tierschutzpartei",
    "MIETERPARTEI": "mieterpartei", "Die Urbane.": "die_urbane", "DKP": "dkp",
    "\u00d6DP": "oedp", "HEIMAT": "heimat", "SGP": "sgp", "MERA25": "mera25", "PdF": "pdf",
    "FREIE W\u00c4HLER": "freie_wahler",
}


class ResultsTableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_table = False
        self.rows = []
        self._cur_row = None
        self._cur_cell_sort = None
        self._cur_cell_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table" and "table-stimmen" in (attrs.get("class") or ""):
            self.in_table = True
            return
        if not self.in_table:
            return
        if tag == "tr":
            self._cur_row = []
        elif tag in ("th", "td"):
            self._cur_cell_sort = attrs.get("data-sort", None)
            self._cur_cell_text = []

    def handle_endtag(self, tag):
        if not self.in_table:
            return
        if tag == "table":
            self.in_table = False
        elif tag == "tr":
            if self._cur_row is not None:
                self.rows.append(self._cur_row)
            self._cur_row = None
        elif tag in ("th", "td"):
            if self._cur_row is not None:
                text = "".join(self._cur_cell_text).strip()
                self._cur_row.append((self._cur_cell_sort, text))
            self._cur_cell_sort = None

    def handle_data(self, data):
        if self.in_table and self._cur_row is not None:
            self._cur_cell_text.append(data)


def parse_number(s):
    if s is None or s == "":
        return None
    s = s.strip()
    if s in ("-", ""):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_bezirk_page(html_text):
    parser = ResultsTableParser()
    parser.feed(html_text)

    summary = {}
    parties = []
    for row in parser.rows:
        if len(row) < 4:
            continue
        label_sort, label_text = row[0]
        if label_sort in SUMMARY_LABELS:
            vals = [parse_number(c[0]) for c in row[1:4]]
            summary[label_sort] = {"count": vals[0], "pct": vals[1]}
        elif label_text:
            vals = [parse_number(c[0]) for c in row[1:4]]
            if vals[0]:
                key = PARTY_KEY_MAP.get(label_text, "other")
                parties.append((key, vals[0], vals[1]))

    eligible = summary.get("Wahlberechtigte", {}).get("count")
    voters = summary.get("W\u00e4hlende", {}).get("count")
    valid = summary.get("G\u00fcltige Stimmen", {}).get("count")
    if not valid:
        return None

    totals = {}
    for key, count, _pct in parties:
        totals[key] = totals.get(key, 0) + count
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    top5 = [[p, round(c / valid, 4)] for p, c in ranked[:5]]
    turnout = round(voters / eligible, 4) if eligible and voters else None

    return {"eligible": eligible, "voters": voters, "valid": valid,
            "turnout": turnout, "top5": top5, "totals": totals}


def main():
    with open(BOUNDARY_RAW, encoding="utf-8") as f:
        boundary_raw = json.load(f)
    boundary_out = {"type": "FeatureCollection", "features": []}
    gebiet_nrs = []
    for feat in boundary_raw["geoJSON"]["features"]:
        p = feat["properties"]
        gebiet_nrs.append(p["gebietNr"])
        boundary_out["features"].append({
            "type": "Feature",
            "properties": {"gebiet_nr": p["gebietNr"], "name": p["name"]},
            "geometry": feat["geometry"],
        })
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "bezirke.geojson", "w", encoding="utf-8") as f:
        json.dump(boundary_out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"boundary: {len(gebiet_nrs)} Bezirke")

    muni_format = {}
    citywide_totals = {}
    eligible_sum = voters_sum = 0
    for nr in gebiet_nrs:
        page_path = RAW_DIR / f"{nr}.html"
        rec = parse_bezirk_page(page_path.read_text(encoding="utf-8"))
        if rec is None:
            print(f"WARNING: Bezirk {nr} had no parseable result")
            continue
        muni_format[nr] = {
            "w": rec["top5"][0][0], "s": rec["top5"][0][1],
            "b": rec["top5"], "t": rec["turnout"],
        }
        for k, v in rec["totals"].items():
            citywide_totals[k] = citywide_totals.get(k, 0) + v
        eligible_sum += rec["eligible"] or 0
        voters_sum += rec["voters"] or 0

    with open(OUT_DIR / "muni_format.json", "w", encoding="utf-8") as f:
        json.dump(muni_format, f, ensure_ascii=False, separators=(",", ":"))
    print(f"results: {len(muni_format)}/{len(gebiet_nrs)} Bezirke parsed")

    valid_sum = sum(citywide_totals.values())
    ranked = sorted(citywide_totals.items(), key=lambda kv: kv[1], reverse=True)
    top5 = [[p, round(c / valid_sum, 4)] for p, c in ranked[:5]]
    turnout = round(voters_sum / eligible_sum, 4) if eligible_sum else None
    rollup = {BERLIN_AGS: {"w": top5[0][0], "s": top5[0][1], "b": top5, "t": turnout}}
    rollup_dir = PREPARED_KOMMUNAL_DIR / "berlin"
    rollup_dir.mkdir(parents=True, exist_ok=True)
    with open(rollup_dir / "2026.json", "w", encoding="utf-8") as f:
        json.dump(rollup, f, ensure_ascii=False, separators=(",", ":"))
    print(f"citywide rollup: {ranked[0][0]} leads with {top5[0][1]*100:.1f}% "
          f"(of {valid_sum} valid votes across {len(muni_format)} Bezirke)")

    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)
    years = manifest["kommunal"]["states"]["berlin"]["years"]
    if "2026" not in years:
        years.append("2026")
        years.sort()
    manifest.setdefault("special", {}).setdefault("kommunal", {}).setdefault("berlin", {})["2026"] = {
        "boundary": "special/berlin_bvv_2026/bezirke.geojson",
        "data": "special/berlin_bvv_2026/muni_format.json",
        "key_prop": "gebiet_nr",
        "status": "Vorl\u00e4ufiges Ergebnis (preliminary result, published 2026-09-21 - not "
                  "yet the certified final count)",
        "source_label": "wahlen-berlin.de (Landeswahlleiterin Berlin) - BVV-Wahlen",
        "note": "Bezirk (district) resolution — the BVV vote is proportional only, no "
                "direct-mandate seats, so this is 12 real administrative districts rather "
                "than a finer constituency layer.",
    }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, separators=(",", ":"))
    print("patched manifest.json: added 2026 to Berlin Kommunalwahl years + special-layer entry")


if __name__ == "__main__":
    main()
