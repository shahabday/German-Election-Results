"""
Build the "trends" dataset: swing between each consecutive pair of elections of the
same type (Bundestag/Europawahl/Landtag/Kommunalwahl), per municipality, derived
entirely from map-all-elections's already-prepared per-year files
(../map-all-elections/data/prepared/<type>/[<state>/]<year>.json, each a dict
ags -> {w: winner key, s: winner share, b: top-5 [party, share] pairs, t: turnout}).

This is a read-only consumer of that data - it never writes into map-all-elections/.
Its own output goes under map-trends/data/prepared/, mirroring the same
<type>/[<state>/]<year>.json layout, except each file here represents "swing arriving
at <year>, relative to the previous election of the same type/state" rather than a
snapshot, and the boundary files (gemeinden.geojson, state_outlines.geojson) are
copied in once so this app has no path dependency on map-all-elections/ at runtime.

Metric design note (the "how do you show growth of a brand-new party without
infinity" problem): the primary metric is percentage-point (pp) swing, i.e.
curr_share - prev_share, which is always finite (a new party's swing is just its
own share - 0). A relative ("times more votes") growth rate is only meaningful
above a minimum baseline; below that we don't compute a % multiplier at all - the
frontend labels it "new" using the reconstructed previous share (curr_share - swing).

Because the per-year files only keep each area's top 5 parties, a party that falls
out of the top 5 in one of the two years has its share in that year treated as 0 for
swing purposes. This under-counts small/fading parties slightly but is the same
resolution the rest of the app already works at.

Run from the repo root, after map-all-elections/build_municipality_data.py (and any
of its 2026 add-on scripts) have produced current data:
    python map-trends/build_trends_data.py
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "map-all-elections" / "data" / "prepared"
OUT = Path(__file__).resolve().parent / "data" / "prepared"

STATE_SLUG_TO_CODE = {
    "schleswig_holstein": "01", "hamburg": "02", "niedersachsen": "03", "bremen": "04",
    "north_rhine_westphalia": "05", "hesse": "06", "rhineland_palatinate": "07",
    "baden_wuerttemberg": "08", "bavaria": "09", "saarland": "10", "berlin": "11",
    "brandenburg": "12", "mecklenburg_vorpommern": "13", "saxony": "14",
    "saxony_anhalt": "15", "thuringia": "16",
}

# If, after repeating this election's swing one more time, the gap between the
# winner and the fastest-rising challenger would close to this many points or
# less, the area is flagged "at risk" of flipping next time.
RISK_PROJECTED_GAP = 0.05
MIN_SWING_TO_RECORD = 0.0005  # 0.05pp - below this, treat as unchanged (drop from output)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


# CSU only runs in Bavaria, CDU everywhere else - they're not competitors, just the
# same party family split by state. Treating them separately meant "CDU" swing/risk
# queries showed Bavaria as blank, and a CDU<->CSU handover (never happens, but the
# absence of one confused the "flipped" flag conceptually) wasn't handled sanely.
# Alias both (and any source file that already collapsed them into "cdu_csu") onto one
# key everywhere in this app's calculations.
PARTY_ALIAS = {"cdu": "cdu_csu", "csu": "cdu_csu"}


def alias_party(key):
    return PARTY_ALIAS.get(key, key)


def alias_shares(pairs):
    out = {}
    for key, value in pairs:
        k = alias_party(key)
        out[k] = out.get(k, 0.0) + value
    return out


def compute_pair(prev, curr):
    """prev, curr: ags -> {w,s,b,t}. Returns ags -> swing record (see README for schema)."""
    out = {}
    for ags, c in curr.items():
        p = prev.get(ags)
        if p is None:
            continue  # municipality didn't exist / wasn't matched in the earlier year
        prev_shares = alias_shares(p.get("b") or [])
        curr_shares = alias_shares(c.get("b") or [])
        parties = set(prev_shares) | set(curr_shares)

        sw = {}
        for party in parties:
            cs = curr_shares.get(party, 0.0)
            delta = cs - prev_shares.get(party, 0.0)
            if abs(delta) >= MIN_SWING_TO_RECORD:
                sw[party] = [round(delta, 4), round(cs, 4)]

        w0, w1 = alias_party(p.get("w")), alias_party(c.get("w"))
        flipped = w0 != w1

        ranked = sorted(curr_shares.items(), key=lambda kv: kv[1], reverse=True)
        s1 = ranked[0][1] if ranked else c.get("s", 0.0)
        margin = (ranked[0][1] - ranked[1][1]) if len(ranked) > 1 else None

        rec = {
            "w0": w0, "w1": w1, "f": 1 if flipped else 0,
            "s0": round(prev_shares.get(w0, p.get("s", 0.0)), 4),
            "s1": round(s1, 4),
        }
        if margin is not None:
            rec["m1"] = round(margin, 4)
        if sw:
            rec["sw"] = sw

        if not flipped and margin is not None:
            challengers = [(party, sw[party][0]) for party in curr_shares if party != w1 and party in sw]
            challengers.sort(key=lambda kv: kv[1], reverse=True)
            if challengers and challengers[0][1] > 0:
                ch_party, ch_swing = challengers[0]
                proj = round(margin - ch_swing, 4)
                rec["ch"] = [ch_party, round(ch_swing, 4)]
                rec["proj"] = proj
                rec["risk"] = 1 if proj <= RISK_PROJECTED_GAP else 0

        pt, ct = p.get("t"), c.get("t")
        if pt is not None and ct is not None:
            dt = round(ct - pt, 4)
            if abs(dt) >= MIN_SWING_TO_RECORD:
                rec["dt"] = dt

        out[ags] = rec
    return out


def build_national(type_key, years):
    pairs = []
    for prev_year, year in zip(years, years[1:]):
        prev = load(SRC / type_key / f"{prev_year}.json")
        curr = load(SRC / type_key / f"{year}.json")
        rec = compute_pair(prev, curr)
        dump(OUT / type_key / f"{year}.json", rec)
        pairs.append({"from": prev_year, "to": year})
        print(f"{type_key}/{year}.json  ({prev_year}->{year}, {len(rec)} areas)")
    return pairs


def build_state_scoped(type_key, states_manifest):
    states_out = {}
    for slug, info in states_manifest.items():
        years = info["years"]
        pairs = []
        for prev_year, year in zip(years, years[1:]):
            prev_path = SRC / type_key / slug / f"{prev_year}.json"
            curr_path = SRC / type_key / slug / f"{year}.json"
            if not prev_path.exists() or not curr_path.exists():
                print(f"  skip {type_key}/{slug} {prev_year}->{year}: missing source file")
                continue
            prev = load(prev_path)
            curr = load(curr_path)
            rec = compute_pair(prev, curr)
            dump(OUT / type_key / slug / f"{year}.json", rec)
            pairs.append({"from": prev_year, "to": year})
        if pairs:
            print(f"{type_key}/{slug}: {len(pairs)} pairs ({pairs[0]['from']}->{pairs[-1]['to']})")
            states_out[slug] = {"label": info["label"], "code": STATE_SLUG_TO_CODE[slug], "year_pairs": pairs}
    return states_out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = load(SRC / "manifest.json")

    print("copying boundary files...")
    shutil.copyfile(SRC / "gemeinden.geojson", OUT / "gemeinden.geojson")
    shutil.copyfile(SRC / "state_outlines.geojson", OUT / "state_outlines.geojson")

    trends_manifest = {
        "party_info": manifest["party_info"],
        "state_bounds": manifest["state_bounds"],
        "default_fallback": manifest["default_fallback"],
        "risk_projected_gap": RISK_PROJECTED_GAP,
    }

    print("\n== federal ==")
    trends_manifest["federal"] = {
        "scope": "national",
        "year_pairs": build_national("federal", manifest["federal"]["years"]),
    }

    print("\n== european ==")
    trends_manifest["european"] = {
        "scope": "national",
        "year_pairs": build_national("european", manifest["european"]["years"]),
    }

    print("\n== landtag ==")
    trends_manifest["landtag"] = {
        "scope": "state",
        "states": build_state_scoped("landtag", manifest["landtag"]["states"]),
    }

    print("\n== kommunal ==")
    trends_manifest["kommunal"] = {
        "scope": "state",
        "states": build_state_scoped("kommunal", manifest["kommunal"]["states"]),
    }

    dump(OUT / "trends_manifest.json", trends_manifest)
    print("\nwrote trends_manifest.json")


if __name__ == "__main__":
    main()
