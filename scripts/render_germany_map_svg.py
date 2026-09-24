"""
Render a real, static SVG choropleth of Germany's 16 states, colored by each
state's real average 2025 Bundestag winner - not an abstract illustration, an
actual map built from the same boundary and election data every tool in this
project uses. Used as the hub page's "map visualization" card illustration.

Run from the repo root:
    python scripts/render_germany_map_svg.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_BOUNDARY = ROOT / "map-trends" / "data" / "prepared" / "state_outlines.geojson"
FEDERAL_2025 = ROOT / "map-all-elections" / "data" / "prepared" / "federal" / "2025.json"
OUT_SVG = ROOT / "scripts" / "out" / "germany_map_2025.svg"

STATE_SLUG_TO_CODE = {
    "schleswig_holstein": "01", "hamburg": "02", "niedersachsen": "03", "bremen": "04",
    "north_rhine_westphalia": "05", "hesse": "06", "rhineland_palatinate": "07",
    "baden_wuerttemberg": "08", "bavaria": "09", "saarland": "10", "berlin": "11",
    "brandenburg": "12", "mecklenburg_vorpommern": "13", "saxony": "14",
    "saxony_anhalt": "15", "thuringia": "16",
}

PARTY_COLORS = {
    "cdu": "#4D4D52", "csu": "#4D4D52", "cdu_csu": "#4D4D52",
    "spd": "#E3000F", "gruene": "#46962B", "fdp": "#FFED00",
    "linke_pds": "#BE3075", "die_linke": "#BE3075", "afd": "#009EE0",
    "bsw": "#7D2E68", "other": "#6f7580",
}

VB_W, VB_H = 300, 340  # Germany is taller than wide


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    boundary = load(STATE_BOUNDARY)
    federal = load(FEDERAL_2025)

    # Average each state's municipalities' party shares (unweighted, same
    # convention as every other tool here), pick the plurality winner.
    sums = {code: {} for code in STATE_SLUG_TO_CODE.values()}
    counts = {code: 0 for code in STATE_SLUG_TO_CODE.values()}
    for ags, rec in federal.items():
        code = ags[:2]
        if code not in sums:
            continue
        counts[code] += 1
        for party, share in rec.get("b", []):
            sums[code][party] = sums[code].get(party, 0) + share

    winners = {}
    for code, party_sums in sums.items():
        if not party_sums:
            continue
        winners[code] = max(party_sums.items(), key=lambda kv: kv[1] / counts[code])[0]

    # Bounding box across all coordinates, to project lon/lat -> SVG x/y.
    min_lon, max_lon = 180.0, -180.0
    min_lat, max_lat = 90.0, -90.0

    def visit_coords(geom):
        nonlocal min_lon, max_lon, min_lat, max_lat
        gtype = geom["type"]
        coords = geom["coordinates"]
        if gtype == "Polygon":
            rings = coords
        elif gtype == "MultiPolygon":
            rings = [ring for poly in coords for ring in poly]
        else:
            return
        for ring in rings:
            for lon, lat in ring:
                min_lon = min(min_lon, lon); max_lon = max(max_lon, lon)
                min_lat = min(min_lat, lat); max_lat = max(max_lat, lat)

    for f in boundary["features"]:
        visit_coords(f["geometry"])

    lon_span = max_lon - min_lon
    lat_span = max_lat - min_lat
    pad = 4
    scale = min((VB_W - 2 * pad) / lon_span, (VB_H - 2 * pad) / lat_span)
    off_x = pad + (VB_W - 2 * pad - lon_span * scale) / 2
    off_y = pad + (VB_H - 2 * pad - lat_span * scale) / 2

    def project(lon, lat):
        x = off_x + (lon - min_lon) * scale
        y = off_y + (max_lat - lat) * scale  # flip Y: latitude up, SVG down
        return round(x, 1), round(y, 1)

    def ring_to_path(ring):
        pts = [project(lon, lat) for lon, lat in ring]
        d = f"M{pts[0][0]},{pts[0][1]} " + " ".join(f"L{x},{y}" for x, y in pts[1:]) + " Z"
        return d

    def geom_to_path(geom):
        gtype = geom["type"]
        coords = geom["coordinates"]
        if gtype == "Polygon":
            rings = coords
        else:
            rings = [ring for poly in coords for ring in poly]
        return " ".join(ring_to_path(ring) for ring in rings)

    paths = []
    for f in boundary["features"]:
        code = f["properties"]["code"]
        party = winners.get(code, "other")
        color = PARTY_COLORS.get(party, PARTY_COLORS["other"])
        d = geom_to_path(f["geometry"])
        paths.append(f'<path d="{d}" fill="{color}" stroke="#0b0d11" stroke-width="1.2" fill-rule="evenodd"/>')

    svg = (
        f'<svg viewBox="0 0 {VB_W} {VB_H}" xmlns="http://www.w3.org/2000/svg">\n'
        f'<rect x="0" y="0" width="{VB_W}" height="{VB_H}" fill="#0b0d11"/>\n'
        + "\n".join(paths) + "\n"
        "</svg>\n"
    )

    OUT_SVG.parent.mkdir(parents=True, exist_ok=True)
    OUT_SVG.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT_SVG} ({OUT_SVG.stat().st_size / 1024:.1f} KB)")
    print("state winners:", {k: winners.get(k) for k in sorted(winners)})


if __name__ == "__main__":
    main()
