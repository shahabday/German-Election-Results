"""Exports every raw JSON pull behind map-society and map-population-pyramid into
plain CSV files under processed/society/ and processed/population_age/, alongside the
project's existing processed/ tables (elections, covariates, crosswalks) - so this data
is reusable outside these two map tools, not locked inside their JSON blobs.

Each source JSON has its own shape (a hand-picked design choice per GENESIS table pull,
not something worth normalizing away), so this uses one of a handful of named shape
converters per file rather than a single generic flattener. Run from the repo root:

    python scripts/export_raw_to_csv.py

Also copies over the handful of raw non-JSON originals (xlsx/csv/pdf source files) as-is
for full traceability, and writes one codebook CSV per output folder describing every
file: geography, years, columns, unit, and source table/document.
"""
import csv
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOCIETY_RAW = os.path.join(ROOT, "map-society", "data", "raw")
PYRAMID_RAW = os.path.join(ROOT, "map-population-pyramid", "data", "raw")
OUT_SOCIETY = os.path.join(ROOT, "processed", "society")
OUT_POP_AGE = os.path.join(ROOT, "processed", "population_age")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote {os.path.relpath(path, ROOT)} ({len(rows)} rows)")


# ---------- shape converters ----------

def flat_year(src_path, out_path, key_col, value_col):
    """{key: {year: value}} -> key,year,value"""
    data = load(src_path)
    rows = []
    for key, years in data.items():
        for year, value in years.items():
            if value is not None:
                rows.append([key, year, value])
    write_csv(out_path, [key_col, "year", value_col], rows)


def flat_single(src_path, out_path, key_col, value_col, year):
    """{key: value} -> key,year,value (year comes from the filename, not the data)"""
    data = load(src_path)
    rows = [[key, year, value] for key, value in data.items() if value is not None]
    write_csv(out_path, [key_col, "year", value_col], rows)


def nested_fields_flat(src_path, out_path, key_col, fields, year=None):
    """{key: {field1: v1, field2: v2}} -> key,[year,]field1,field2,..."""
    data = load(src_path)
    header = [key_col] + (["year"] if year else []) + fields
    rows = []
    for key, rec in data.items():
        row = [key] + ([year] if year else []) + [rec.get(f) for f in fields]
        rows.append(row)
    write_csv(out_path, header, rows)


def nested_year_fields(src_path, out_path, key_col, fields):
    """{key: {year: {field1: v1, field2: v2}}} -> key,year,field1,field2,..."""
    data = load(src_path)
    rows = []
    for key, years in data.items():
        for year, rec in years.items():
            rows.append([key, year] + [rec.get(f) for f in fields])
    write_csv(out_path, [key_col, "year"] + fields, rows)


def pyramid_county_year(src_path, out_path, year):
    """{ags: {age_band_label: {m: x, f: y}}} -> ags,year,age_band,sex,count (long format)"""
    data = load(src_path)
    rows = []
    for ags, bands in data.items():
        for band, sexes in bands.items():
            for sex, count in sexes.items():
                if count is not None:
                    rows.append([ags, year, band, sex, count])
    write_csv(out_path, ["ags", "year", "age_band", "sex", "count"], rows)


def pyramid_state(src_path, out_path):
    """{year: {state: {sex: {age_label: count}}}} -> year,state,sex,age_band,count"""
    data = load(src_path)
    rows = []
    for year, states in data.items():
        for state, sexes in states.items():
            for sex, bands in sexes.items():
                for band, count in bands.items():
                    if count is not None:
                        rows.append([year, state, sex, band, count])
    write_csv(out_path, ["year", "state", "sex", "age_band", "count"], rows)


def copy_original(src_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, os.path.basename(src_path))
    shutil.copyfile(src_path, dest)
    print(f"  copied {os.path.relpath(dest, ROOT)} (original, already tabular/source doc)")


# ---------- codebook rows, filled in as each file is exported ----------
society_codebook = []
pop_age_codebook = []


def s(filename, geography, years, columns, unit, source, notes=""):
    society_codebook.append({
        "output_file": filename, "geography": geography, "years": years,
        "columns": columns, "unit": unit, "source": source, "notes": notes,
    })


def p(filename, geography, years, columns, unit, source, notes=""):
    pop_age_codebook.append({
        "output_file": filename, "geography": geography, "years": years,
        "columns": columns, "unit": unit, "source": source, "notes": notes,
    })


def main():
    r = lambda name: os.path.join(SOCIETY_RAW, name)
    o = lambda name: os.path.join(OUT_SOCIETY, name)

    print("map-society ->", os.path.relpath(OUT_SOCIETY, ROOT))

    flat_year(r("marriages_2018_2025.json"), o("marriages.csv"), "ags", "marriages")
    s("marriages.csv", "county", "2018-2025", "ags,year,marriages", "count",
      "regionalstatistik.de, table 12611-01-02-4")

    flat_year(r("divorces_2018_2024.json"), o("divorces.csv"), "ags", "divorces")
    s("divorces.csv", "county", "2018-2024", "ags,year,divorces", "count",
      "regionalstatistik.de, table 12631-01-02-4")

    flat_year(r("population_2018_2025.json"), o("population.csv"), "ags", "population")
    s("population.csv", "county", "2018-2025", "ags,year,population", "residents",
      "regionalstatistik.de, table 12411-01-01-4")

    flat_year(r("edu_abitur_2006_2024.json"), o("edu_abitur.csv"), "ags", "pct_abitur")
    s("edu_abitur.csv", "county", "2006-2024", "ags,year,pct_abitur",
      "% of school leavers", "Regionalatlas Deutschland, table AI003-2")

    flat_year(r("edu_no_hauptschulabschluss_2006_2024.json"), o("edu_no_hauptschulabschluss.csv"),
               "ags", "pct_no_hauptschulabschluss")
    s("edu_no_hauptschulabschluss.csv", "county", "2006-2024",
      "ags,year,pct_no_hauptschulabschluss", "% of school leavers",
      "Regionalatlas Deutschland, table AI003-2")

    flat_year(r("crime_hz_2020_2024.json"), o("crime_haeufigkeitszahl.csv"), "ags", "hz")
    s("crime_haeufigkeitszahl.csv", "county", "2020-2024", "ags,year,hz",
      "cases per 100,000 residents", "BKA Polizeiliche Kriminalstatistik, T01 Grundtabelle \"Kreise\"",
      "HZ = Haeufigkeitszahl, already a rate as published by the BKA")

    flat_year(r("bedarfsgemeinschaften_persons_2018_2024.json"), o("welfare_bedarfsgemeinschaften_persons.csv"),
               "ags", "persons")
    s("welfare_bedarfsgemeinschaften_persons.csv", "county", "2018-2024 (biennial: 2018/20/22/24)",
      "ags,year,persons", "count of people",
      "regionalstatistik.de, table 22811-02-02-4",
      "Persons in Bedarfsgemeinschaften (SGB II basic income support, Buergergeld/Hartz IV)")

    flat_year(r("business_registrations_2008_2025.json"), o("business_registrations_rate.csv"),
               "ags", "registrations_per_10k")
    s("business_registrations_rate.csv", "county", "2008-2025", "ags,year,registrations_per_10k",
      "new registrations per 10,000 residents", "Regionalatlas Deutschland, table AI004-1")

    flat_year(r("naturalization_rate_2011_2025.json"), o("naturalization_rate.csv"), "ags", "rate_pct")
    s("naturalization_rate.csv", "county", "2011-2025 (partial coverage)", "ags,year,rate_pct",
      "% of eligible foreign residents naturalized", "regionalstatistik.de, table 12511-04-01-4",
      "Einbuergerungsquote (BEV008Q)")

    flat_year(r("tax_revenue_capacity_2022_2024.json"), o("tax_revenue_capacity_total_eur.csv"),
               "ags", "total_eur")
    s("tax_revenue_capacity_total_eur.csv", "county", "2022-2024", "ags,year,total_eur",
      "EUR (total, not per resident)", "regionalstatistik.de, table 71231-01-03-4 (Realsteuervergleich)",
      "Steuereinnahmekraft - property tax + net business tax + municipal income/VAT shares, summed across the county")

    flat_year(r("religion_2001_2022.json"), o("church_membership_by_state.csv"), "state", "pct")
    s("church_membership_by_state.csv", "state", "2001-2022", "state,year,pct",
      "% of state population", "fowid.de, \"Bundeslaender: Kirchenmitglieder\" (EKD + Katholische Kirche)")

    flat_year(r("sports_membership_2017_2025.json"), o("sports_club_members_by_state.csv"), "state", "members")
    s("sports_club_members_by_state.csv", "state", "2017-2025", "state,year,members",
      "count of memberships (not unique people)", "DOSB Bestandserhebung 2025, p.17")

    flat_year(r("happiness_by_state.json"), o("life_satisfaction_by_state.csv"), "state", "score")
    s("life_satisfaction_by_state.csv", "state", "2019, 2021, 2024, 2025 (survey years only)",
      "state,year,score", "0-10 scale", "SKL Gluecksatlas 2025, Tabelle 1")

    flat_year(r("volunteering_by_state.json"), o("volunteering_rate_by_state.csv"), "state", "pct")
    s("volunteering_rate_by_state.csv", "state", "2019 only", "state,year,pct",
      "% of population 14+", "5. Deutscher Freiwilligensurvey 2019, Laenderbericht, p.137/148")

    nested_year_fields(r("life_expectancy_by_state.json"), o("life_expectancy_by_state.csv"),
                         "state", ["m", "f"])
    s("life_expectancy_by_state.csv", "state", "2023 only", "state,year,m,f",
      "years (life expectancy at birth)", "regionalstatistik.de, table 12613-06-01-4-B",
      "m/f = male/female period life expectancy at birth")

    nested_year_fields(r("gini_income_inequality_by_state.json"), o("income_inequality_by_state.csv"),
                         "state", ["gini", "s80s20"])
    s("income_inequality_by_state.csv", "state", "2021-2025", "state,year,gini,s80s20",
      "gini = 0-100 index; s80s20 = ratio", "regionalstatistik.de, table 12241-02-01 (EU-SILC)")

    nested_fields_flat(r("students_by_county_ws2023_24.json"), o("students_by_county.csv"),
                         "ags", ["total", "german", "foreign", "male", "female"], year="2023/24")
    s("students_by_county.csv", "county", "WS 2023/24 only", "ags,year,total,german,foreign,male,female",
      "count of enrolled students", "regionalstatistik.de, table 21311-01-01-4")

    nested_fields_flat(r("childcare_coverage_u3_2025.json"), o("childcare_coverage_under3.csv"),
                         "ags", ["rate", "count"], year="2025")
    s("childcare_coverage_under3.csv", "county", "2025 (Stichtag 01.03.)", "ags,year,rate,count",
      "rate = % of children under 3; count = children in care",
      "regionalstatistik.de, table 22543-03-01-4-B",
      "rate is the simple average of the three published single-year age bands (0-1,1-2,2-3), KINTE5=Insgesamt")

    flat_single(r("hospital_beds_2024.json"), o("hospital_beds.csv"), "ags", "beds", "2024")
    s("hospital_beds.csv", "county", "2024 (Stichtag 31.12.)", "ags,year,beds",
      "count, summed across all 15 Fachabteilungen",
      "regionalstatistik.de, table 23111-01-05-4-B", "aufgestellte Betten im Jahresdurchschnitt")

    flat_single(r("pkw_bestand_2026.json"), o("car_ownership.csv"), "ags", "cars", "2026")
    s("car_ownership.csv", "county", "2026 (Stichtag 01.01.)", "ags,year,cars",
      "count of registered passenger cars", "regionalstatistik.de, table 46251-01-03-4-B",
      "Personenkraftwagen insgesamt (commercial + private)")

    flat_year(r("renewable_electricity_share_by_state.json"), o("renewable_electricity_share_by_state.csv"),
               "state", "pct")
    s("renewable_electricity_share_by_state.csv", "state", "2009-2023", "state,year,pct",
      "% of gross electricity consumption (can exceed 100 in net-exporting states)",
      "regionalstatistik.de, table 86251-Z-02")

    flat_year(r("health_personnel_density_by_state.json"), o("health_personnel_density_by_state.csv"),
               "state", "per_1000")
    s("health_personnel_density_by_state.csv", "state", "2008, 2012, 2018, 2024", "state,year,per_1000",
      "health-sector employees per 1,000 residents", "regionalstatistik.de, table 88121-Z-03",
      "Geschlecht + Art der Einrichtung = Insgesamt")

    flat_single(r("tourism_overnight_stays_per_capita_2024.json"), o("tourism_overnight_stays_per_capita.csv"),
                 "ags", "stays_per_resident", "2024")
    s("tourism_overnight_stays_per_capita.csv", "county", "2024", "ags,year,stays_per_resident",
      "overnight stays per resident", "Regionalatlas Deutschland, table AI012 (\"Uebernachtungen je EW\")")

    flat_single(r("new_housing_completions_2024.json"), o("new_housing_completions.csv"), "ags", "dwellings", "2024")
    s("new_housing_completions.csv", "county", "2024", "ags,year,dwellings",
      "count of newly completed dwellings", "regionalstatistik.de, table 31121-01-02-4 (WOHN01, Insgesamt)")

    for orig in ["pks_2020.xlsx", "pks_2021.xlsx", "pks_2022.xlsx", "pks_2023.xlsx",
                 "pks_2024.xlsx", "pks_2024.csv", "ekd_2025.xlsx", "fowid_kirchenmitglieder.xlsx",
                 "dosb_2025.pdf", "freiwilligensurvey_laenderbericht.pdf"]:
        copy_original(r(orig), os.path.join(OUT_SOCIETY, "originals"))
    s("originals/pks_2020.xlsx ... pks_2024.csv", "county", "2020-2024",
      "(BKA original workbook, multiple sheets)", "-", "BKA Polizeiliche Kriminalstatistik (bka.de)",
      "Source workbooks behind crime_haeufigkeitszahl.csv - open directly in Excel")
    s("originals/ekd_2025.xlsx, fowid_kirchenmitglieder.xlsx", "state", "2001-2022",
      "(original workbooks)", "-", "fowid.de / EKD", "Source behind church_membership_by_state.csv")
    s("originals/dosb_2025.pdf", "state", "2025", "(PDF, p.17 table hand-extracted)", "-",
      "DOSB Bestandserhebung 2025", "Source document behind sports_club_members_by_state.csv")
    s("originals/freiwilligensurvey_laenderbericht.pdf", "state", "2019",
      "(PDF, p.137/148 tables hand-extracted)", "-", "5. Deutscher Freiwilligensurvey 2019, Laenderbericht",
      "Source document behind volunteering_rate_by_state.csv")

    write_csv(os.path.join(OUT_SOCIETY, "CODEBOOK.csv"),
              ["output_file", "geography", "years", "columns", "unit", "source", "notes"],
              [[c["output_file"], c["geography"], c["years"], c["columns"], c["unit"], c["source"], c["notes"]]
               for c in society_codebook])

    # ---------------- population_age (map-population-pyramid raw pulls) ----------------
    print("\nmap-population-pyramid ->", os.path.relpath(OUT_POP_AGE, ROOT))
    rp = lambda name: os.path.join(PYRAMID_RAW, name)
    op = lambda name: os.path.join(OUT_POP_AGE, name)

    for year in ["2011", "2014", "2017", "2020", "2023", "2025"]:
        pyramid_county_year(rp(f"population_by_age_sex_county_{year}.json"),
                              op(f"population_by_age_sex_county_{year}.csv"), year)
    p("population_by_age_sex_county_<year>.csv (6 files: 2011/14/17/20/23/25)", "county",
      "2011, 2014, 2017, 2020, 2023, 2025 (Stichtag 31.12.)", "ags,year,age_band,sex,count",
      "count of residents", "regionalstatistik.de, table 12411-09-01-4",
      "20 five-year age bands (0-4 ... 95+); long format, one row per county x band x sex")

    pyramid_state(rp("population_by_age_sex_state.json"), op("population_by_age_sex_state.csv"))
    p("population_by_age_sex_state.csv", "state", "2011, 2014, 2017, 2020, 2023, 2025 (Stichtag 31.12.)",
      "year,state,sex,age_band,count", "count of residents",
      "regionalstatistik.de, table 12411-04-02-4-B",
      "single-year-of-age bands (not 5-year), long format")

    write_csv(os.path.join(OUT_POP_AGE, "CODEBOOK.csv"),
              ["output_file", "geography", "years", "columns", "unit", "source", "notes"],
              [[c["output_file"], c["geography"], c["years"], c["columns"], c["unit"], c["source"], c["notes"]]
               for c in pop_age_codebook])

    print("\ndone.")


if __name__ == "__main__":
    main()
