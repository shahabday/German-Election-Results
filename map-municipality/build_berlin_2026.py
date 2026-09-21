"""
Integrate the 2026 Berlin Abgeordnetenhauswahl (state parliament election, held
2026-09-20) at Wahlkreis resolution (78 constituencies) into the municipality map.

This is a special case, kept deliberately separate from build_municipality_data.py:
- It's the only Landtag election in this repo sourced live from the state's own results
  portal rather than from GERDA (GERDA's data predates this election by about a day -
  see map-municipality/README.md).
- It's the only Landtag election rendered at Wahlkreis (78 areas) resolution instead of
  municipality resolution - Berlin is one municipality (AGS 11000000) in the harmonized
  election files, so a "which party won this municipality" map would just be one blob;
  the real electoral geography here is Berlin's 78 Abgeordnetenhaus constituencies, each
  with a real Erststimme direct-mandate winner, exactly like a Bundestag Wahlkreis.

Source: https://wahlen-berlin.de (Landeswahlleiterin), "Vorläufiges Ergebnis" (preliminary
result) as published the morning after the election. Results WILL change slightly once
certified - re-run this script against the same URLs later to refresh.

Inputs (already fetched into a scratch dir by hand - see fetch step below):
- Wahlkreis boundaries: m_303539_0_3_0_78.json (the site's own map layer for the 78
  constituencies - saved locally as boundaries/berlin_2026_wahlkreise_raw.geojson)
- Per-Wahlkreis result pages: ergebnisse_wahlkreis_<gebietNr>.html for all 78 gebietNr

Run from the repo root:
    python map-municipality/build_berlin_2026.py
"""
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "map-municipality" / "data" / "special" / "berlin_2026" / "raw_pages"
BOUNDARY_IN = ROOT / "map-municipality" / "data" / "special" / "berlin_2026" / "berlin_2026_wahlkreise_raw.geojson"
OUT_DIR = ROOT / "map-municipality" / "data" / "special" / "berlin_2026"
PREPARED_LANDTAG_DIR = ROOT / "map-municipality" / "data" / "prepared" / "landtag"
BERLIN_AGS = "11000000"

SUMMARY_LABELS = {"Wahlberechtigte", "Wählende", "Ungültige Stimmen", "Gültige Stimmen"}

# Party abbreviation (as shown on wahlen-berlin.de) -> our internal party key.
# Kept consistent with map-municipality/build_municipality_data.py's PARTY_INFO keys
# where the party already exists there.
PARTY_KEY_MAP = {
    "CDU": "cdu_csu", "SPD": "spd", "GRÜNE": "gruene", "Die Linke": "linke_pds",
    "AfD": "afd", "FDP": "fdp", "BSW": "bsw", "Volt": "volt",
    "Die PARTEI": "die_partei", "Tierschutzpartei": "tierschutzpartei",
    "MIETERPARTEI": "mieterpartei", "Die Urbane.": "die_urbane", "DKP": "dkp",
    "ÖDP": "oedp", "HEIMAT": "heimat", "SGP": "sgp", "MERA25": "mera25", "PdF": "pdf",
}


class ResultsTableParser(HTMLParser):
    """Parses the single <table class="tablesaw table-stimmen"> on a wahlen-berlin.de
    Wahlkreis results page into rows of (kind, label_or_party, candidate, data_sorts)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_table = False
        self.depth = 0
        self.rows = []
        self._cur_row = None
        self._cur_cell_sort = None
        self._cur_cell_text = []
        self._in_abbr = False
        self._abbr_text = []
        self._capture_text_for_sort = False

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
        elif tag == "abbr":
            self._in_abbr = True
            self._abbr_text = []

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
        elif tag == "abbr":
            self._in_abbr = False

    def handle_data(self, data):
        if self.in_table and self._cur_row is not None:
            self._cur_cell_text.append(data)


def parse_number(s):
    # s comes from a data-sort="..." attribute, already a plain float string
    # (e.g. "32501", "79.0837205009", "-1.7338031616") - NOT the German-formatted
    # display text ("32.501", "79,1 %"), so no locale cleanup needed here.
    if s is None or s == "":
        return None
    s = s.strip()
    if s in ("-", ""):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _sum_by_key(pairs):
    out = {}
    for k, v in pairs:
        out[k] = out.get(k, 0) + v
    return out


def parse_wahlkreis_page(html_text, gebiet_nr):
    parser = ResultsTableParser()
    parser.feed(html_text)

    summary = {}
    parties = []

    for row in parser.rows:
        if len(row) < 8:
            continue
        cells = row
        label_sort, label_text = cells[0]
        cand_sort, cand_text = cells[1]

        if label_sort in SUMMARY_LABELS:
            vals = [parse_number(c[0]) for c in cells[2:8]]
            summary[label_sort] = {
                "erst_count": vals[0], "erst_pct": vals[1],
                "zweit_count": vals[3], "zweit_pct": vals[4],
            }
        elif label_text and label_text in PARTY_KEY_MAP:
            vals = [parse_number(c[0]) for c in cells[2:8]]
            parties.append({
                "party": PARTY_KEY_MAP[label_text],
                "party_label": label_text,
                "candidate": cand_text or None,
                "erst_count": vals[0], "erst_pct": vals[1],
                "zweit_count": vals[3], "zweit_pct": vals[4],
            })
        elif label_text and label_text not in ("",) and cand_sort is not None:
            # A party not in our known map (independent/fringe candidate) - keep as "other".
            vals = [parse_number(c[0]) for c in cells[2:8]]
            if any(v is not None for v in vals):
                parties.append({
                    "party": "other",
                    "party_label": label_text or "Sonstige",
                    "candidate": cand_text or None,
                    "erst_count": vals[0], "erst_pct": vals[1],
                    "zweit_count": vals[3], "zweit_pct": vals[4],
                })

    eligible = summary.get("Wahlberechtigte", {}).get("erst_count")
    turnout_pct = summary.get("Wählende", {}).get("erst_pct")
    valid_zweit = summary.get("Gültige Stimmen", {}).get("zweit_count")

    # Zweitstimme plurality (party-list vote - what actually decides seats)
    zweit_ranked = sorted(
        [p for p in parties if p["zweit_pct"] is not None],
        key=lambda p: p["zweit_pct"], reverse=True,
    )
    # Erststimme plurality (direct-mandate winner - the real single-winner seat)
    erst_ranked = sorted(
        [p for p in parties if p["erst_pct"] is not None],
        key=lambda p: p["erst_pct"], reverse=True,
    )

    if not zweit_ranked or not erst_ranked:
        return None

    top_zweit = [[p["party"], round(p["zweit_pct"] / 100, 4)] for p in zweit_ranked[:5]]
    top_erst = [[p["party"], round(p["erst_pct"] / 100, 4)] for p in erst_ranked[:5]]

    voters_count = summary.get("Wählende", {}).get("erst_count")

    return {
        "gebiet_nr": gebiet_nr,
        "eligible_voters": eligible,
        "voters_count": voters_count,
        "turnout": round(turnout_pct / 100, 4) if turnout_pct is not None else None,
        "valid_votes_zweit": valid_zweit,
        "winner_erststimme": erst_ranked[0]["party"],
        "winner_erststimme_candidate": erst_ranked[0]["candidate"],
        "winner_erststimme_share": round(erst_ranked[0]["erst_pct"] / 100, 4),
        "winner_zweitstimme": zweit_ranked[0]["party"],
        "winner_zweitstimme_share": round(zweit_ranked[0]["zweit_pct"] / 100, 4),
        "top5_erststimme": top_erst,
        "top5_zweitstimme": top_zweit,
        # Full per-party absolute Zweitstimme counts (not just top5) - kept only for
        # summing into a citywide total in aggregate_citywide() below, since GERDA-style
        # municipality-level files elsewhere in this map need one number per municipality,
        # and Berlin is one municipality (AGS 11000000) - see build_state_elections_2026.py
        # docstring / map-municipality/README.md for why Wahlkreis resolution is the
        # *primary* view for Berlin, with this citywide rollup as a secondary fallback
        # so Berlin still shows up in the "All of Germany" national aggregate.
        # Several unmapped fringe candidates can all land under "other" in one Wahlkreis -
        # sum them rather than overwrite.
        "_zweit_counts_full": _sum_by_key((p["party"], p["zweit_count"]) for p in parties if p["zweit_count"]),
    }


def build_boundary():
    with open(BOUNDARY_IN, encoding="utf-8") as f:
        d = json.load(f)
    features = []
    for feat in d["geoJSON"]["features"]:
        p = feat["properties"]
        features.append({
            "type": "Feature",
            "properties": {
                "gebiet_nr": p["gebietNr"],
                "name": p["name"],
                "bezirk_nr": p["parentNr"],
            },
            "geometry": feat["geometry"],
        })
    fc = {"type": "FeatureCollection", "features": features}
    out_path = OUT_DIR / "wahlkreise.geojson"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, separators=(",", ":"))
    print(f"boundary: {len(features)} Wahlkreise -> {out_path.name} "
          f"({out_path.stat().st_size / 1024:.1f} KB)")
    return [f["properties"]["gebiet_nr"] for f in features]


def write_citywide_rollup(results):
    """Sum all 78 Wahlkreise's full per-party Zweitstimme counts (not just each one's
    own top5) into one citywide total, and write it as a normal municipality-schema
    file (data/prepared/landtag/berlin/2026.json, AGS 11000000) - the same shape
    build_municipality_data.py produces for every other state/year. Wahlkreis
    resolution (muni_format.json) stays the primary, richer view for Berlin (selected
    directly), but this citywide rollup lets Berlin 2026 merge into the "All of
    Germany" national aggregate the same way every other state does, instead of being
    silently skipped because its only other data is keyed by Wahlkreis, not AGS.
    """
    totals = {}
    eligible_sum = 0
    voters_sum = 0
    for r in results.values():
        for party, count in r["_zweit_counts_full"].items():
            totals[party] = totals.get(party, 0) + count
        eligible_sum += r["eligible_voters"] or 0
        voters_sum += r["voters_count"] or 0

    valid_sum = sum(totals.values())
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    top5 = [[p, round(c / valid_sum, 4)] for p, c in ranked[:5]]
    turnout = round(voters_sum / eligible_sum, 4) if eligible_sum else None

    record = {"w": top5[0][0], "s": top5[0][1], "b": top5, "t": turnout}
    out_dir = PREPARED_LANDTAG_DIR / "berlin"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "2026.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({BERLIN_AGS: record}, f, ensure_ascii=False, separators=(",", ":"))
    print(f"citywide rollup: {ranked[0][0]} leads with {top5[0][1]*100:.1f}% "
          f"(of {valid_sum} valid Zweitstimmen across {len(results)} Wahlkreise) "
          f"-> {out_path.relative_to(ROOT)}")


def main():
    gebiet_nrs = build_boundary()

    results = {}
    missing = []
    for nr in gebiet_nrs:
        page_path = RAW_DIR / f"{nr}.html"
        if not page_path.exists():
            missing.append(nr)
            continue
        html_text = page_path.read_text(encoding="utf-8")
        rec = parse_wahlkreis_page(html_text, nr)
        if rec is None:
            missing.append(nr)
            continue
        results[nr] = rec

    if missing:
        print(f"WARNING: {len(missing)} Wahlkreise had no parseable result: {missing}")

    out_path = OUT_DIR / "results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "election": "Abgeordnetenhauswahl Berlin 2026",
            "election_date": "2026-09-20",
            "status": "Vorläufiges Ergebnis (preliminary, as published 2026-09-21)",
            "source": "https://wahlen-berlin.de/wahlen/BE2026/Afspraes/AGH/ergebnisse.html",
            "results": results,
        }, f, ensure_ascii=False, indent=2)
    print(f"results: {len(results)}/{len(gebiet_nrs)} Wahlkreise parsed -> {out_path.name}")

    # Also emit a "muni_format.json" using the SAME compact {w,s,b,t} record schema the
    # rest of map-municipality uses (keyed by gebiet_nr instead of ags), so the frontend
    # can reuse its existing render/tooltip/legend logic almost unchanged. Primary metric
    # is Zweitstimme plurality (the party-list vote, consistent with every other dataset
    # in this map, which only ever has list-vote shares) - Erststimme (the real direct
    # mandate) is kept alongside as bonus fields since Berlin's Wahlkreise, uniquely among
    # everything else in map-municipality, have a genuine single-winner seat like the
    # federal Wahlkreis map does.
    muni_format = {}
    for nr, r in results.items():
        muni_format[nr] = {
            "w": r["winner_zweitstimme"],
            "s": r["winner_zweitstimme_share"],
            "b": r["top5_zweitstimme"],
            "t": r["turnout"],
            "erst_w": r["winner_erststimme"],
            "erst_s": r["winner_erststimme_share"],
            "erst_candidate": r["winner_erststimme_candidate"],
        }
    muni_format_path = OUT_DIR / "muni_format.json"
    with open(muni_format_path, "w", encoding="utf-8") as f:
        json.dump(muni_format, f, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {muni_format_path.name}")

    write_citywide_rollup(results)

    # Patch the main manifest.json (built by build_municipality_data.py) so the frontend
    # picks this up: add "2026" to Berlin's Landtag years, register a "special" entry, and
    # make sure any party keys unique to this election (e.g. minor Berlin-only parties
    # bucketed as "other") have a display color.
    manifest_path = ROOT / "map-municipality" / "data" / "prepared" / "manifest.json"
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    berlin_years = manifest["landtag"]["states"]["berlin"]["years"]
    if "2026" not in berlin_years:
        berlin_years.append("2026")
        berlin_years.sort()

    manifest.setdefault("special", {}).setdefault("landtag", {}).setdefault("berlin", {})["2026"] = {
        "boundary": "special/berlin_2026/wahlkreise.geojson",
        "data": "special/berlin_2026/muni_format.json",
        "key_prop": "gebiet_nr",
        "status": "Vorläufiges Ergebnis (preliminary result, published 2026-09-21 - not "
                  "yet the certified final count)",
        "source_label": "wahlen-berlin.de (Landeswahlleiterin Berlin)",
        "note": "Wahlkreis (constituency) resolution — a real direct-mandate seat, like the federal map.",
    }

    minor_party_labels = {
        "tierschutzpartei": "Tierschutzpartei", "mieterpartei": "MIETERPARTEI",
        "die_urbane": "Die Urbane.", "dkp": "DKP", "oedp": "ÖDP", "heimat": "HEIMAT",
        "sgp": "SGP", "mera25": "MERA25", "pdf": "PdF",
    }
    for p, label in minor_party_labels.items():
        manifest["party_info"].setdefault(p, {"label": label, "color": manifest["default_fallback"]["color"]})

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, separators=(",", ":"))
    print(f"patched {manifest_path.relative_to(ROOT)}: added 2026 to Berlin Landtag years + special-layer entry")

    sample_nr = next(iter(results))
    print(f"\nSample ({sample_nr}):", json.dumps(results[sample_nr], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
