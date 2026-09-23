import json
import sys
sys.path.insert(0, "scripts")
from build_state_story import build_story

YEARS = list(range(1990, 2027))
ELECTION_YEARS = [1990,1994,1998,2002,2005,2009,2013,2017,2021,2025]
ALL_PARTIES = ['cdu','afd','spd','linke_pds','gruene']
MERGE = {
    'cdu': {'cdu','csu','cdu_csu'},
    'linke_pds': {'linke_pds','die_linke'},
    'afd': {'afd'},
    'spd': {'spd'},
    'gruene': {'gruene'},
}
STATE_NAMES = {
 '01':'schleswig_holstein','02':'hamburg','03':'niedersachsen','04':'bremen','05':'nrw',
 '06':'hessen','07':'rheinland_pfalz','08':'baden_wuerttemberg','09':'bayern','10':'saarland',
 '11':'berlin','12':'brandenburg','13':'mv','14':'sachsen','15':'sachsen_anhalt','16':'thueringen'
}

yearfiles = {y: json.load(open(f'map-current-standing-trends/data/prepared/{y}.json', encoding='utf-8')) for y in YEARS}

states = {code: {p: [] for p in ALL_PARTIES} for code in STATE_NAMES}
for y in YEARS:
    d = yearfiles[y]
    sums = {code: {p: 0.0 for p in ALL_PARTIES} for code in STATE_NAMES}
    n = {code: 0 for code in STATE_NAMES}
    for k, v in d.items():
        code = k[:2]
        if code not in STATE_NAMES: continue
        n[code] += 1
        bmap = {}
        for p, s in v.get('b', []):
            bmap[p] = bmap.get(p, 0.0) + s
        for p in ALL_PARTIES:
            sums[code][p] += sum(bmap.get(alt, 0.0) for alt in MERGE[p])
    for code in STATE_NAMES:
        for p in ALL_PARTIES:
            states[code][p].append(round((sums[code][p]/n[code])*100, 2) if n[code] else 0)

named = {STATE_NAMES[c]: states[c] for c in STATE_NAMES}

# Berlin is tracked as a single citywide AGS record (n=1), so any party that misses the
# top-5 for one election is a hard 0, not a soft averaging bias. AfD's real 2021 federal
# result was 10.3% (6th place, just behind FDP) -- patch that one known gap.
i2021 = YEARS.index(2021)
i2022 = YEARS.index(2022)
named['berlin']['afd'][i2021] = 10.3
named['berlin']['afd'][i2022] = 10.3

GROUPS = {
    'east_combined': ['15','16','13','12','11'],
    'west_combined': ['08','05','01','10'],
    'poor_combined': ['13','12','14','15','03'],
    'superrich_combined': ['06','08'],
    'rich_combined': ['05','09'],
}
def combine(codes):
    out = {p: [] for p in ALL_PARTIES}
    for i in range(len(YEARS)):
        for p in ALL_PARTIES:
            vals = [states[c][p][i] for c in codes]
            out[p].append(round(sum(vals)/len(vals), 2))
    return out
combined = {g: combine(codes) for g, codes in GROUPS.items()}

def pick(series, parties):
    return {p: series[p] for p in parties}

# ---------------------------------------------------------------------------
# Economic data: household income per capita, indexed to % of national average,
# from map-demographics' real county-level series (2001-2019, some states shorter).
# ---------------------------------------------------------------------------
YEARS_ECON = list(range(2001, 2020))
econ_yearfiles = {y: json.load(open(f'map-demographics/data/prepared/county/{y}.json', encoding='utf-8')) for y in YEARS_ECON}

state_hh = {code: {} for code in STATE_NAMES}
national_hh = {}
for y in YEARS_ECON:
    d = econ_yearfiles[y]
    sums = {code: 0.0 for code in STATE_NAMES}
    counts = {code: 0 for code in STATE_NAMES}
    nat_sum, nat_n = 0.0, 0
    for k, v in d.items():
        if 'hh_income' not in v: continue
        code = k[:2]
        if code not in STATE_NAMES: continue
        sums[code] += v['hh_income']; counts[code] += 1
        nat_sum += v['hh_income']; nat_n += 1
    for code in STATE_NAMES:
        if counts[code]:
            state_hh[code][y] = sums[code] / counts[code]
    if nat_n:
        national_hh[y] = nat_sum / nat_n

income_pct = {code: {} for code in STATE_NAMES}
for code in STATE_NAMES:
    for y, v in state_hh[code].items():
        income_pct[code][y] = round(v / national_hh[y] * 100, 1)

named_income_pct = {STATE_NAMES[c]: income_pct[c] for c in STATE_NAMES}

def econ_series(name, y_min, y_max):
    pct = named_income_pct[name]
    years = sorted(pct.keys())
    return {"years": years, "values": [pct[y] for y in years], "min": y_min, "max": y_max,
            "label": "Household income, % of national average"}

def econ_series_combined(codes, y_min, y_max):
    years = sorted(set.intersection(*[set(income_pct[c].keys()) for c in codes]))
    values = [round(sum(income_pct[c][y] for c in codes) / len(codes), 1) for y in years]
    return {"years": years, "values": values, "min": y_min, "max": y_max,
            "label": "Household income, % of national average"}

STORY_ROOT = "story/"

# ---------------------------------------------------------------------------
# 1. Sachsen-Anhalt
# ---------------------------------------------------------------------------
build_story({
    "title": "Sachsen-Anhalt: No Party Holds On For Long",
    "chart_title": "Sachsen-Anhalt",
    "chart_subtitle": "Current standing composite (federal + state + European), unweighted municipality average · 1990–2026",
    "hero_body": "Four parties, thirty-six years — and unlike its neighbor Sachsen, no single party has ever really held Sachsen-Anhalt for long. This is the state that tried an SPD–PDS coalition before anyone else, and later handed the AfD its first big win.",
    "years": YEARS, "election_years": ELECTION_YEARS, "y_max": 60,
    "party_order": ["cdu","spd","linke_pds","afd"],
    "data": pick(named["sachsen_anhalt"], ["cdu","spd","linke_pds","afd"]),
    "econ": econ_series("sachsen_anhalt", 78, 91),
    "steps": [
        {"eyebrow": "Sachsen-Anhalt since 1990", "headline": "No party held on here",
         "lines": {"cdu":1,"spd":0,"linke_pds":0,"afd":0},
         "body": "The CDU led the first Bundestag elections here, same as everywhere else in the East. But by 1998 it had fallen to <strong>28.9%</strong> — third place, not first. Sachsen-Anhalt never settled into a one-party pattern the way Sachsen did."},
        {"eyebrow": "The Magdeburg Model", "headline": "SPD actually governed here",
         "lines": {"cdu":1,"spd":1,"linke_pds":0,"afd":0},
         "body": "Add SPD and 1998–2002 stands out: <strong>38.5%</strong>, then <strong>42.7%</strong> — the strongest SPD federal result of any state in this series. From 1994 to 2002, Sachsen-Anhalt was governed by an SPD state government tolerated in parliament by the PDS, the so-called 'Magdeburg Model' — a coalition shape no other state tried."},
        {"eyebrow": "Die Linke's high-water mark", "headline": "Die Linke's best state, by far",
         "lines": {"cdu":1,"spd":0.3,"linke_pds":1,"afd":0},
         "body": "Add Die Linke (and predecessor PDS) and its 2009 peak stands out: <strong>32.1%</strong> — the highest Die Linke result of any state measured so far. Even after the SPD-PDS coalition ended in 2002, Die Linke kept growing here on its own for another seven years."},
        {"eyebrow": "2016: the first real shock", "headline": "AfD's first big state win",
         "lines": {"cdu":1,"spd":0.3,"linke_pds":0.3,"afd":1},
         "markers": [{"year": 2016, "label": "AfD 24.2% (state election)"}],
         "body": "In the March 2016 state election, AfD took <strong>24.2%</strong> here — at the time, the strongest AfD result anywhere in Germany, and the first sign the party could win at governing scale, not just protest-vote scale."},
        {"eyebrow": "Where it stands now", "headline": "The highest AfD share measured yet",
         "lines": {"cdu":0.3,"spd":0.3,"linke_pds":0.3,"afd":1},
         "markers": [{"year": 2026, "label": "AfD 43.8% official, 2026 state election"}],
         "body": "By the 2025 federal election AfD reached <strong>41.7%</strong> here. In the September 2026 state election it went further still: <strong>43.8%</strong> officially — the highest vote share any party has won in Sachsen-Anhalt since reunification, with CDU falling to a historic low of 17.2%."},
        {"eyebrow": "The economic picture", "headline": "Income converged. The swing didn't slow.",
         "lines": {"cdu":0.15,"spd":0.15,"linke_pds":0.15,"afd":0.15}, "econ": True,
         "body": "Sachsen-Anhalt's average household income actually closed ground on the national average — from <strong>81%</strong> in 2007 to <strong>88%</strong> by 2019 — while GDP per capita nearly doubled, from €16,400 to €28,900. Public debt per capita barely moved (€12,200 to €12,500) and stayed the highest of any state in this series. None of that slowed the AfD, whose vote share kept climbing through the same years."},

        {"eyebrow": "One state, no lasting winner", "headline": "The opposition kept changing hands",
         "lines": {"cdu":1,"spd":1,"linke_pds":1,"afd":1},
         "body": "CDU, then SPD, then Die Linke, now AfD — Sachsen-Anhalt has cycled through more leading challengers than any other state in this series. Every value here is the same 'current standing' composite (federal, state and European results, unweighted municipality average) used across this site.",
         "cta": [("Open the current standing tool", "../map-current-standing-trends/"), ("Open the swing map", "../map-trends/")]},
    ],
    "methodology_html": '''    <p>This chart uses the same <strong>current standing</strong> composite as the Current Standing tool: each of Sachsen-Anhalt's 218 municipalities is shown at its own most recently held election — federal, state, or European — not one single nationwide vote. As with every tool on this site, values are an <strong>unweighted average across municipalities</strong>, which tends to overstate the AfD's most rural strongholds. The 2026 state-election figure quoted in the text (43.8%) is the official result; this chart's own composite reads a few points higher for the same reason.</p>''',
}, STORY_ROOT + "sachsen-anhalt.html")

# ---------------------------------------------------------------------------
# 2. Thueringen
# ---------------------------------------------------------------------------
build_story({
    "title": "Thüringen: Where the AfD Won First",
    "chart_title": "Thüringen",
    "chart_subtitle": "Current standing composite (federal + state + European), unweighted municipality average · 1990–2026",
    "hero_body": "Four parties, thirty-six years — the state that gave Germany its first Die Linke state premier in 2014, and ten years later, its first outright AfD win in a state election.",
    "years": YEARS, "election_years": ELECTION_YEARS, "y_max": 60,
    "party_order": ["cdu","spd","linke_pds","afd"],
    "data": pick(named["thueringen"], ["cdu","spd","linke_pds","afd"]),
    "econ": econ_series("thueringen", 78, 92),
    "steps": [
        {"eyebrow": "Thüringen since 1990", "headline": "CDU's long lead, then a slow fade",
         "lines": {"cdu":1,"spd":0,"linke_pds":0,"afd":0},
         "body": "CDU held the top spot in every federal election from 1990 through 2013, though not always comfortably — it fell to <strong>32.8%</strong> in 1998 before recovering to <strong>42.8%</strong> in 2013."},
        {"eyebrow": "The traditional No. 2", "headline": "SPD, strongest in the 1990s",
         "lines": {"cdu":1,"spd":1,"linke_pds":0,"afd":0},
         "body": "SPD peaked at <strong>37.7%</strong> in 2002 — briefly within 4 points of the CDU — before fading through the 2000s, the same pattern seen in most East German states."},
        {"eyebrow": "Ramelow's Die Linke", "headline": "Germany's first Linke state premier",
         "lines": {"cdu":1,"spd":0.3,"linke_pds":1,"afd":0},
         "markers": [{"year": 2014, "label": "Bodo Ramelow (Linke) becomes premier"}],
         "body": "Die Linke's Thüringen support tracked the CDU's dips closely for two decades, peaking at <strong>26.5%</strong> in 2009. In 2014, Bodo Ramelow became Germany's first-ever Die Linke state premier — and governed Thüringen for a decade."},
        {"eyebrow": "2013: a new opposition", "headline": "The Höcke era begins",
         "lines": {"cdu":1,"spd":0.3,"linke_pds":0.3,"afd":1},
         "markers": [{"year": 2013, "label": "AfD founded"}, {"year": 2017, "label": "AfD 23.7%"}],
         "body": "AfD enters in 2013 at <strong>6.0%</strong>, then <strong>23.7%</strong> by 2017. Under state leader Björn Höcke, Thüringen's AfD became the party's most radical branch nationally — and its fastest-growing."},
        {"eyebrow": "2024: the first outright win", "headline": "The first state election an AfD has won",
         "lines": {"cdu":0.3,"spd":0.3,"linke_pds":0.3,"afd":1},
         "markers": [{"year": 2024, "label": "AfD 32.8% (state election)"}],
         "body": "In the September 2024 state election, AfD won <strong>32.8%</strong> — the first time any AfD branch has come first in a German state election. By the 2025 federal election, its share reached <strong>42.0%</strong> here."},
        {"eyebrow": "The economic picture", "headline": "Income converged, debt fell — AfD still grew fastest",
         "lines": {"cdu":0.15,"spd":0.15,"linke_pds":0.15,"afd":0.15}, "econ": True,
         "body": "Thüringen's income share rose from <strong>82%</strong> to <strong>89%</strong> of the national average between 2001 and 2019, GDP per capita nearly doubled (€16,800 to €29,300), and public debt per capita actually <em>fell</em> (€10,000 to €9,300) — a genuine improvement on every measure. Over the same years, Thüringen's AfD had the fastest rise of any state in this series, ending with the first outright AfD state-election win in Germany."},

        {"eyebrow": "One state, two firsts", "headline": "First a Linke premier, then an AfD win",
         "lines": {"cdu":1,"spd":1,"linke_pds":1,"afd":1},
         "body": "No other state in this series has swung this far in one direction and then this far in the opposite one. Every value here is the same 'current standing' composite (federal, state and European results, unweighted municipality average) used across this site.",
         "cta": [("Open the current standing tool", "../map-current-standing-trends/"), ("Open the swing map", "../map-trends/")]},
    ],
    "methodology_html": '''    <p>This chart uses the same <strong>current standing</strong> composite as the Current Standing tool: each of Thüringen's ~605–633 municipalities is shown at its own most recently held election — federal, state, or European — not one single nationwide vote. As with every tool on this site, values are an <strong>unweighted average across municipalities</strong>, which tends to overstate the AfD's most rural strongholds relative to the official, population-weighted result.</p>''',
}, STORY_ROOT + "thueringen.html")

# ---------------------------------------------------------------------------
# 3. Brandenburg
# ---------------------------------------------------------------------------
build_story({
    "title": "Brandenburg: The East German State CDU Never Won",
    "chart_title": "Brandenburg",
    "chart_subtitle": "Current standing composite (federal + state + European), unweighted municipality average · 1990–2026",
    "hero_body": "Four parties, thirty-six years — the one East German state where the CDU was never the dominant party. Here, it was always SPD's to lose, right up to a photo-finish in 2024.",
    "years": YEARS, "election_years": ELECTION_YEARS, "y_max": 60,
    "party_order": ["spd","cdu","linke_pds","afd"],
    "data": pick(named["brandenburg"], ["spd","cdu","linke_pds","afd"]),
    "econ": econ_series("brandenburg", 80, 94),
    "steps": [
        {"eyebrow": "Brandenburg since 1994", "headline": "SPD's state from the start",
         "lines": {"spd":1,"cdu":0,"linke_pds":0,"afd":0},
         "body": "CDU narrowly led in 1990, but from 1994 on SPD took over and never let go in a federal election for three decades — peaking at <strong>45.4%</strong> in 2002. Manfred Stolpe, Matthias Platzeck and Dietmar Woidke kept SPD in the premier's office continuously since reunification."},
        {"eyebrow": "The other big party", "headline": "CDU, a distant second",
         "lines": {"spd":1,"cdu":1,"linke_pds":0,"afd":0},
         "body": "Add CDU and the gap is stark: it never topped <strong>37.3%</strong> here, and by 2021 had fallen to just <strong>16.0%</strong> — a state where the traditional 'big two' were never evenly matched."},
        {"eyebrow": "The real opposition", "headline": "Die Linke, not CDU, pushed SPD hardest",
         "lines": {"spd":1,"cdu":0.3,"linke_pds":1,"afd":0},
         "body": "Add Die Linke (and predecessor PDS) and it's clear this was SPD's actual rival for two decades, peaking at <strong>27.7%</strong> in 2009 — a stronger showing here than CDU ever managed."},
        {"eyebrow": "2013: a new opposition", "headline": "AfD arrives, and grows fast",
         "lines": {"spd":0.3,"cdu":0.3,"linke_pds":0.3,"afd":1},
         "markers": [{"year": 2013, "label": "AfD founded"}, {"year": 2017, "label": "AfD 22.2%"}],
         "body": "AfD enters in 2013 at <strong>5.4%</strong>, then <strong>22.2%</strong> by 2017 — already ahead of Die Linke. By 2025 it reached <strong>38.4%</strong>, this time challenging SPD directly rather than CDU."},
        {"eyebrow": "2024: SPD's narrow save", "headline": "The closest result in this series",
         "lines": {"spd":1,"cdu":0.3,"linke_pds":0.3,"afd":1},
         "markers": [{"year": 2024, "label": "SPD 30.9% narrowly beats AfD 29.2%"}],
         "body": "In the September 2024 state election, Dietmar Woidke's SPD held on with <strong>30.9%</strong> against AfD's <strong>29.2%</strong> — the narrowest AfD-vs-incumbent margin of any East German state election that year, and the only one an established party still won outright."},
        {"eyebrow": "The economic picture", "headline": "A state that got richer, and closer to an AfD win",
         "lines": {"spd":0.15,"cdu":0.15,"linke_pds":0.15,"afd":0.15}, "econ": True,
         "body": "Brandenburg's income share climbed from <strong>83%</strong> to <strong>91%</strong> of the national average, GDP per capita rose from €18,000 to €30,800, and debt per capita fell from €11,500 to €10,300 — one of the clearest economic improvements of any state in this series. It didn't stop AfD from coming within 1.7 points of winning the 2024 state election outright."},

        {"eyebrow": "One state, one incumbent", "headline": "Still SPD's, for now",
         "lines": {"spd":1,"cdu":1,"linke_pds":1,"afd":1},
         "body": "Brandenburg is the outlier in this series: the East German state where CDU was never the story, and where AfD's rise has been a threat to SPD, not to CDU. Every value here is the same 'current standing' composite used across this site.",
         "cta": [("Open the current standing tool", "../map-current-standing-trends/"), ("Open the swing map", "../map-trends/")]},
    ],
    "methodology_html": '''    <p>This chart uses the same <strong>current standing</strong> composite as the Current Standing tool: each of Brandenburg's ~413–416 municipalities is shown at its own most recently held election — federal, state, or European — not one single nationwide vote. As with every tool on this site, values are an <strong>unweighted average across municipalities</strong>, which tends to overstate the AfD's most rural strongholds relative to the official, population-weighted result.</p>''',
}, STORY_ROOT + "brandenburg.html")

# ---------------------------------------------------------------------------
# 4. Berlin
# ---------------------------------------------------------------------------
build_story({
    "title": "Berlin: Four Parties, Real Competition",
    "chart_title": "Berlin",
    "chart_subtitle": "Current standing composite (federal + state + European); Berlin is tracked as a single citywide result, not an average · 1990–2026",
    "hero_body": "Unlike every other state in this series, Berlin doesn't reduce to a two-party or opposition-flip story. Four parties have taken real turns as the city's leading force — and the AfD, unusually, isn't one of them.",
    "years": YEARS, "election_years": ELECTION_YEARS, "y_max": 45,
    "party_order": ["spd","cdu","linke_pds","gruene","afd"],
    "data": pick(named["berlin"], ["spd","cdu","linke_pds","gruene","afd"]),
    "econ": econ_series("berlin", 87, 97),
    "steps": [
        {"eyebrow": "Berlin since 1990", "headline": "The one place SPD never really lost",
         "lines": {"spd":1,"cdu":0,"linke_pds":0,"gruene":0,"afd":0},
         "body": "SPD has led or come close in almost every federal election since reunification, from <strong>30.6%</strong> in 1990 to a 2021 result of <strong>23.4%</strong> that still put it first, narrowly, over the Greens."},
        {"eyebrow": "The traditional rival", "headline": "CDU, strong once, fading since",
         "lines": {"spd":1,"cdu":1,"linke_pds":0,"gruene":0,"afd":0},
         "body": "CDU actually led Berlin in 1990 (<strong>39.4%</strong>), reunification's immediate aftermath. It never got that high again, falling to <strong>15.9%</strong> by 2021 — a collapse steeper than almost any other state in this series."},
        {"eyebrow": "The enduring third force", "headline": "Die Linke never really left",
         "lines": {"spd":1,"cdu":0.3,"linke_pds":1,"gruene":0,"afd":0},
         "body": "Add Die Linke and its consistency stands out: double digits in every single election since 1990, and part of Berlin's governing coalition for most of 2001–2011 and again 2016–2023 — longer than in any other state measured here."},
        {"eyebrow": "The rising fourth force", "headline": "Then Greens nearly overtook everyone",
         "lines": {"spd":1,"cdu":0.3,"linke_pds":0.3,"gruene":1,"afd":0},
         "markers": [{"year": 2019, "label": "Greens 27.6%, European election"}],
         "body": "In the 2019 European election, Berlin's Greens hit <strong>27.6%</strong> — ahead of every other party in the city that year. By the 2021 federal election they stood at <strong>22.4%</strong>, effectively tied with SPD for first place."},
        {"eyebrow": "Where the AfD stands", "headline": "The weakest AfD result in this series",
         "lines": {"spd":0.3,"cdu":0.3,"linke_pds":0.3,"gruene":0.3,"afd":1},
         "body": "AfD reached just <strong>15.2%</strong> in Berlin's 2025 federal result — its lowest peak of any state or region examined in this series so far, well under half its Sachsen or Sachsen-Anhalt share."},
        {"eyebrow": "The economic picture", "headline": "Income slipped, GDP boomed — AfD stayed the weakest",
         "lines": {"spd":0.15,"cdu":0.15,"linke_pds":0.15,"gruene":0.15,"afd":0.15}, "econ": True,
         "body": "Berlin is the one exception in this series: its income share actually <em>fell</em> relative to the national average, from <strong>94.5%</strong> in 2001 to <strong>91.9%</strong> in 2019, even as GDP per capita nearly doubled (€25,500 to €42,900) and debt per capita fell sharply (€14,000 to €12,300, after Berlin's post-reunification debt consolidation). If economic anxiety alone drove the AfD, Berlin's numbers point the wrong way — and its AfD result stayed the weakest of any state examined in this series."},

        {"eyebrow": "One city, four real contenders", "headline": "No opposition-flip story here",
         "lines": {"spd":1,"cdu":1,"linke_pds":1,"gruene":1,"afd":0.5},
         "body": "SPD, CDU, Die Linke and the Greens have all taken real turns leading or nearly leading Berlin. Because Berlin is tracked here as a single citywide result rather than an average of many municipalities, these numbers are Berlin's actual results, not a statistical approximation.",
         "cta": [("Open the current standing tool", "../map-current-standing-trends/"), ("Open the swing map", "../map-trends/")]},
    ],
    "methodology_html": '''    <p>This chart uses the same <strong>current standing</strong> composite as the Current Standing tool. Unlike every other story in this series, Berlin is recorded as a <strong>single citywide unit</strong> in the underlying dataset rather than hundreds of separate municipalities, so there is no municipality-averaging bias here — these are Berlin's actual results. That single-record structure does have one side effect: a party that narrowly misses the top five citywide is recorded as zero rather than averaged down. AfD's 2021 federal result (10.3%, sixth place behind the FDP) fell into that gap in the raw data; this chart uses the correct official figure instead.</p>''',
}, STORY_ROOT + "berlin.html")

# ---------------------------------------------------------------------------
# 5. Baden-Wuerttemberg
# ---------------------------------------------------------------------------
build_story({
    "title": "Baden-Württemberg: The State That Went Green",
    "chart_title": "Baden-Württemberg",
    "chart_subtitle": "Current standing composite (federal + state + European), unweighted municipality average · 1990–2026",
    "hero_body": "Germany's most reliably CDU state in Bundestag elections — until 2011, when it became the first state ever to elect a Green minister-president, and stayed that way for over a decade.",
    "years": YEARS, "election_years": ELECTION_YEARS, "y_max": 60,
    "party_order": ["cdu","spd","gruene","afd"],
    "data": pick(named["baden_wuerttemberg"], ["cdu","spd","gruene","afd"]),
    "econ": econ_series("baden_wuerttemberg", 105, 115),
    "steps": [
        {"eyebrow": "Baden-Württemberg since 1990", "headline": "Germany's most reliably CDU state",
         "lines": {"cdu":1,"spd":0,"gruene":0,"afd":0},
         "body": "CDU topped <strong>50%</strong> in three separate federal elections here (1990, 2013) — a level of dominance unmatched by CDU in any other state in this series, East or West."},
        {"eyebrow": "The traditional No. 2", "headline": "SPD, never close",
         "lines": {"cdu":1,"spd":1,"gruene":0,"afd":0},
         "body": "Add SPD and the gap never really closes: it peaked at <strong>33.4%</strong> in 1998 and fell steadily after, never mounting a serious statewide challenge to the CDU."},
        {"eyebrow": "2011: everything changes", "headline": "The first Green state premier, anywhere",
         "lines": {"cdu":1,"spd":0.3,"gruene":1,"afd":0},
         "markers": [{"year": 2011, "label": "Kretschmann (Greens) becomes premier"}, {"year": 2016, "label": "Greens win the state election"}],
         "body": "In 2011, Winfried Kretschmann became the first Green minister-president anywhere in Germany. In the 2016 state election, the Greens won outright — <strong>30.3%</strong> officially, ahead of the CDU for the only time in this state's history."},
        {"eyebrow": "A methodology note, mid-story", "headline": "Why this chart shows it differently",
         "lines": {"cdu":1,"spd":0.3,"gruene":1,"afd":0},
         "markers": [{"type": "band", "from": 2015, "to": 2017, "label": "Official: Greens 30.3%, CDU 27.0%"}],
         "body": "This chart's own unweighted-average composite shows CDU narrowly ahead of the Greens in 2016 (<strong>31.1% vs 28.2%</strong>), because CDU's strength is spread across many small rural municipalities that count equally here. The <strong>official, population-weighted result was the reverse</strong>: Greens 30.3%, CDU 27.0% — Greens' best state result anywhere in Germany, then or since."},
        {"eyebrow": "Where the AfD stands", "headline": "Still behind both CDU and the Greens",
         "lines": {"cdu":0.3,"spd":0.3,"gruene":0.3,"afd":1},
         "body": "AfD reached <strong>22.0%</strong> in the 2025 federal election here — a real presence, but still well behind both CDU and the Greens, unlike the East German states where it has overtaken everyone."},
        {"eyebrow": "The economic picture", "headline": "Consistently richest, consistently lowest debt",
         "lines": {"cdu":0.15,"spd":0.15,"gruene":0.15,"afd":0.15}, "econ": True,
         "body": "Baden-Württemberg's income has stayed <strong>8-12%</strong> above the national average throughout this period, GDP per capita rose from €29,300 to €46,000, and debt per capita — already the lowest of any state in this series alongside Bavaria — barely moved (€7,600 to €8,300). It is also the West German state where AfD's 2025 share (22.0%) stayed furthest behind both CDU and the Greens."},

        {"eyebrow": "One state, a new No. 2", "headline": "CDU's country, Greens' government",
         "lines": {"cdu":1,"spd":1,"gruene":1,"afd":1},
         "body": "Baden-Württemberg still leans CDU in federal elections, but the Greens — not SPD, not AfD — became its real second party. Every value here is the same 'current standing' composite used across this site.",
         "cta": [("Open the current standing tool", "../map-current-standing-trends/"), ("Open the swing map", "../map-trends/")]},
    ],
    "methodology_html": '''    <p>This chart uses the same <strong>current standing</strong> composite as the Current Standing tool: each of Baden-Württemberg's 1,102 municipalities is shown at its own most recently held election — federal, state, or European — not one single nationwide vote. As with every tool on this site, values are an <strong>unweighted average across municipalities</strong>; this understates the Greens' real 2016 result specifically because their support concentrates in fewer, larger cities while CDU's is spread evenly across many small ones. The 2016 state-election figures quoted in the text are the official, population-weighted results.</p>''',
}, STORY_ROOT + "baden-wuerttemberg.html")

# ---------------------------------------------------------------------------
# 6. NRW
# ---------------------------------------------------------------------------
build_story({
    "title": "Nordrhein-Westfalen: Still CDU vs. SPD",
    "chart_title": "Nordrhein-Westfalen",
    "chart_subtitle": "Current standing composite (federal + state + European), unweighted municipality average · 1990–2026",
    "hero_body": "Germany's most populous state has run on the same two-party logic for 35 years. The Greens are rising and the AfD has arrived, but neither has displaced the original rivalry.",
    "years": YEARS, "election_years": ELECTION_YEARS, "y_max": 55,
    "party_order": ["cdu","spd","gruene","afd"],
    "data": pick(named["nrw"], ["cdu","spd","gruene","afd"]),
    "econ": econ_series("nrw", 94, 104),
    "steps": [
        {"eyebrow": "NRW since 1990", "headline": "A genuine two-party contest",
         "lines": {"cdu":1,"spd":1,"gruene":0,"afd":0},
         "body": "CDU and SPD have traded the lead back and forth for 35 years like textbook Volksparteien — SPD peaked at <strong>43.0%</strong> in 1998, CDU hit <strong>45.0%</strong> in 2013. Neither has ever fallen far behind the other for long."},
        {"eyebrow": "The rising third force", "headline": "Greens, slowly building",
         "lines": {"cdu":1,"spd":1,"gruene":1,"afd":0},
         "body": "Add the Greens and the trend is steady rather than dramatic: from <strong>3.8%</strong> in 1990 to <strong>13.2%</strong> in 2021, a real third force but still well behind the big two in federal elections."},
        {"eyebrow": "2013: a new arrival", "headline": "AfD, present but contained",
         "lines": {"cdu":1,"spd":1,"gruene":0.3,"afd":1},
         "markers": [{"year": 2013, "label": "AfD founded"}],
         "body": "AfD enters in 2013 at under <strong>1%</strong> — the weakest first showing of any state examined in this series — and by 2025 reached <strong>17.9%</strong>, still the smallest of the four parties tracked here."},
        {"eyebrow": "The East-West contrast", "headline": "Less than half the Sachsen share",
         "lines": {"cdu":0.3,"spd":0.3,"gruene":0.3,"afd":1},
         "body": "NRW's 2025 AfD result (<strong>17.9%</strong>) sits at under half of Sachsen's (<strong>45.3%</strong>) for the same election — the clearest single number showing how differently this story has played out in West and East Germany."},
        {"eyebrow": "Where it stands now", "headline": "Still CDU, still SPD",
         "lines": {"cdu":1,"spd":1,"gruene":1,"afd":0.3},
         "body": "By 2025, CDU (<strong>34.7%</strong>) and SPD (<strong>18.8%</strong>) remain the state's top two forces, with the Greens (<strong>10.3%</strong>) and AfD (<strong>17.9%</strong>) both real but secondary."},
        {"eyebrow": "The economic picture", "headline": "Near the national average, drifting slightly down",
         "lines": {"cdu":0.15,"spd":0.15,"gruene":0.15,"afd":0.15}, "econ": True,
         "body": "NRW's income share slipped from <strong>101%</strong> to <strong>98%</strong> of the national average between 2001 and 2019, and its debt per capita rose from €10,600 to €11,800 — the opposite direction from most East German states over the same period. GDP per capita still grew steadily, from €25,100 to €37,800. NRW's AfD share (17.9% by 2025) stayed among the smallest of any state in this series."},

        {"eyebrow": "One state, one steady rivalry", "headline": "35 years, same two names on top",
         "lines": {"cdu":1,"spd":1,"gruene":1,"afd":1},
         "body": "Of every state examined in this series, NRW has changed the least. Every value here is the same 'current standing' composite used across this site.",
         "cta": [("Open the current standing tool", "../map-current-standing-trends/"), ("Open the swing map", "../map-trends/")]},
    ],
    "methodology_html": '''    <p>This chart uses the same <strong>current standing</strong> composite as the Current Standing tool: each of NRW's 396 municipalities is shown at its own most recently held election — federal, state, or European — not one single nationwide vote. As with every tool on this site, values are an <strong>unweighted average across municipalities</strong>, which tends to overstate the AfD's most rural strongholds relative to the official, population-weighted result.</p>''',
}, STORY_ROOT + "nrw-opposition.html")

# ---------------------------------------------------------------------------
# 7. Saarland
# ---------------------------------------------------------------------------
build_story({
    "title": "Saarland: SPD's Smallest Stronghold",
    "chart_title": "Saarland",
    "chart_subtitle": "Current standing composite (federal + state + European), unweighted municipality average · 1990–2026",
    "hero_body": "Germany's smallest mainland state was also its strongest SPD state — until its own most famous politician split the left vote and handed CDU and the AfD room to grow.",
    "years": YEARS, "election_years": ELECTION_YEARS, "y_max": 60,
    "party_order": ["spd","cdu","gruene","afd"],
    "data": pick(named["saarland"], ["spd","cdu","gruene","afd"]),
    "econ": econ_series("saarland", 90, 100),
    "steps": [
        {"eyebrow": "Saarland since 1990", "headline": "The strongest SPD state anywhere",
         "lines": {"spd":1,"cdu":0,"gruene":0,"afd":0},
         "body": "SPD topped <strong>50%</strong> in three of Saarland's first four Bundestag elections, peaking at <strong>52.8%</strong> in 1998 — the single strongest SPD federal result of any state measured in this series."},
        {"eyebrow": "The traditional rival", "headline": "CDU, a consistent second",
         "lines": {"spd":1,"cdu":1,"gruene":0,"afd":0},
         "body": "Add CDU and it's a stable two-party pattern through the 1990s — never in serious danger of beating SPD, but always the clear No. 2."},
        {"eyebrow": "2005: Lafontaine's split", "headline": "The Left vote fractures",
         "lines": {"spd":1,"cdu":1,"gruene":0.3,"afd":0},
         "markers": [{"year": 2005, "label": "Lafontaine leaves SPD, joins Die Linke"}],
         "body": "Oskar Lafontaine — Saarland's own former SPD premier and federal finance minister — left the party and helped found Die Linke. In the 2005 federal election, Die Linke won <strong>18.0%</strong> here, then <strong>20.4%</strong> in 2009, the strongest Die Linke result anywhere in West Germany. SPD's own share fell from 43.6% to 33.5% and then 25.0% over the same years."},
        {"eyebrow": "The Greens, by comparison", "headline": "Germany's weakest Green state",
         "lines": {"spd":1,"cdu":1,"gruene":1,"afd":0},
         "body": "Unlike Baden-Württemberg or NRW, the Greens never became Saarland's real opposition — they've never cleared <strong>12%</strong> here, and stood at just <strong>3.9%</strong> in 2025, the weakest Green result of any West German state in this series."},
        {"eyebrow": "2013: a new arrival", "headline": "AfD closes in on CDU",
         "lines": {"spd":0.3,"cdu":1,"gruene":0.3,"afd":1},
         "body": "AfD enters in 2013 at <strong>5.0%</strong> and grows steadily to <strong>21.9%</strong> by 2025 — just a few points behind CDU's <strong>28.2%</strong>, the closest an AfD result has come to overtaking CDU specifically (rather than SPD) in any West German state examined here."},
        {"eyebrow": "The economic picture", "headline": "The clearest economic-decline story in this series",
         "lines": {"spd":0.15,"cdu":0.15,"gruene":0.15,"afd":0.15}, "econ": True,
         "body": "Saarland's income share fell from <strong>97%</strong> to <strong>93%</strong> of the national average between 2001 and 2019 — the steepest relative decline of any West German state in this series, echoing its long industrial contraction in coal and steel. Debt per capita held roughly flat (€10,500 both years). Of every West German state examined here, Saarland's AfD came closest to overtaking CDU directly, reaching 21.9% by 2025."},

        {"eyebrow": "One state, an old loyalty tested", "headline": "SPD's lead has shrunk, not disappeared",
         "lines": {"spd":1,"cdu":1,"gruene":1,"afd":1},
         "body": "SPD is still Saarland's largest party, but its once-overwhelming lead is gone — split first by its own former leader, and now squeezed by the AfD. Every value here is the same 'current standing' composite used across this site.",
         "cta": [("Open the current standing tool", "../map-current-standing-trends/"), ("Open the swing map", "../map-trends/")]},
    ],
    "methodology_html": '''    <p>This chart uses the same <strong>current standing</strong> composite as the Current Standing tool: Saarland has only 52 municipalities, the smallest sample of any single-state story in this series, so year-to-year swings here are more sensitive to individual local results than in larger states. Values are an <strong>unweighted average across municipalities</strong>, consistent with every tool on this site.</p>''',
}, STORY_ROOT + "saarland.html")

# ---------------------------------------------------------------------------
# 8. East combined
# ---------------------------------------------------------------------------
build_story({
    "title": "The East: One Region, One Opposition",
    "chart_title": "East Germany (5 states, equal-weighted)",
    "chart_subtitle": "Sachsen-Anhalt, Thüringen, Mecklenburg-Vorpommern, Brandenburg, Berlin — equal-weighted average of each state's own composite · 1990–2026",
    "hero_body": "Zoom out from any single state and the regional pattern is unmistakable: Sachsen-Anhalt, Thüringen, Mecklenburg-Vorpommern, Brandenburg and Berlin, averaged together, tell one shared story about who challenges the CDU — and it changed only once, in 2013.",
    "years": YEARS, "election_years": ELECTION_YEARS, "y_max": 55,
    "party_order": ["cdu","spd","linke_pds","gruene","afd"],
    "data": pick(combined["east_combined"], ["cdu","spd","linke_pds","gruene","afd"]),
    "econ": econ_series_combined(GROUPS["east_combined"], 82, 93),
    "steps": [
        {"eyebrow": "Five states, one region", "headline": "CDU led, but never overwhelmingly",
         "lines": {"cdu":1,"spd":0,"linke_pds":0,"gruene":0,"afd":0},
         "body": "Across these five states and 36 years, CDU's regional average never exceeded <strong>46.6%</strong> and fell as low as <strong>18.6%</strong> by 2021 — a weaker, less stable lead than in Sachsen alone, because Brandenburg (SPD-led) and Berlin (four-way) both pull the regional picture away from a clean CDU story."},
        {"eyebrow": "SPD's regional role", "headline": "Strong in some states, weak in others",
         "lines": {"cdu":1,"spd":1,"linke_pds":0,"gruene":0,"afd":0},
         "body": "SPD's regional average peaked at <strong>40.3%</strong> in 2002 — pulled up by Brandenburg and Berlin specifically, since SPD was never that strong in Sachsen, Thüringen or Sachsen-Anhalt in the same years."},
        {"eyebrow": "The real regional opposition", "headline": "Die Linke, the East's actual rival to CDU",
         "lines": {"cdu":1,"spd":0.3,"linke_pds":1,"gruene":0,"afd":0},
         "body": "Add Die Linke (and predecessor PDS) and the regional mirror-pattern is clear: it averaged above <strong>20%</strong> in every election from 2005 through 2021, peaking at <strong>26.9%</strong> in 2009 — consistently the East's real opposition to CDU, state after state."},
        {"eyebrow": "2013: the region's new opposition", "headline": "AfD's regional breakthrough",
         "lines": {"cdu":1,"spd":0.3,"linke_pds":0.3,"gruene":0.3,"afd":1},
         "markers": [{"year": 2013, "label": "AfD founded"}, {"year": 2017, "label": "AfD 19.8% regional average"}],
         "body": "AfD's regional average jumped from <strong>5.1%</strong> in 2013 to <strong>19.8%</strong> in 2017 — and by 2025 reached <strong>35.6%</strong>, more than triple Die Linke's best year. Every one of these five states shows the same shift, just at different speeds."},
        {"eyebrow": "Berlin's effect on the average", "headline": "Why the Greens show up here at all",
         "lines": {"cdu":0.3,"spd":0.3,"linke_pds":0.3,"gruene":1,"afd":1},
         "body": "The Greens' regional average (<strong>5.6%</strong> in 2021) is almost entirely Berlin's doing — in the other four states, Greens rarely clear 2-3%. Pooling Berlin in with the other four East states is what makes this the one 'East' story in this series where Greens register at all."},
        {"eyebrow": "The economic picture, regionally", "headline": "The whole region converged. The whole region swung.",
         "lines": {"cdu":0.15,"spd":0.15,"linke_pds":0.15,"gruene":0.15,"afd":0.15}, "econ": True,
         "body": "Every one of these five states saw its income share of the national average rise between the early 2000s and 2019 — Brandenburg and Thüringen gained the most, Sachsen-Anhalt and MV close behind. Berlin is the one exception, slipping slightly instead. Debt per capita fell in most of the five over the same period. None of that regional convergence slowed the region's AfD growth, which rose in lockstep across all five states."},

        {"eyebrow": "One region, one clear shift", "headline": "Five states, the same turning point",
         "lines": {"cdu":1,"spd":1,"linke_pds":1,"gruene":1,"afd":1},
         "body": "Whatever the state-by-state differences in degree, the shape is the same across the East: CDU's leading challenger was Die Linke until 2013, and has been the AfD ever since. This chart averages each state's own composite equally, not by municipality count, so no single state dominates the regional picture.",
         "cta": [("Open the Sachsen story", "sachsen-opposition.html"), ("Open the current standing tool", "../map-current-standing-trends/")]},
    ],
    "methodology_html": '''    <p>This chart averages the five member states' own "current standing" composites <strong>equally, one state at a time</strong> — not by pooling every municipality into one giant unweighted average. That matters here specifically because Berlin (1 citywide record) would otherwise be swamped by the hundreds of small municipalities in the other four states; equal-weighting keeps Berlin's distinct four-party pattern visible in the regional picture instead of erasing it. Within each state, values are still an unweighted average across its own municipalities, consistent with every tool on this site.</p>''',
}, STORY_ROOT + "east-germany-opposition.html")

# ---------------------------------------------------------------------------
# 9. West combined
# ---------------------------------------------------------------------------
build_story({
    "title": "The West: CDU vs. SPD, With Greens Closing In",
    "chart_title": "West Germany (4 states, equal-weighted)",
    "chart_subtitle": "Baden-Württemberg, NRW, Schleswig-Holstein, Saarland — equal-weighted average of each state's own composite · 1990–2026",
    "hero_body": "Baden-Württemberg, Nordrhein-Westfalen, Schleswig-Holstein and Saarland, averaged together: a much steadier story than the East's, where the CDU's real challenger has always been SPD — until the Greens started closing the gap.",
    "years": YEARS, "election_years": ELECTION_YEARS, "y_max": 55,
    "party_order": ["cdu","spd","gruene","afd"],
    "data": pick(combined["west_combined"], ["cdu","spd","gruene","afd"]),
    "econ": econ_series_combined(GROUPS["west_combined"], 96, 106),
    "steps": [
        {"eyebrow": "Four states, one region", "headline": "CDU's steadiest lead in this series",
         "lines": {"cdu":1,"spd":0,"gruene":0,"afd":0},
         "body": "Across these four states, CDU's regional average never fell below <strong>25.7%</strong> in three decades — the most stable lead of any region examined in this series, East or West."},
        {"eyebrow": "The traditional rival", "headline": "SPD, always close, rarely ahead",
         "lines": {"cdu":1,"spd":1,"gruene":0,"afd":0},
         "body": "Add SPD and the regional pattern is the classic Volksparteien rivalry: it peaked at <strong>42.6%</strong> in 1998, within a few points of CDU that year, and has remained the clear second party in every federal election since."},
        {"eyebrow": "The rising third force", "headline": "Greens, closing the gap",
         "lines": {"cdu":1,"spd":1,"gruene":1,"afd":0},
         "body": "Add the Greens and the trend is unmistakable: from <strong>3.6%</strong> in 1990 to <strong>10.8%</strong> in 2021 — still behind SPD regionally, but pulled up sharply by Baden-Württemberg's Kretschmann-era breakthrough."},
        {"eyebrow": "2013: a new arrival", "headline": "AfD, present but well behind",
         "lines": {"cdu":1,"spd":1,"gruene":0.3,"afd":1},
         "markers": [{"year": 2013, "label": "AfD founded"}],
         "body": "AfD's regional average reached <strong>19.8%</strong> by 2025 — a real presence, but barely more than half the East's regional average (<strong>35.6%</strong>) for the same election."},
        {"eyebrow": "The East-West contrast", "headline": "The clearest single comparison in this series",
         "lines": {"cdu":0.3,"spd":0.3,"gruene":0.3,"afd":1},
         "body": "Put West and East regional AfD averages side by side for 2025 and the gap is stark: <strong>19.8%</strong> here versus <strong>35.6%</strong> there — a near two-to-one difference that holds across every individual state pairing in this series."},
        {"eyebrow": "The economic picture, regionally", "headline": "Right at the national average, the whole time",
         "lines": {"cdu":0.15,"spd":0.15,"gruene":0.15,"afd":0.15}, "econ": True,
         "body": "Averaged together, these four West German states have sat almost exactly at the national income average for two decades — never more than about 1.5 points off in either direction. That stability sits alongside the steadiest political rivalry in this series: CDU and SPD trading the lead, AfD staying well under the eastern regional average throughout."},

        {"eyebrow": "One region, a familiar rivalry", "headline": "Still CDU and SPD, with company",
         "lines": {"cdu":1,"spd":1,"gruene":1,"afd":1},
         "body": "The West's core rivalry hasn't flipped the way the East's has — CDU and SPD remain the top two regionally, with the Greens now a genuine third force and AfD a smaller fourth. This chart averages each state's own composite equally, not by municipality count.",
         "cta": [("Open the East Germany story", "east-germany-opposition.html"), ("Open the current standing tool", "../map-current-standing-trends/")]},
    ],
    "methodology_html": '''    <p>This chart averages the four member states' own "current standing" composites <strong>equally, one state at a time</strong> — not by pooling every municipality into one giant unweighted average, which would let NRW's larger cities or Baden-Württemberg's many small towns dominate disproportionately. Within each state, values are still an unweighted average across its own municipalities, consistent with every tool on this site.</p>''',
}, STORY_ROOT + "west-germany-opposition.html")

# ---------------------------------------------------------------------------
# 10. Rich vs Poor
# ---------------------------------------------------------------------------
build_story({
    "title": "Income and the Vote: Poor, Rich and Super-Rich States",
    "chart_title": "By income tier (equal-weighted state averages)",
    "chart_subtitle": "Poor: MV, Brandenburg, Sachsen, Sachsen-Anhalt, Niedersachsen · Rich: NRW, Bayern · Super-rich: Hessen, Baden-Württemberg",
    "hero_body": "Group states by average income instead of by geography, and a real pattern shows up in the AfD numbers — but not the simple 'poorer states vote AfD' story you might expect. What actually separates these groups is history as much as income.",
    "years": YEARS, "election_years": ELECTION_YEARS, "y_max": 45,
    "party_order": ["afd_poor","afd_rich","afd_superrich"],
    "party_colors": {"afd_poor": "#e0622f", "afd_rich": "#4a90e2", "afd_superrich": "#46962B"},
    "party_labels": {"afd_poor": "AfD — poor states", "afd_rich": "AfD — rich states", "afd_superrich": "AfD — super-rich states"},
    "data": {
        "afd_poor": combined["poor_combined"]["afd"],
        "afd_rich": combined["rich_combined"]["afd"],
        "afd_superrich": combined["superrich_combined"]["afd"],
    },
    "steps": [
        {"eyebrow": "Three income tiers", "headline": "Grouping states by income, not geography",
         "lines": {"afd_poor":0,"afd_rich":0,"afd_superrich":0},
         "body": "Poor: Mecklenburg-Vorpommern, Brandenburg, Sachsen, Sachsen-Anhalt and Niedersachsen. Rich: NRW and Bayern. Super-rich: Hessen and Baden-Württemberg. Each group's line below is an equal-weighted average of its member states' own AfD share."},
        {"eyebrow": "The poor states", "headline": "By far the strongest AfD support",
         "lines": {"afd_poor":1,"afd_rich":0,"afd_superrich":0},
         "body": "The poor-state average was still at <strong>0%</strong> before 2013, but reached <strong>37.0%</strong> by 2025 — more than any single income group, and more than most individual states in this series."},
        {"eyebrow": "The rich states", "headline": "A much smaller rise",
         "lines": {"afd_poor":1,"afd_rich":1,"afd_superrich":0},
         "body": "NRW and Bayern together reached just <strong>19.8%</strong> by 2025 — almost exactly half the poor-state average, for the same election."},
        {"eyebrow": "The super-rich states", "headline": "Not actually the lowest",
         "lines": {"afd_poor":1,"afd_rich":1,"afd_superrich":1},
         "body": "Here's the surprise: Hessen and Baden-Württemberg — Germany's two highest-income states — landed at <strong>21.4%</strong>, slightly <em>higher</em> than the merely 'rich' NRW/Bayern group (19.8%), not lower. Income alone doesn't cleanly predict AfD support among the western states."},
        {"eyebrow": "What actually explains the gap", "headline": "It's East vs. West more than rich vs. poor",
         "lines": {"afd_poor":1,"afd_rich":0.3,"afd_superrich":0.3},
         "body": "The real dividing line in this data isn't income tier — it's whether a state was part of the former East Germany. Four of the five 'poor' states here are East German; strip out Niedersachsen (which, at roughly the national-average income level, doesn't statistically belong in this group at all) and the remaining four East states would show an even higher average."},
        {"eyebrow": "One correlation, one caveat", "headline": "Income tracks the story, it doesn't drive it",
         "lines": {"afd_poor":1,"afd_rich":1,"afd_superrich":1},
         "body": "Real average income (verfügbares Einkommen) does correlate with this chart's groupings — roughly €25,100 per person in Sachsen-Anhalt versus €31,500 in Bayern — but the East/West political history behind those numbers is doing at least as much explanatory work as income itself.",
         "cta": [("Open the East Germany story", "east-germany-opposition.html"), ("Open the current standing tool", "../map-current-standing-trends/")]},
    ],
    "methodology_html": '''    <p>Each line is an <strong>equal-weighted average of its member states' own "current standing" composites</strong> (federal, state and European results, unweighted municipality average within each state) — not a population-weighted national figure. <strong>Niedersachsen's inclusion in the "poor" group follows the grouping as given</strong>, but real income data (Statistisches Bundesamt, 2023) puts its disposable income per capita at roughly €28,000 — close to the national average of €28,452, and well above Sachsen-Anhalt's €25,094. Niedersachsen is solidly middle-income, not among Germany's poorest states by that measure; its presence in this "poor" group pulls that line's AfD average down slightly relative to the four East German states alone.</p>''',
}, STORY_ROOT + "income-and-the-vote.html")

# ---------------------------------------------------------------------------
# 11. Schleswig-Holstein
# ---------------------------------------------------------------------------
build_story({
    "title": "Schleswig-Holstein: The North's Steady Rivalry",
    "chart_title": "Schleswig-Holstein",
    "chart_subtitle": "Current standing composite (federal + state + European), unweighted municipality average · 1990–2026",
    "hero_body": "Germany's northernmost state runs on a familiar West German pattern — CDU on top, SPD close behind — but with the Greens rising faster here than almost anywhere else, and the AfD arriving later and smaller than in most West German states.",
    "years": YEARS, "election_years": ELECTION_YEARS, "y_max": 55,
    "party_order": ["cdu","spd","gruene","afd"],
    "data": pick(named["schleswig_holstein"], ["cdu","spd","gruene","afd"]),
    "econ": econ_series("schleswig_holstein", 95, 104),
    "steps": [
        {"eyebrow": "Schleswig-Holstein since 1990", "headline": "CDU's coastal stronghold",
         "lines": {"cdu":1,"spd":0,"gruene":0,"afd":0},
         "body": "CDU led every federal election here from 1990 on, peaking at <strong>49.3%</strong> that year and never falling below <strong>26.4%</strong> even at its weakest, in 2021."},
        {"eyebrow": "The traditional rival", "headline": "SPD, closer than in most West states",
         "lines": {"cdu":1,"spd":1,"gruene":0,"afd":0},
         "body": "Add SPD and 1998 stands out: <strong>41.1%</strong>, briefly ahead of a dip in the CDU's own number that year — the closest SPD came to overtaking CDU of any West German state examined in this series."},
        {"eyebrow": "The rising third force", "headline": "A real Green surge, in one specific year",
         "lines": {"cdu":1,"spd":1,"gruene":1,"afd":0},
         "markers": [{"year": 2019, "label": "Greens 25.8%, European election"}],
         "body": "In the 2019 European election, Greens reached <strong>25.8%</strong> here — one of their strongest results anywhere in Germany that year — before settling back to <strong>12.7%</strong> by the 2025 federal election, still SH's clearest third force."},
        {"eyebrow": "2013: a new, smaller arrival", "headline": "AfD, present but modest",
         "lines": {"cdu":1,"spd":0.3,"gruene":0.3,"afd":1},
         "markers": [{"year": 2013, "label": "AfD founded"}],
         "body": "AfD enters in 2013 at <strong>2.8%</strong> and grows to <strong>17.5%</strong> by 2025 — a real presence, but among the smaller AfD results of any West German state in this series."},
        {"eyebrow": "Where it stands now", "headline": "Still CDU, still SPD",
         "lines": {"cdu":1,"spd":1,"gruene":1,"afd":0.5},
         "body": "By 2025, CDU (<strong>31.2%</strong>) and SPD (<strong>16.0%</strong>) remain on top, with Greens (<strong>12.7%</strong>) and AfD (<strong>17.5%</strong>) both real but secondary forces."},
        {"eyebrow": "The economic picture", "headline": "Income caught up to the national average",
         "lines": {"cdu":0.15,"spd":0.15,"gruene":0.15,"afd":0.15}, "econ": True,
         "body": "Schleswig-Holstein's income share crossed from just below the national average (<strong>98.3%</strong> in 2001) to just above it (<strong>101.1%</strong> in 2019) — modest, genuine convergence. GDP per capita grew from €23,400 to €34,800, while debt per capita stayed roughly flat (€11,200 to €11,500). Its AfD result (17.5% by 2025) tracked the general West German pattern: real, but modest."},

        {"eyebrow": "One state, a familiar shape", "headline": "CDU and SPD, with a Green interlude",
         "lines": {"cdu":1,"spd":1,"gruene":1,"afd":1},
         "body": "Schleswig-Holstein's underlying rivalry has stayed CDU-vs-SPD for 35 years, the same as NRW and Baden-Württemberg — this state just happened to give the Greens their single best moment of any state in this series, in one European election. Every value here is the same 'current standing' composite used across this site.",
         "cta": [("Open the West Germany story", "west-germany-opposition.html"), ("Open the current standing tool", "../map-current-standing-trends/")]},
    ],
    "methodology_html": '''    <p>This chart uses the same <strong>current standing</strong> composite as the Current Standing tool: each of Schleswig-Holstein's ~1,103–1,105 municipalities is shown at its own most recently held election — federal, state, or European — not one single nationwide vote. As with every tool on this site, values are an <strong>unweighted average across municipalities</strong>. Not shown here: the SSW, representing Schleswig-Holstein's Danish and Frisian minority, holds a constitutional exemption from the 5% threshold and has a long, distinctive local history this chart's four-party frame doesn't capture.</p>''',
}, STORY_ROOT + "schleswig-holstein.html")

print("Done.")
