"""
Downloader for the pieces that this sandbox's restricted network could NOT reach
(destatis.de, regionalstatistik.de, bbsr.bund.de, and similar are blocked at the
network level in the environment this dataset was built in). Run this from a normal
machine with unrestricted internet access.

Covers: full raw GERDA files (in case you want the un-selected ones, e.g. state_unharm,
mayoral elections, county council elections), and pointers to house-price and Zensus 2011
migration-background sources that need manual/portal retrieval.

Requires: requests
"""
import requests
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "raw_downloads"
OUT.mkdir(exist_ok=True)

GERDA_BASE = "https://media.githubusercontent.com/media/awiedem/german_election_data/main"

# Any file listed on https://www.german-elections.com/election-data/ can be fetched this
# way. Add/remove entries as you like - this is just what wasn't already pulled.
ADDITIONAL_GERDA_FILES = {
    "state_unharm.csv": "data/state_elections/final/state_unharm.csv",
    "mayoral_harm.csv": "data/mayoral_elections/final/mayoral_harm.csv",
    "mayoral_candidates.csv": "data/mayoral_elections/final/mayoral_candidates.csv",
    "county_elec_harm_21_cty.csv": "data/county_elections/final/county_elec_harm_21_cty.csv",
    "county_elec_harm_21_muni.csv": "data/county_elections/final/county_elec_harm_21_muni.csv",
    "county_council_seats.csv": "data/county_elections/final/county_council_seats.csv",
    "landrat_unharm.csv": "data/landrat_elections/final/landrat_unharm.csv",
    "ltw_wkr_unharm_long.csv": "data/state_elections/final/ltw_wkr_unharm_long.csv",
    "federal_muni_raw.csv": "data/federal_elections/municipality_level/final/federal_muni_raw.csv",
}

def fetch_gerda_extras():
    for name, path in ADDITIONAL_GERDA_FILES.items():
        url = f"{GERDA_BASE}/{path}"
        dest = OUT / name
        print(f"Downloading {name} ...")
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        dest.write_bytes(r.content)
        print(f"  -> {dest} ({len(r.content):,} bytes)")

def print_manual_sources():
    print("""
Not fetchable via a simple script - these need manual portal interaction or a paid
data source:

1. HOUSE PURCHASE PRICES (Bodenrichtwerte / transaction prices)
   - BORIS-D (federal portal, coverage varies by state): https://www.bodenrichtwerte-boris.de
   - Each state's own Gutachterausschuss (search "<Bundesland> Gutachterausschuss
     Grundstueckswerte") - most publish a Grundstuecksmarktbericht (property market
     report), often as PDF, sometimes with a downloadable table.
   - Private alternative with a public price index (not raw microdata):
     https://www.europace.de/en/research/epx/ or https://www.vdpresearch.de

2. ZENSUS 2011 migration background (for a 2011-vs-2022 comparison)
   - Portal: https://ergebnisse.zensus2011.de
   - Look for "Bevoelkerung nach Migrationshintergrund" at Gemeinde level; the portal
     has a table browser that exports CSV per query, no bulk download endpoint as of
     this writing.

3. INKAR itself, if you want variables beyond what's bundled in GERDA
   - https://www.inkar.de - browser-based, or via the R packages `bonn` / `inkaR` /
     `inkr` (search PyPI/CRAN by those names) which talk to INKAR's own data service.
""")

if __name__ == "__main__":
    fetch_gerda_extras()
    print_manual_sources()
