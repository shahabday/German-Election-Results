"""
Render one real, data-driven SVG illustration per tool (9 total), replacing the
two generic shared symbols (illus-map / illus-trend) used on the hub page.
Each illustration is built from that tool's own already-built data/prepared
output - real boundaries, real 2025/2026 numbers - not a mockup.

Run from the repo root:
    python scripts/render_tool_illustrations.py

Writes scripts/out/illus_<id>.svg (one file per symbol, inner content only,
no outer <svg> wrapper) plus prints a manifest the splice step consumes.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "scripts" / "out"

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
    "bsw": "#7D2E68", "freie_wahler": "#F39200", "ssw": "#003C8F",
    "other": "#6f7580",
}

VB_W, VB_H = 300, 340
TVB_W, TVB_H = 300, 120


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------- geometry projection ----------

def bbox_of(features):
    min_lon, max_lon = 180.0, -180.0
    min_lat, max_lat = 90.0, -90.0

    def visit(geom):
        nonlocal min_lon, max_lon, min_lat, max_lat
        gtype = geom["type"]
        coords = geom["coordinates"]
        rings = coords if gtype == "Polygon" else [r for poly in coords for r in poly]
        for ring in rings:
            for lon, lat in ring:
                min_lon = min(min_lon, lon); max_lon = max(max_lon, lon)
                min_lat = min(min_lat, lat); max_lat = max(max_lat, lat)

    for f in features:
        visit(f["geometry"])
    return min_lon, max_lon, min_lat, max_lat


def projector(features, vb_w=VB_W, vb_h=VB_H, pad=4):
    min_lon, max_lon, min_lat, max_lat = bbox_of(features)
    lon_span = max_lon - min_lon
    lat_span = max_lat - min_lat
    scale = min((vb_w - 2 * pad) / lon_span, (vb_h - 2 * pad) / lat_span)
    off_x = pad + (vb_w - 2 * pad - lon_span * scale) / 2
    off_y = pad + (vb_h - 2 * pad - lat_span * scale) / 2

    def project(lon, lat):
        x = off_x + (lon - min_lon) * scale
        y = off_y + (max_lat - lat) * scale
        return round(x, 1), round(y, 1)

    return project


def _perp_dist(pt, a, b):
    (x, y), (ax, ay), (bx, by) = pt, a, b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((x - ax) ** 2 + (y - ay) ** 2) ** 0.5
    t = ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)
    px, py = ax + t * dx, ay + t * dy
    return ((x - px) ** 2 + (y - py) ** 2) ** 0.5


def simplify_ring(points, epsilon):
    """Ramer-Douglas-Peucker, for cutting card-thumbnail path size - not for
    anything that needs surveying-grade boundary accuracy."""
    if epsilon <= 0 or len(points) < 4:
        return points
    dmax, idx = 0.0, 0
    for i in range(1, len(points) - 1):
        d = _perp_dist(points[i], points[0], points[-1])
        if d > dmax:
            dmax, idx = d, i
    if dmax > epsilon:
        left = simplify_ring(points[: idx + 1], epsilon)
        right = simplify_ring(points[idx:], epsilon)
        return left[:-1] + right
    return [points[0], points[-1]]


def geom_to_path(geom, project, epsilon_deg=0.0):
    gtype = geom["type"]
    coords = geom["coordinates"]
    rings = coords if gtype == "Polygon" else [r for poly in coords for r in poly]
    parts = []
    for ring in rings:
        pts = simplify_ring(ring, epsilon_deg) if epsilon_deg else ring
        if len(pts) < 4:
            continue
        proj_pts = [project(lon, lat) for lon, lat in pts]
        d = f"M{proj_pts[0][0]},{proj_pts[0][1]} " + " ".join(f"L{x},{y}" for x, y in proj_pts[1:]) + " Z"
        parts.append(d)
    return " ".join(parts)


def render_polygon_map(features, color_fn, stroke="#0b0d11", stroke_width=1.2,
                        opacity_fn=None, vb_w=VB_W, vb_h=VB_H, pad=4, key_fn=None,
                        epsilon_deg=0.0):
    project = projector(features, vb_w, vb_h, pad)
    paths = [f'<rect x="0" y="0" width="{vb_w}" height="{vb_h}" fill="#0b0d11"/>']
    for f in features:
        key = key_fn(f) if key_fn else f["properties"].get("code")
        color = color_fn(key, f)
        op = opacity_fn(key, f) if opacity_fn else 1.0
        d = geom_to_path(f["geometry"], project, epsilon_deg)
        if not d:
            continue
        paths.append(
            f'<path d="{d}" fill="{color}" fill-opacity="{op}" '
            f'stroke="{stroke}" stroke-width="{stroke_width}" fill-rule="evenodd"/>'
        )
    return "\n".join(paths)


# ---------- state-level aggregation helpers ----------

def state_avgs_from_share_lists(records, list_key="b"):
    sums = {code: {} for code in STATE_SLUG_TO_CODE.values()}
    counts = {code: 0 for code in STATE_SLUG_TO_CODE.values()}
    for ags, rec in records.items():
        code = ags[:2]
        if code not in sums:
            continue
        counts[code] += 1
        for party, share in rec.get(list_key, []):
            sums[code][party] = sums[code].get(party, 0) + share
    return {
        code: {p: v / counts[code] for p, v in sums[code].items()}
        for code in sums if counts[code] > 0
    }


def state_avgs_from_swing(records):
    sums = {code: {} for code in STATE_SLUG_TO_CODE.values()}
    counts = {code: 0 for code in STATE_SLUG_TO_CODE.values()}
    for ags, rec in records.items():
        code = ags[:2]
        if code not in sums:
            continue
        counts[code] += 1
        for party, pair in rec.get("sw", {}).items():
            delta = pair[0]
            sums[code][party] = sums[code].get(party, 0) + delta
    return {
        code: {p: v / counts[code] for p, v in sums[code].items()}
        for code in sums if counts[code] > 0
    }


def winner_of(avg_dict):
    if not avg_dict:
        return "other"
    return max(avg_dict.items(), key=lambda kv: kv[1])[0]


# ---------- line chart helper ----------

def render_line_chart(series, x_labels_count, y_min, y_max, vb_w=TVB_W, vb_h=TVB_H):
    pad_l, pad_r, pad_t, pad_b = 10, 10, 12, 14
    plot_w = vb_w - pad_l - pad_r
    plot_h = vb_h - pad_t - pad_b

    def xy(x_idx, value):
        x = pad_l + (x_idx / (x_labels_count - 1)) * plot_w if x_labels_count > 1 else pad_l
        frac = (value - y_min) / (y_max - y_min) if y_max > y_min else 0.5
        y = pad_t + (1 - frac) * plot_h
        return round(x, 1), round(y, 1)

    parts = [f'<rect x="0" y="0" width="{vb_w}" height="{vb_h}" fill="#0b0d11"/>']
    # baseline
    base_y = pad_t + plot_h
    parts.append(f'<line x1="{pad_l}" y1="{base_y}" x2="{vb_w - pad_r}" y2="{base_y}" stroke="#2a2e38" stroke-width="1"/>')

    for s in series:
        pts = [xy(i, v) for i, v in enumerate(s["values"])]
        d = "M" + " L".join(f"{x},{y}" for x, y in pts)
        parts.append(f'<path d="{d}" fill="none" stroke="{s["color"]}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>')
        for i, (x, y) in enumerate(pts):
            if s.get("dots") and not s["dots"][i]:
                continue
            r = 2.6 if s.get("dots") else 1.8
            parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{s["color"]}"/>')
    return "\n".join(parts)


def write_symbol(name, view_box, inner):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"illus_{name}.svg"
    path.write_text(f'<symbol id="illus-{name}" viewBox="{view_box}">\n{inner}\n</symbol>\n', encoding="utf-8")
    print(f"  wrote illus-{name} ({path.stat().st_size / 1024:.1f} KB)")


# =====================================================================
# 1. map/  -> Wahlkreis-level 2025 federal results (finest resolution)
# =====================================================================

def build_map_wkr():
    d = load(ROOT / "map" / "data" / "prepared" / "wkr_2025.geojson")
    features = d["features"]

    def color_fn(key, f):
        party = f["properties"].get("zweitstimme_top_party", "other")
        return PARTY_COLORS.get(party, PARTY_COLORS["other"])

    inner = render_polygon_map(features, color_fn, stroke="#0b0d11", stroke_width=0.35, key_fn=lambda f: None, epsilon_deg=0.03)
    write_symbol("map-wkr", f"0 0 {VB_W} {VB_H}", inner)


# =====================================================================
# 2. map-all-elections/ -> Bavaria at full municipality resolution
#    (zoomed-in detail shot to show the fine-grained ~10,900-area data)
# =====================================================================

def build_map_muni():
    gem = load(ROOT / "map-all-elections" / "data" / "prepared" / "gemeinden.geojson")
    federal = load(ROOT / "map-all-elections" / "data" / "prepared" / "federal" / "2025.json")
    # Landkreis Muenchen (32 municipalities) - a close-up detail shot that shows
    # the tool's fine-grained resolution without embedding all ~10,900 areas.
    subset = [f for f in gem["features"] if f["properties"]["ags"].startswith("09184")]

    def color_fn(key, f):
        ags = f["properties"]["ags"]
        rec = federal.get(ags)
        party = rec["w"] if rec else "other"
        return PARTY_COLORS.get(party, PARTY_COLORS["other"])

    inner = render_polygon_map(subset, color_fn, stroke="#0b0d11", stroke_width=0.4, key_fn=lambda f: None, epsilon_deg=0.001)
    write_symbol("map-muni", f"0 0 {VB_W} {VB_H}", inner)


# =====================================================================
# 3. map-trends/ -> state-level swing map: 2021->2025 biggest-gain party
# =====================================================================

def build_map_swing():
    boundary = load(ROOT / "map-trends" / "data" / "prepared" / "state_outlines.geojson")
    federal = load(ROOT / "map-trends" / "data" / "prepared" / "federal" / "2025.json")
    avgs = state_avgs_from_swing(federal)
    winners = {code: winner_of(a) for code, a in avgs.items()}

    def color_fn(code, f):
        return PARTY_COLORS.get(winners.get(code, "other"), PARTY_COLORS["other"])

    def opacity_fn(code, f):
        return 0.62

    inner = render_polygon_map(
        boundary["features"], color_fn, stroke="#0b0d11", stroke_width=1.2,
        opacity_fn=opacity_fn, key_fn=lambda f: f["properties"]["code"],
    )
    write_symbol("map-swing", f"0 0 {VB_W} {VB_H}", inner)


# =====================================================================
# 4. map-current-standing/ -> state-level "current picture" (2026 composite)
# =====================================================================

def build_map_standing():
    boundary_geo = load(ROOT / "map-trends" / "data" / "prepared" / "state_outlines.geojson")
    composite = load(ROOT / "map-current-standing" / "data" / "prepared" / "2026.json")
    avgs = state_avgs_from_share_lists(composite, list_key="b")
    winners = {code: winner_of(a) for code, a in avgs.items()}

    def color_fn(code, f):
        return PARTY_COLORS.get(winners.get(code, "other"), PARTY_COLORS["other"])

    inner = render_polygon_map(
        boundary_geo["features"], color_fn, stroke="#0b0d11", stroke_width=1.2,
        key_fn=lambda f: f["properties"]["code"],
    )
    write_symbol("map-standing", f"0 0 {VB_W} {VB_H}", inner)


# =====================================================================
# 5. map-demographics/ -> county-level average gross wage (2019), non-party scale
# =====================================================================

def lerp_color(t, c_lo=(44, 91, 138), c_hi=(224, 168, 62)):
    t = max(0.0, min(1.0, t))
    r = round(c_lo[0] + (c_hi[0] - c_lo[0]) * t)
    g = round(c_lo[1] + (c_hi[1] - c_lo[1]) * t)
    b = round(c_lo[2] + (c_hi[2] - c_lo[2]) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def build_map_demo():
    boundary = load(ROOT / "map-demographics" / "data" / "prepared" / "counties.geojson")
    county_data = load(ROOT / "map-demographics" / "data" / "prepared" / "county" / "2019.json")
    values = {f["properties"]["county"]: county_data.get(f["properties"]["county"], {}).get("gross_wage")
              for f in boundary["features"]}
    present = [v for v in values.values() if v is not None]
    v_min, v_max = min(present), max(present)

    def color_fn(key, f):
        v = values.get(f["properties"]["county"])
        if v is None:
            return PARTY_COLORS["other"]
        t = (v - v_min) / (v_max - v_min) if v_max > v_min else 0.5
        return lerp_color(t)

    inner = render_polygon_map(boundary["features"], color_fn, stroke="#0b0d11", stroke_width=0.3, key_fn=lambda f: None, epsilon_deg=0.02)
    write_symbol("map-demo", f"0 0 {VB_W} {VB_H}", inner)


# =====================================================================
# 6. map-election-profile/ -> state blend: federal 2025 vs latest Landtag
#    "consistency" view - dim fill where the two disagree
# =====================================================================

def build_map_profile():
    boundary = load(ROOT / "map-trends" / "data" / "prepared" / "state_outlines.geojson")
    federal = load(ROOT / "map-election-profile" / "data" / "prepared" / "federal" / "2025.json")
    fed_avgs = state_avgs_from_share_lists(federal)
    fed_winners = {code: winner_of(a) for code, a in fed_avgs.items()}

    landtag_dir = ROOT / "map-election-profile" / "data" / "prepared" / "landtag"
    landtag_winners = {}
    for slug, code in STATE_SLUG_TO_CODE.items():
        state_dir = landtag_dir / slug
        if not state_dir.exists():
            continue
        years = sorted(int(p.stem) for p in state_dir.glob("*.json"))
        if not years:
            continue
        latest = load(state_dir / f"{years[-1]}.json")
        avgs = state_avgs_from_share_lists(latest)
        combined = {}
        for c, a in avgs.items():
            combined = a
            break
        landtag_winners[code] = winner_of(combined) if combined else None

    def color_fn(code, f):
        return PARTY_COLORS.get(fed_winners.get(code, "other"), PARTY_COLORS["other"])

    def opacity_fn(code, f):
        return 1.0 if landtag_winners.get(code) == fed_winners.get(code) else 0.4

    inner = render_polygon_map(
        boundary["features"], color_fn, stroke="#0b0d11", stroke_width=1.2,
        opacity_fn=opacity_fn, key_fn=lambda f: f["properties"]["code"],
    )
    write_symbol("map-profile", f"0 0 {VB_W} {VB_H}", inner)


# =====================================================================
# 7. map-election-timeseries/ -> nationwide AfD vs CDU/CSU share, federal 1994-2025
# =====================================================================

def build_trend_timeseries():
    fed_dir = ROOT / "map-election-timeseries" / "data" / "prepared" / "federal"
    years = sorted(int(p.stem) for p in fed_dir.glob("*.json"))
    afd_vals, union_vals = [], []
    for y in years:
        recs = load(fed_dir / f"{y}.json")
        sums = {}
        n = 0
        for ags, rec in recs.items():
            n += 1
            for party, share in rec.get("b", []):
                sums[party] = sums.get(party, 0) + share
        afd_vals.append(sums.get("afd", 0) / n if n else 0)
        union_vals.append((sums.get("cdu_csu", 0) + sums.get("cdu", 0) + sums.get("csu", 0)) / n if n else 0)

    all_vals = afd_vals + union_vals
    y_min, y_max = 0, max(all_vals) * 1.15
    series = [
        {"label": "CDU/CSU", "color": PARTY_COLORS["cdu_csu"], "values": union_vals},
        {"label": "AfD", "color": PARTY_COLORS["afd"], "values": afd_vals},
    ]
    inner = render_line_chart(series, len(years), y_min, y_max)
    write_symbol("trend-timeseries", f"0 0 {TVB_W} {TVB_H}", inner)


# =====================================================================
# 8. map-current-standing-trends/ -> step-shaped AfD line, Saxony-Anhalt,
#    dots only at years the composite actually refreshed for that state
# =====================================================================

def build_trend_standing():
    prep = ROOT / "map-current-standing-trends" / "data" / "prepared"
    years = sorted(int(p.stem) for p in prep.glob("[12][0-9][0-9][0-9].json"))
    vals, dots = [], []
    for y in years:
        recs = load(prep / f"{y}.json")
        sums, n, fresh_count = 0, 0, 0
        for ags, rec in recs.items():
            if not ags.startswith("15"):
                continue
            n += 1
            for party, share in rec.get("b", []):
                if party == "afd":
                    sums += share
            if rec.get("y") == str(y):
                fresh_count += 1
        vals.append(sums / n if n else 0)
        dots.append(fresh_count > n / 2 if n else False)

    y_min, y_max = 0, max(vals) * 1.15 if vals else 1
    series = [{"label": "AfD - Saxony-Anhalt", "color": PARTY_COLORS["afd"], "values": vals, "dots": dots}]
    inner = render_line_chart(series, len(years), y_min, y_max)
    write_symbol("trend-standing", f"0 0 {TVB_W} {TVB_H}", inner)


# =====================================================================
# 9. map-timeseries/ -> nationwide avg gross wage over time (smooth, non-election)
# =====================================================================

def build_trend_demo():
    state_dir = ROOT / "map-timeseries" / "data" / "prepared" / "state"
    years = sorted(int(p.stem) for p in state_dir.glob("*.json"))
    vals = []
    for y in years:
        recs = load(state_dir / f"{y}.json")
        wages = [r["gross_wage"] for r in recs.values() if r.get("gross_wage") is not None]
        vals.append(sum(wages) / len(wages) if wages else 0)

    y_min, y_max = min(vals) * 0.95, max(vals) * 1.05
    series = [{"label": "Avg. gross wage", "color": "#4a90e2", "values": vals}]
    inner = render_line_chart(series, len(years), y_min, y_max)
    write_symbol("trend-demo", f"0 0 {TVB_W} {TVB_H}", inner)


def main():
    print("map/ -> illus-map-wkr")
    build_map_wkr()
    print("map-all-elections/ -> illus-map-muni")
    build_map_muni()
    print("map-trends/ -> illus-map-swing")
    build_map_swing()
    print("map-current-standing/ -> illus-map-standing")
    build_map_standing()
    print("map-demographics/ -> illus-map-demo")
    build_map_demo()
    print("map-election-profile/ -> illus-map-profile")
    build_map_profile()
    print("map-election-timeseries/ -> illus-trend-timeseries")
    build_trend_timeseries()
    print("map-current-standing-trends/ -> illus-trend-standing")
    build_trend_standing()
    print("map-timeseries/ -> illus-trend-demo")
    build_trend_demo()


if __name__ == "__main__":
    main()
