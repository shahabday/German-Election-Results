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
  - business_registrations_2008_2025.json  AI004-1  Regionalatlas: Gewerbeanmeldungen
                                 je 10.000 Einwohner (already a rate, computed by Destatis)
  - life_expectancy_by_state.json  12613-06-01-4-B  Statistik der Sterbefaelle, Lebenserwartung
                                 nach Alter und Geschlecht (period life table), Bundeslaender,
                                 age 0 (at birth), male + female separately - state-level,
                                 single year (2023) only
  - tax_revenue_capacity_2022_2024.json  71231-01-03-4  Realsteuervergleich, Steuereinnahmekraft
                                 (STNW15) - total municipal tax revenue capacity (Grundsteuer A/B,
                                 Gewerbesteuer netto, plus the municipal shares of income and VAT
                                 revenue) summed across all municipalities in the county, in EUR;
                                 divided here by population to get EUR per resident
  - gini_income_inequality_by_state.json  12241-02-01  Einkommen und Lebensbedingungen (EU-SILC):
                                 Gini-Index des verfuegbaren Aequivalenzeinkommens and the S80/S20
                                 income-quintile ratio - state-level (the source table also has
                                 Regierungsbezirk-level rows, but every state already has its own
                                 direct row, so no aggregation was needed), 2021-2025 only (EU-SILC
                                 sub-sample, not run before 2021)
  - naturalization_rate_2011_2025.json  12511-04-01-4  Einbuergerungsstatistiken,
                                 Einbuergerungsquote (BEV008Q) - naturalizations that year as a
                                 share of the "Einbuergerungspotential" (foreign residents who have
                                 met the minimum residency requirement), already computed as a
                                 rate by Destatis
  - students_by_county_ws2023_24.json  21311-01-01-4  Statistik der Studierenden, students by
                                 sex and nationality, winter semester 2023/24 only (single
                                 snapshot, not a time series) - "foreign" here means non-German
                                 citizenship, both Bildungsinlaender (grew up/schooled in Germany)
                                 and Bildungsauslaender (came from abroad for the degree) counted
                                 together; only ~240 of 490 counties have a university/college at
                                 all, the rest are genuinely 0, not missing data
  - childcare_coverage_u3_2025.json  22543-03-01-4-B  Statistik der Kinder in
                                 Kindertagesbetreuung, Betreuungsquote (KIND36) for children
                                 under 3, KINTE5="Insgesamt" (all care types combined), single
                                 Stichtag 01.03.2025 - the three single-year age bands (0-1,
                                 1-2, 2-3) are simply averaged here since no combined "under 3"
                                 rate is published directly
  - hospital_beds_2024.json     23111-01-05-4-B  Krankenhausstatistik: Grunddaten, "aufgestellte
                                 Betten im Jahresdurchschnitt" (GES017), summed across all 15
                                 Fachabteilungen (departments) since no combined total is
                                 separately selectable - Stichtag 31.12.2024; divided here by
                                 population for beds per 1,000 residents
  - pkw_bestand_2026.json       46251-01-03-4-B  Statistik des Kraftfahrzeug- und
                                 Anhaengerbestandes, Personenkraftwagen (PKW001) "insgesamt",
                                 Stichtag 01.01.2026; divided here by 2025 population (closest
                                 available) for cars per 1,000 residents
  - renewable_electricity_share_by_state.json  86251-Z-02  Anteil erneuerbarer Energien am
                                 Bruttostromverbrauch - already a rate, computed by the
                                 statistical offices themselves; STATE-LEVEL ONLY. Some states
                                 exceed 100% in windy years (net electricity exporters), 2009-2023
  - tourism_overnight_stays_per_capita_2024.json  AI012  Regionalatlas Deutschland, "Uebernachtungen
                                 je EW" - overnight stays per resident, already computed by
                                 Destatis, single year (2024)
  - new_housing_completions_2024.json  31121-01-02-4  Statistik der Baufertigstellungen,
                                 "Wohnungen" (WOHN01) completed that year, all building sizes
                                 combined (Insgesamt), Jahressumme 2024; divided here by
                                 population for completions per 1,000 residents
  - building_land_sales_2025.json  61511-01-03-4-B  Statistik der Kaufwerte fuer Bauland,
                                 Veraeusserungsfaelle von Bauland (BAU001, transaction count)
                                 and Durchschnittlicher Kaufwert je qm (BAU004, average price
                                 per square meter), Jahressumme 2025. NOTE: this is sales of
                                 UNDEVELOPED building land/plots, not existing houses or
                                 apartments - Germany has no free, uniform annual source for
                                 actual home-resale counts or prices (those live with each
                                 region's own Gutachterausschuss); this is the closest
                                 available free, county-level, annual proxy for real-estate
                                 transaction activity. transaction count divided here by
                                 population for sales per 1,000 residents; price per sqm used
                                 as published.

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
    business_formation_rate = load("business_registrations_2008_2025.json")
    life_expectancy_raw = load("life_expectancy_by_state.json")
    tax_revenue_raw = load("tax_revenue_capacity_2022_2024.json")
    gini_raw = load("gini_income_inequality_by_state.json")
    naturalization_rate = load("naturalization_rate_2011_2025.json")
    students_raw = load("students_by_county_ws2023_24.json")
    childcare_raw = load("childcare_coverage_u3_2025.json")
    hospital_beds_raw = load("hospital_beds_2024.json")
    pkw_raw = load("pkw_bestand_2026.json")
    health_personnel_by_state = load("health_personnel_density_by_state.json")
    renewable_by_state = load("renewable_electricity_share_by_state.json")
    tourism_raw = load("tourism_overnight_stays_per_capita_2024.json")
    housing_completions_raw = load("new_housing_completions_2024.json")
    building_land_raw = load("building_land_sales_2025.json")
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

    life_expectancy_by_state = {}
    for state, years in life_expectancy_raw.items():
        life_expectancy_by_state[state] = {}
        for year, mf in years.items():
            life_expectancy_by_state[state][year] = round((mf["m"] + mf["f"]) / 2, 1)
    life_expectancy = broadcast_state_metric(life_expectancy_by_state, county_to_state)

    tax_revenue_capacity = {}
    for ags, years in tax_revenue_raw.items():
        pop_years = population.get(ags, {})
        tax_revenue_capacity[ags] = {}
        for year, total_eur in years.items():
            pop = pop_years.get(year)
            if total_eur is None or pop is None or pop == 0:
                tax_revenue_capacity[ags][year] = None
            else:
                tax_revenue_capacity[ags][year] = round(total_eur / pop, 0)

    gini_by_state = {}
    s80s20_by_state = {}
    for state, years in gini_raw.items():
        gini_by_state[state] = {}
        s80s20_by_state[state] = {}
        for year, vals in years.items():
            if vals.get("gini") is not None:
                gini_by_state[state][year] = vals["gini"]
            if vals.get("s80s20") is not None:
                s80s20_by_state[state][year] = vals["s80s20"]
    gini_index = broadcast_state_metric(gini_by_state, county_to_state)
    income_quintile_ratio = broadcast_state_metric(s80s20_by_state, county_to_state)

    foreign_student_share = {}
    for ags, counts in students_raw.items():
        total = counts.get("total")
        foreign = counts.get("foreign")
        if total and foreign is not None and total > 0:
            foreign_student_share[ags] = {"2023": round(foreign / total * 100, 1)}

    childcare_coverage_u3 = {}
    for ags, vals in childcare_raw.items():
        rate = vals.get("rate")
        if rate is not None:
            childcare_coverage_u3[ags] = {"2025": rate}

    hospital_beds_per_1000 = {}
    for ags, beds in hospital_beds_raw.items():
        pop = population.get(ags, {}).get("2024")
        if beds is not None and pop:
            hospital_beds_per_1000[ags] = {"2024": round(beds / pop * 1000, 2)}

    car_ownership_per_1000 = {}
    for ags, cars in pkw_raw.items():
        pop = population.get(ags, {}).get("2025")
        if cars is not None and pop:
            car_ownership_per_1000[ags] = {"2025": round(cars / pop * 1000, 1)}

    health_personnel_density = broadcast_state_metric(health_personnel_by_state, county_to_state)
    renewable_electricity_share = broadcast_state_metric(renewable_by_state, county_to_state)

    tourism_intensity = {}
    for ags, val in tourism_raw.items():
        tourism_intensity[ags] = {"2024": val}

    new_housing_rate = {}
    for ags, count in housing_completions_raw.items():
        pop = population.get(ags, {}).get("2024")
        if count is not None and pop:
            new_housing_rate[ags] = {"2024": round(count / pop * 1000, 2)}

    building_land_sales_rate = {}
    building_land_price_per_sqm = {}
    for ags, vals in building_land_raw.items():
        sales = vals.get("sales")
        pop = population.get(ags, {}).get("2025")
        if sales is not None and pop:
            building_land_sales_rate[ags] = {"2025": round(sales / pop * 1000, 3)}
        price = vals.get("avg_value_per_sqm")
        if price is not None:
            building_land_price_per_sqm[ags] = {"2025": price}

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
        ("business_formation_rate", "New business registrations", "per 10,000 residents", "Economic Structure",
         "New business registrations (Gewerbeanmeldungen) per 10,000 residents that year.",
         "New trade/business registrations (Gewerbeanmeldungen - covers most businesses except the liberal professions and agriculture) per 10,000 residents that year, already computed as a rate by Destatis. Counts registrations, not surviving businesses, so it's a signal of entrepreneurial activity and churn rather than net business growth - a county can have a high rate while also having a high closure (Gewerbeabmeldungen) rate. Covers 2008-2025, so it also captures the 2008-09 financial crisis dip and the COVID-era swings.",
         "Regionalatlas Deutschland (regionalstatistik.de), table AI004-1", business_formation_rate),
        ("life_expectancy", "Life expectancy at birth", "years", "Health & Demographics",
         "Average life expectancy at birth, male and female averaged.",
         "Period life expectancy at birth (Lebenserwartung), unweighted average of the separately published male and female figures (male: 76.1-80.3 years, female: 82.4-84.5 years across states in 2023 - the roughly 5-6 year gender gap itself is larger than the gap between any two states). STATE-LEVEL ONLY, and only ONE year exists (2023) - Destatis publishes this from a rolling multi-year period life table, not an annual survey, so a new value only appears every few years. The state gaps track a mix of local healthcare access, industrial history (former mining/heavy-industry regions in the East and Saarland skew lower), and average income - not a good place to look for year-to-year change given only one year is available.",
         "regionalstatistik.de, table 12613-06-01-4-B (Statistik der Sterbefaelle)", life_expectancy),
        ("tax_revenue_capacity", "Tax revenue capacity", "EUR per resident", "Economic Structure",
         "Total municipal tax revenue capacity per resident.",
         "Total municipal tax revenue capacity per resident (Steuereinnahmekraft) - the sum of property tax (Grundsteuer A + B), net business tax (Gewerbesteuer, after the state-bound Gewerbesteuerumlage is deducted), plus the municipality's share of national income tax and VAT revenue, added up across every municipality in the county and divided by county population. This is what actually funds local government services (schools, roads, day care), distinct from resident income or GDP - a county can have modest household incomes but strong tax capacity if it hosts a lot of taxable business activity (Gewerbesteuer is levied on businesses, not residents), or vice versa for a wealthy commuter-belt county with little local industry.",
         "regionalstatistik.de, table 71231-01-03-4 (Realsteuervergleich), \"Steuereinnahmekraft\"; divided by population from table 12411-01-01-4", tax_revenue_capacity),
        ("gini_index", "Income inequality (Gini)", "Gini index (0-100)", "Income & Economy",
         "Gini index of disposable equivalised income - higher means more unequal.",
         "Gini index of disposable (post-tax, post-transfer) equivalised household income, on a 0-100 scale where 0 would be perfectly equal (everyone has the same income) and 100 would be maximally unequal (one household has all of it). Real German states run roughly 23-36. STATE-LEVEL ONLY, and only from 2021 onward - this comes from the EU-SILC survey sub-sample (Einkommen und Lebensbedingungen), which is too small a sample to break out below state level reliably, and the German sub-sample wasn't run this way before 2021. City-states (Hamburg, Berlin, Bremen) and states with a big high-income metro tend to sit higher, since a Gini index is driven by the gap between top and bottom earners, not by the overall income level (compare against tax revenue capacity above, which tracks the level).",
         "regionalstatistik.de, table 12241-02-01 (Einkommen und Lebensbedingungen / EU-SILC), \"Gini-Index des verfuegbaren Aequivalenzeinkommens\"", gini_index),
        ("income_quintile_ratio", "Income quintile ratio (S80/S20)", "ratio", "Income & Economy",
         "How many times more the richest fifth earns than the poorest fifth.",
         "The S80/S20 ratio: total income held by the richest 20% of households divided by total income held by the poorest 20%, from the same EU-SILC survey as the Gini index above. A value of 4.5 means the top fifth collectively earns 4.5 times what the bottom fifth does. It moves in the same direction as the Gini index (they're both inequality measures from the same source) but is more intuitive to read directly - \"the top fifth earns 5x the bottom fifth\" is a more concrete statement than a Gini score. STATE-LEVEL ONLY, 2021 onward, same survey-size caveat as the Gini index.",
         "regionalstatistik.de, table 12241-02-01 (Einkommen und Lebensbedingungen / EU-SILC), \"Einkommensquintilverhaeltnis S80/S20\"", income_quintile_ratio),
        ("naturalization_rate", "Naturalization rate", "% of eligible foreign residents", "Migration & Diversity",
         "Share of eligible foreign residents naturalized as German citizens that year.",
         "Naturalizations that year (Einbuergerungen) as a share of the county's \"Einbuergerungspotential\" - foreign residents who have already met the minimum residency requirement to apply, not all foreign residents. So this measures how many of the people who COULD naturalize actually did that year, not overall citizenship uptake among immigrants generally. A county can score high here even with a small foreign population if its existing eligible residents are naturalizing at a high rate, and low even with a large foreign population if most of it is recent arrivals not yet eligible.",
         "regionalstatistik.de, table 12511-04-01-4 (Einbuergerungsstatistiken), \"Einbuergerungsquote\" (BEV008Q)", naturalization_rate),
        ("foreign_student_share", "International students", "% of enrolled students", "Migration & Diversity",
         "Share of enrolled students who are not German citizens.",
         "Share of all students enrolled at a university/college in the county who hold a non-German citizenship, winter semester 2023/24 (a single snapshot, not a time series). Only around half of Germany's counties have a higher-education institution at all - the other half genuinely show 0%, not missing data, since there's no student population to measure. Where a county does have a university, this is a strong signal of that institution's international draw (technical universities and business schools tend to run higher than regional teacher-training colleges) - it says more about the specific institution than about the county's foreign population generally, since students are transient residents.",
         "regionalstatistik.de, table 21311-01-01-4 (Statistik der Studierenden), WS 2023/24", foreign_student_share),
        ("childcare_coverage_u3", "Childcare coverage (under 3)", "% of children under 3", "Family & Marriage",
         "Share of children under 3 in formal daycare (Kindertagesbetreuung).",
         "Share of children under 3 years old in formal daycare - either a Kindertageseinrichtung (daycare center) or Kindertagespflege (registered childminder) - as of 01.03.2025. Simple average of the three published single-year age bands (0-1, 1-2, 2-3), since Destatis doesn't publish one combined \"under 3\" rate directly; the true population-weighted rate would differ slightly. About 90 of Germany's 490 counties are missing at least one age band's figure (small-county suppression) and are left out here rather than estimated. This directly answers whether local supply of daycare slots is keeping up with demand - it's a supply/uptake rate, not a measure of the under-3 population's size (see the age-group map tool for that).",
         "regionalstatistik.de, table 22543-03-01-4-B (Statistik der Kinder in Kindertagesbetreuung), Stichtag 01.03.2025", childcare_coverage_u3),
        ("hospital_beds_rate", "Hospital beds", "per 1,000 residents", "Health & Demographics",
         "Hospital beds (aufgestellte Betten) per 1,000 residents.",
         "Hospital beds physically set up and staffed on average that year (aufgestellte Betten im Jahresdurchschnitt), summed across all medical departments and all hospitals located in the county, per 1,000 residents, as of 31.12.2024. This counts beds by hospital LOCATION, not by patients' home county - a county with a major regional hospital will show a high rate partly because it treats patients from neighboring counties too, not because its own residents are unusually sick. About 80 of 490 counties have no hospital at all and are left out (0 beds, not missing data, but excluded here since dividing by population would be misleading for a true zero versus a data gap).",
         "regionalstatistik.de, table 23111-01-05-4-B (Krankenhausstatistik: Grunddaten), Stichtag 31.12.2024; divided by population from table 12411-01-01-4", hospital_beds_per_1000),
        ("health_personnel_density", "Health personnel density", "per 1,000 residents", "Health & Demographics",
         "Health sector employees per 1,000 residents, across all care settings.",
         "People employed anywhere in the health sector (Gesundheitspersonal) - doctors, nurses, pharmacists, therapists, administrators, everyone counted in the Gesundheitspersonalrechnung - per 1,000 residents. Much broader than just doctors or hospital staff: it includes outpatient practices, pharmacies, elder care, ambulance services and public health administration. STATE-LEVEL ONLY - this accounting isn't broken out below Bundesland level. Every state has risen steadily since 2008 as the health sector has grown faster than the population nationwide, so compare states to each other within a year rather than reading a rising line as something unique to one state.",
         "regionalstatistik.de, table 88121-Z-03 (Gesundheitspersonalrechnung der Laender), Geschlecht + Art der Einrichtung = Insgesamt", health_personnel_density),
        ("car_ownership_rate", "Car ownership", "cars per 1,000 residents", "Economic Structure",
         "Registered passenger cars (Pkw) per 1,000 residents.",
         "Registered passenger cars (Personenkraftwagen), commercial and private together, per 1,000 residents, as of 01.01.2026 (divided by 2025 population, the closest available). This is vehicle STOCK, not usage - a county can have a high rate because commuting without a car is impractical there (weak public transit, longer distances), or simply because company-fleet cars are registered at a local business address rather than where their drivers actually live, which inflates the rate in counties with big employers or leasing companies.",
         "regionalstatistik.de, table 46251-01-03-4-B (Statistik des Kraftfahrzeug- und Anhaengerbestandes), Stichtag 01.01.2026; divided by population from table 12411-01-01-4", car_ownership_per_1000),
        ("renewable_electricity_share", "Renewable electricity share", "% of gross electricity consumption", "Economic Structure",
         "Renewable share of gross electricity consumption - can exceed 100% in net-exporting states.",
         "Renewable energy's share of gross electricity consumption (Anteil erneuerbarer Energien am Bruttostromverbrauch), already computed by the statistical offices. STATE-LEVEL ONLY. Values above 100% are real, not errors - a windy, sparsely populated state like Schleswig-Holstein can generate far more renewable electricity than it consumes and export the surplus, pushing its own ratio past 100%, while a dense consuming state like Hamburg or Berlin sits in the single digits because it has little land for wind or solar and imports most of its power. So this measures local GENERATION capacity relative to local demand, not how \"green\" a resident's own electricity use is.",
         "regionalstatistik.de, table 86251-Z-02 (Anteil erneuerbarer Energien am Bruttostromverbrauch), 2009-2023", renewable_electricity_share),
        ("tourism_intensity", "Tourism intensity", "overnight stays per resident", "Economic Structure",
         "Hotel/guesthouse overnight stays per resident that year.",
         "Overnight stays (Gaesteuebernachtungen, in establishments with 10+ beds) divided by resident population, already computed by Destatis as part of the Regionalatlas. A value of 1.0 means the county recorded as many tourist overnight stays that year as it has residents; well-known destinations run far higher - the highest county here is well above 50. Purely a volume measure: it doesn't distinguish a few very busy resort towns within a large rural county from evenly-spread tourism, and doesn't capture day-trippers who don't stay overnight at all.",
         "Regionalatlas Deutschland (regionalstatistik.de), table AI012, \"Uebernachtungen je EW\", 2024", tourism_intensity),
        ("new_housing_rate", "New housing construction", "completions per 1,000 residents", "Economic Structure",
         "Newly completed dwellings (Baufertigstellungen) per 1,000 residents that year.",
         "Dwellings (Wohnungen) newly completed in residential buildings that year (Statistik der Baufertigstellungen), all building sizes combined, per 1,000 residents, 2024. This measures completions, not permits or construction starts, so it lags the actual building decision by the construction period (often 1-2+ years for larger projects) - a county mid-way through a construction boom can still show a low rate here if nothing has finished yet. It also says nothing about affordability or who the new housing is for.",
         "regionalstatistik.de, table 31121-01-02-4 (Statistik der Baufertigstellungen), Jahressumme 2024; divided by population from table 12411-01-01-4", new_housing_rate),
        ("building_land_sales_rate", "Building land sales", "transactions per 1,000 residents", "Economic Structure",
         "Undeveloped building-land (plot) sales per 1,000 residents that year.",
         "Number of undeveloped building-land transactions (Baulandverkaeufe - vacant plots sold for future construction, not existing houses or apartments) per 1,000 residents, 2025. This is the closest free, uniform, county-level annual proxy available for real-estate transaction activity in Germany - actual home/apartment resale counts and prices are tracked regionally by each area's own Gutachterausschuss (expert appraisal committee) and aren't published as one free national dataset. A high rate here signals an active land market (new subdivisions, greenfield development), not necessarily a hot existing-home resale market.",
         "regionalstatistik.de, table 61511-01-03-4-B (Statistik der Kaufwerte fuer Bauland), Jahressumme 2025; divided by population from table 12411-01-01-4", building_land_sales_rate),
        ("building_land_price_per_sqm", "Building land price", "EUR per square meter", "Economic Structure",
         "Average purchase price per square meter of building land sold that year.",
         "Average price paid per square meter for undeveloped building land (Baulandpreis) that year, 2025 - a companion to the sales-rate metric above, from the same source. Reflects land value, not home/construction cost, so it's driven heavily by local zoning scarcity and proximity to a city center; the highest values by far are in city-state cores (Berlin, Munich) rather than any particular region generally.",
         "regionalstatistik.de, table 61511-01-03-4-B (Statistik der Kaufwerte fuer Bauland), Jahressumme 2025", building_land_price_per_sqm),
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
