"""Builds the population-pyramid dataset from a regionalstatistik.de pull.

Raw file (data/raw/population_by_age_sex_state.json) was fetched by hand through
the regionalstatistik.de GENESIS web GUI, table 12411-04-02-4-B ("Bevoelkerung
nach Geschlecht und Altersjahren (79) - Stichtag 31.12. - regionale Ebenen"),
at the "Bundeslaender" resolution. It's a nested dict:
  {year: {state_name: {"m": {age_label: count}, "f": {age_label: count}}}}
covering 2011, 2014, 2017, 2020, 2023, 2025 (a representative subset of the
full 2011-2025 annual series - fetching every year requires a manual GUI
round trip per year, so these six were chosen to show the shape of the
demographic shift without an exhaustive pull).

Ages 0-74 are single years ("N bis unter N+1 Jahre" / "unter 1 Jahr"); 75+
already arrives pre-grouped as 75-79, 80-84, 85-89, and 90+. This script rolls
everything into standard 5-year bins (0-4, 5-9, ..., 85-89, 90+) - 19 bins,
the conventional population-pyramid format.

Also computes a "Deutschland" region by summing all 16 states, so the same
prepared file serves both the national pyramid and the per-state ones.
"""
import json
import re
from pathlib import Path

RAW = Path(__file__).resolve().parent / "data" / "raw" / "population_by_age_sex_state.json"
OUT = Path(__file__).resolve().parent / "data" / "prepared"

BIN_LABELS = [f"{i}-{i+4}" for i in range(0, 90, 5)] + ["90+"]
N_BINS = len(BIN_LABELS)


def bin_index(age_label):
    if age_label == "unter 1 Jahr":
        start = 0
    elif age_label == "90 Jahre und mehr":
        return N_BINS - 1
    else:
        m = re.match(r"(\d+) bis unter \d+ Jahre", age_label)
        start = int(m.group(1))
    return min(start // 5, N_BINS - 1)


def bin_ages(age_counts):
    bins = [0] * N_BINS
    for label, count in age_counts.items():
        if count is None:
            continue
        bins[bin_index(label)] += count
    return bins


def main():
    with open(RAW, encoding="utf-8") as f:
        raw = json.load(f)

    years = sorted(raw.keys())
    all_states = sorted({state for year_data in raw.values() for state in year_data})

    prepared = {"years": years, "bin_labels": BIN_LABELS, "regions": ["Deutschland"] + all_states, "data": {}}

    for year in years:
        year_data = raw[year]
        region_out = {}

        de_m = [0] * N_BINS
        de_f = [0] * N_BINS
        for state, sexes in year_data.items():
            m_bins = bin_ages(sexes["m"])
            f_bins = bin_ages(sexes["f"])
            region_out[state] = {"m": m_bins, "f": f_bins}
            de_m = [a + b for a, b in zip(de_m, m_bins)]
            de_f = [a + b for a, b in zip(de_f, f_bins)]
        region_out["Deutschland"] = {"m": de_m, "f": de_f}

        prepared["data"][year] = region_out

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "pyramid.json", "w", encoding="utf-8") as f:
        json.dump(prepared, f, ensure_ascii=False, separators=(",", ":"))

    print(f"years: {years}")
    print(f"regions: {len(prepared['regions'])}")
    de_2025 = prepared["data"][years[-1]]["Deutschland"]
    total = sum(de_2025["m"]) + sum(de_2025["f"])
    print(f"Deutschland {years[-1]} total: {total:,}")


if __name__ == "__main__":
    main()
