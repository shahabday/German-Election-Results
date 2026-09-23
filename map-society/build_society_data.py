"""Builds map-society's prepared data from the raw regionalstatistik.de pulls in data/raw/.

Raw files were fetched by hand through the regionalstatistik.de GENESIS web GUI
(no API key needed - the automated webservice requires registration since May
2025, but the ordinary table-builder GUI does not). Each raw file is a compact
{ags: {year: value}} dict, keyed by 5-digit county AGS, already filtered down to
the "Insgesamt" (total) row of its source table.

Sources:
  - population_2018_2025.json   12411-01-01-4  Bevoelkerung nach Geschlecht, Stichtag 31.12.
  - marriages_2018_2025.json    12611-01-02-4  Eheschliessungen nach Nationalitaet, Jahr
  - divorces_2018_2024.json     12631-01-02-4  Ehescheidungen, Jahr
  - edu_abitur_2006_2024.json          AI003-2  Regionalatlas: Anteil Schulabgaenger/-innen
                                                  mit allgem. Hochschulreife
  - edu_no_hauptschulabschluss_2006_2024.json  AI003-2  ... ohne Hauptschulabschluss
  - religion_2001_2022.json     fowid.de, "Bundeslaender: Kirchenmitglieder, 2001-2022"
                                 (EKD + Katholische Kirche member statistics, state-level only)
  - sports_membership_2017_2025.json  DOSB Bestandserhebung 2025 PDF, p.17
                                       "Organisationsgrad der Bevoelkerung in den Bundeslaendern"
                                       (state-level sports club membership counts, not a rate)
  - crime_hz_2020_2024.json     BKA Polizeiliche Kriminalstatistik, T01 Grundtabelle "Kreise"
                                 (HZ = Haeufigkeitszahl, cases per 100,000 residents - already
                                 a rate, computed by the BKA itself, not by this script)
  - bedarfsgemeinschaften_persons_2018_2024.json  22811-02-02-4  Personen in
                                 Bedarfsgemeinschaften nach dem SGB II, Stichtag 31.12.
                                 (raw person counts, "Buergergeld" - basic income support)
  - ../../processed/covariates/county_covariates_bonus.csv  share_primary_sector /
                                 share_secondary_sector / share_tertiary_sector columns
                                 (INKAR gross-value-added shares by sector, already pulled for
                                 an earlier tool in this project - reused here, no new fetch)
  - happiness_by_state.json     SKL Gluecksatlas 2025 article (skl-gluecksatlas.de), Tabelle 1
                                 (life-satisfaction index 0-10, state-level, 4 sparse years:
                                 2019, 2021, 2024, 2025 - survey-based, not annual)
  - volunteering_by_state.json  5. Deutscher Freiwilligensurvey 2019, Laenderbericht p.137/148
                                 (Engagementquote, % who volunteer, state-level, single year -
                                 the survey only runs every 5 years)

marriage_rate, divorce_rate and welfare_rate are computed here (count /
population * 1000 or *100); the education shares, sector shares, religion_pct,
happiness and volunteering are already the right unit in their source and
pass through unchanged. sports_rate is computed here (DOSB membership count /
state population * 100) since the PDF only gives population share for the
most recent year. crime_rate (HZ) is used as published, not recomputed.

religion_pct, sports_rate, happiness and volunteering are STATE-level, not
county-level - there's no county resolution for any of these four sources.
Rather than add a second map resolution just for a handful of metrics, the
same state value is broadcast to every county in that state (via
counties.geojson's "state" property), so they render on the existing
county-keyed choropleth as visibly uniform blocks per state. This is
disclosed in each metric's description string, shown in the UI.
"""
import csv
import json
import os

RAW = "data/raw"
OUT_COUNTY = "data/prepared/county"
BONUS_CSV = "../processed/covariates/county_covariates_bonus.csv"


def load(name):
    with open(os.path.join(RAW, name), encoding="utf-8") as f:
        return json.load(f)


def load_bonus_sector_shares():
    """Pulls share_primary/secondary/tertiary_sector straight out of the INKAR
    bonus covariates CSV already sitting in processed/covariates/ from an
    earlier tool - no new fetch needed."""
    primary, secondary, tertiary = {}, {}, {}
    with open(BONUS_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ags = row["county_code"]
            year = str(int(float(row["year"])))
            for target, col in ((primary, "share_primary_sector"),
                                 (secondary, "share_secondary_sector"),
                                 (tertiary, "share_tertiary_sector")):
                raw = row[col]
                if raw == "":
                    continue
                target.setdefault(ags, {})[year] = round(float(raw), 2)
    return primary, secondary, tertiary


def rate_per_1000(count_data, pop_data):
    out = {}
    for ags, years in count_data.items():
        pop_years = pop_data.get(ags, {})
        out[ags] = {}
        for year, count in years.items():
            pop = pop_years.get(year)
            if count is None or pop is None or pop == 0:
                out[ags][year] = None
            else:
                out[ags][year] = round(count / pop * 1000, 2)
    return out


def load_county_to_state():
    with open("data/prepared/counties.geojson", encoding="utf-8") as f:
        gj = json.load(f)
    out = {}
    for feat in gj["features"]:
        props = feat["properties"]
        out[props["county"]] = props["state"]
    return out


def state_population_by_year(population, county_to_state):
    out = {}
    for ags, years in population.items():
        state = county_to_state.get(ags)
        if not state:
            continue
        for year, pop in years.items():
            if pop is None:
                continue
            out.setdefault(state, {}).setdefault(year, 0)
            out[state][year] += pop
    return out


def broadcast_state_metric(state_series, county_to_state):
    """Takes {state_name: {year: value}} and repeats each state's value across
    every county AGS that belongs to it, so it fits the county-keyed schema."""
    out = {}
    for ags, state in county_to_state.items():
        if state in state_series:
            out[ags] = dict(state_series[state])
    return out


def domain_and_cap(series_by_ags):
    vals = [v for years in series_by_ags.values() for v in years.values() if v is not None]
    if not vals:
        return [0, 1], 1
    vals.sort()
    def pct(p):
        idx = min(len(vals) - 1, max(0, round(p * (len(vals) - 1))))
        return vals[idx]
    domain = [pct(0.05), pct(0.95)]

    by_ags_year = {}
    for ags, years in series_by_ags.items():
        for y, v in years.items():
            if v is not None:
                by_ags_year[(ags, y)] = v
    deltas = []
    for ags, years in series_by_ags.items():
        yrs = sorted(y for y in years if years[y] is not None)
        for prev, cur in zip(yrs, yrs[1:]):
            deltas.append(abs(years[cur] - years[prev]))
    deltas.sort()
    cap = deltas[min(len(deltas) - 1, round(0.95 * (len(deltas) - 1)))] if deltas else 1
    return domain, cap


def main():
    population = load("population_2018_2025.json")
    marriages = load("marriages_2018_2025.json")
    divorces = load("divorces_2018_2024.json")
    edu_abitur = load("edu_abitur_2006_2024.json")
    edu_no_hs = load("edu_no_hauptschulabschluss_2006_2024.json")
    religion_by_state = load("religion_2001_2022.json")
    sports_membership_by_state = load("sports_membership_2017_2025.json")
    crime_rate = load("crime_hz_2020_2024.json")
    bedarfsgemeinschaften = load("bedarfsgemeinschaften_persons_2018_2024.json")
    happiness_by_state = load("happiness_by_state.json")
    volunteering_by_state = load("volunteering_by_state.json")
    share_primary, share_secondary, share_tertiary = load_bonus_sector_shares()

    marriage_rate = rate_per_1000(marriages, population)
    divorce_rate = rate_per_1000(divorces, population)
    welfare_rate = {}
    for ags, years in bedarfsgemeinschaften.items():
        pop_years = population.get(ags, {})
        welfare_rate[ags] = {}
        for year, count in years.items():
            pop = pop_years.get(year)
            welfare_rate[ags][year] = round(count / pop * 100, 2) if (count is not None and pop) else None

    county_to_state = load_county_to_state()
    state_pop = state_population_by_year(population, county_to_state)
    sports_rate_by_state = {}
    for state, years in sports_membership_by_state.items():
        sports_rate_by_state[state] = {}
        for year, members in years.items():
            pop = state_pop.get(state, {}).get(year)
            sports_rate_by_state[state][year] = round(members / pop * 100, 2) if pop else None

    religion_pct = broadcast_state_metric(religion_by_state, county_to_state)
    sports_rate = broadcast_state_metric(sports_rate_by_state, county_to_state)
    happiness = broadcast_state_metric(happiness_by_state, county_to_state)
    volunteering = broadcast_state_metric(volunteering_by_state, county_to_state)

    METRICS = [
        ("marriage_rate", "Marriage rate", "per 1,000 residents", "Family & Marriage",
         "New marriages per 1,000 residents that year.",
         "New marriages per 1,000 residents in the county that year (Statistik der Eheschliessungen, marriages counted where at least one spouse lives in the county, divided by county population). Marriage rates have been declining nationwide for decades as cohabitation and later marriage become more common, so a county's level relative to OTHERS in the same year is more informative than its level in isolation.",
         "regionalstatistik.de, table 12611-01-02-4", marriage_rate),
        ("divorce_rate", "Divorce rate", "per 1,000 residents", "Family & Marriage",
         "Divorces finalized per 1,000 residents that year.",
         "Divorces finalized per 1,000 residents that year (Statistik rechtskraeftiger Urteile in Ehesachen). A single year's jump doesn't always mean more marriages are breaking down - court processing backlogs can shift when a divorce is finalized relative to when it was filed, so the multi-year trend is more reliable than any one year.",
         "regionalstatistik.de, table 12631-01-02-4", divorce_rate),
        ("edu_abitur", "School leavers with Abitur", "%", "Education",
         "Share of school leavers with a university entrance qualification.",
         "Share of that year's school leavers (all school types) who left with a general or subject-specific higher education entrance qualification (allgem./fachgeb. Hochschulreife) - the top academic track. Strongly shaped by whether a county has its own Gymnasium (academic-track school) or older students commute elsewhere, so this partly reflects local school infrastructure, not just household background.",
         "Regionalatlas Deutschland (regionalstatistik.de), table AI003-2", edu_abitur),
        ("edu_no_hauptschulabschluss", "School leavers without a degree", "%", "Education",
         "Share of school leavers who left without any qualification.",
         "Share of that year's school leavers who left general education school without even the basic Hauptschulabschluss - the standard proxy for being at risk of not finding an apprenticeship or job. Widely used as an early-warning indicator: counties with a persistently high share here tend to show elevated youth unemployment and welfare receipt a few years later.",
         "Regionalatlas Deutschland (regionalstatistik.de), table AI003-2", edu_no_hs),
        ("religion_pct", "Church membership", "% of population", "Religion & Community",
         "Combined church membership as a share of the state's population.",
         "Combined Protestant (EKD) + Catholic church membership as a share of the state's population (source: fowid.de, based on official EKD/Catholic diocese statistics). STATE-LEVEL ONLY - every county in a state shows the same value, since no county-level source exists for this. Membership has fallen nationwide for decades (formal church-leaving, Kirchenaustritt, is common and easy), so even a state near the top of this ranking is almost certainly still trending downward - use the year slider to see direction, not just level.",
         "fowid.de, \"Bundeslaender: Kirchenmitglieder, 2001-2022\" (EKD + Deutsche Bischofskonferenz statistics)", religion_pct),
        ("sports_rate", "Sports club membership", "% of population", "Religion & Community",
         "Sports club memberships as a share of the state's population.",
         "Registered members of an organized sports club (Landessportbund-affiliated), as a share of the state's population (source: DOSB Bestandserhebung 2025; state population computed here from regionalstatistik.de county figures). Counts memberships, not unique people, so someone in two clubs is counted twice. STATE-LEVEL ONLY - every county in a state shows the same value. The sharp West/East gap traces back to West Germany's much older tradition of the Sportverein as a default local institution, a civic structure the GDR never built in the same form - so this is as much a marker of associational history as of current wealth.",
         "DOSB Bestandserhebung 2025 (dosb.de), p.17; state population from regionalstatistik.de", sports_rate),
        ("crime_rate", "Crime rate", "cases per 100,000 residents", "Crime & Safety",
         "Recorded criminal offenses per 100,000 residents.",
         "All recorded criminal offenses per 100,000 residents that year (Haeufigkeitszahl, BKA Polizeiliche Kriminalstatistik) - reported crime, not necessarily actual crime, and shaped by local policing/reporting practices as well as by the underlying offense rate. Also pulled up mechanically by non-resident activity: a county with a major train station, shopping district, or airport can show a high rate driven by people who don't live there and therefore aren't in the population denominator.",
         "BKA Polizeiliche Kriminalstatistik, T01 Grundtabelle \"Kreise\" (bka.de)", crime_rate),
        ("welfare_rate", "Welfare receipt (Buergergeld)", "% of population", "Labor & Welfare",
         "Share of the population receiving basic income support (Buergergeld).",
         "Share of the county's population receiving basic income support under SGB II (Buergergeld/Hartz IV - Personen in Bedarfsgemeinschaften), computed here from regionalstatistik.de person counts divided by county population. This is a structural indicator, not a cyclical one - in counties where it's persistently high, it reflects the underlying local job market over years, not a recent news-cycle event.",
         "regionalstatistik.de, table 22811-02-02-4", welfare_rate),
        ("share_primary_sector", "Agriculture employment share", "% of gross value added", "Economic Structure",
         "Share of economic output from agriculture, forestry, fishing.",
         "Share of the county's economic output (gross value added) from the primary sector - agriculture, forestry, fishing (INKAR indicator, reused from this project's map-demographics data pull). Nationwide this share is now small almost everywhere, so even a county that looks \"high\" here is usually just less far along the same long-run shift out of agriculture as the rest of the country.",
         "INKAR (BBSR), via processed/covariates/county_covariates_bonus.csv, column \"share_primary_sector\"", share_primary),
        ("share_secondary_sector", "Industry employment share", "% of gross value added", "Economic Structure",
         "Share of economic output from manufacturing and construction.",
         "Share of the county's economic output (gross value added) from the secondary sector - manufacturing and construction (INKAR indicator, reused from this project's map-demographics data pull). Tracking this over time is the most direct way to see (de)industrialization happening in a county, rather than inferring it indirectly from the unemployment rate.",
         "INKAR (BBSR), via processed/covariates/county_covariates_bonus.csv, column \"share_secondary_sector\"", share_secondary),
        ("share_tertiary_sector", "Services employment share", "% of gross value added", "Economic Structure",
         "Share of economic output from services.",
         "Share of the county's economic output (gross value added) from the tertiary sector - services (INKAR indicator, reused from this project's map-demographics data pull). Services is now the largest sector almost everywhere in Germany, so the more informative read is usually which OTHER sector is unusually large in a given county, not how large tertiary itself is.",
         "INKAR (BBSR), via processed/covariates/county_covariates_bonus.csv, column \"share_tertiary_sector\"", share_tertiary),
        ("happiness", "Life satisfaction", "0-10 scale", "Religion & Community",
         "Self-reported life satisfaction, 0-10 scale.",
         "Self-reported general life satisfaction, 0 (not at all satisfied) to 10 (completely satisfied) - survey-based (SKL Gluecksatlas / IfD Allensbach). STATE-LEVEL ONLY, and only 4 sparse survey years (2019, 2021, 2024, 2025) exist - every county in a state shows that state's one value for each of those years. The exact score matters less than the ranking and the gap between states: a move from 7.0 to 6.9 between waves isn't necessarily a real change, but a state that sits near the bottom across all four available years likely reflects something durable.",
         "SKL Gluecksatlas 2025 (skl-gluecksatlas.de), Tabelle 1; underlying survey by IfD Allensbach / SOEP", happiness),
        ("volunteering", "Volunteering rate", "%", "Religion & Community",
         "Share of the population who do formal volunteer work.",
         "Share of the population aged 14+ who do some form of formal volunteer work (Engagementquote, 5. Deutscher Freiwilligensurvey). STATE-LEVEL ONLY, and only ONE year exists (2019) - the survey runs just once every 5 years and the next wave isn't in this dataset. The regional pattern tracks the same West/East and rural/urban associational-culture divide seen in sports club membership above - worth comparing the two side by side.",
         "5. Deutscher Freiwilligensurvey 2019, Laenderbericht (stmas.bayern.de), p.137/148", volunteering),
    ]

    all_years = set()
    for *_, series in METRICS:
        for ags, years in series.items():
            all_years.update(years.keys())
    all_years = sorted(all_years)

    os.makedirs(OUT_COUNTY, exist_ok=True)
    for year in all_years:
        record = {}
        for key, *_ , series in METRICS:
            for ags, years in series.items():
                v = years.get(year)
                if v is None:
                    continue
                record.setdefault(ags, {})[key] = v
        with open(os.path.join(OUT_COUNTY, f"{year}.json"), "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, separators=(",", ":"))

    manifest_metrics = []
    for key, label, unit, category, short_desc, full_desc, source, series in METRICS:
        years_present = sorted({y for years in series.values() for y, v in years.items() if v is not None})
        domain, cap = domain_and_cap(series)
        manifest_metrics.append({
            "key": key,
            "label": label,
            "unit": unit,
            "category": category,
            "description": short_desc,
            "description_full": full_desc,
            "source": source,
            "years": years_present,
            "global_domain": domain,
            "global_delta_cap": cap,
        })

    manifest = {
        "county": {
            "years": all_years,
            "metrics": manifest_metrics,
        }
    }
    with open("data/prepared/metrics_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, separators=(",", ":"))

    print(f"years: {all_years}")
    for m in manifest_metrics:
        print(f"  {m['key']}: {len(m['years'])} years, domain={m['global_domain']}, cap={m['global_delta_cap']}")


if __name__ == "__main__":
    main()
