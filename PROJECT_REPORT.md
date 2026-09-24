# Germany in Maps — Project Report

*A plain-language summary of what this project is, what data it draws on, what it shows, and what's still missing. Written for personal reference, not as technical documentation — see `docs/` for that.*

---

## 1. Introduction

### What we started, and why

This project began as an effort to visualize German election results on maps — to make it possible to actually *see* how the country has voted since 1990, rather than just read tables of numbers. The starting question was simple: can we show, on a map, how a place voted, how that changed over time, and how it compares to its neighbors?

That grew in two directions. First, deeper into elections themselves — not just one map for one election, but swings between elections, a "rolling composite" that always shows each area's most recent vote, and time-series views for comparing specific places or parties across decades. Second, outward from elections into the *context* around them — who lives in these places, how old they are, what they earn, how they work, what their community life looks like — on the theory that a vote doesn't happen in a vacuum, and a map of results is more meaningful next to a map of the people casting them.

By the time of this report, the project has grown past being purely election-focused. It now includes general-purpose tools for exploring Germany's demographics and society on their own terms — an age pyramid, a tool to see where any given age group lives, and a tool for finding statistical relationships between any two of the roughly thirty social and economic indicators collected along the way.

### What kinds of tools exist

The project is a collection of standalone, self-contained web tools (no shared backend — each one loads its own pre-built data and runs entirely in the browser), plus a hub page that links them all together. They fall into a few recognizable shapes:

- **Maps.** A choropleth (color-coded-by-area) map of Germany, with a control panel to pick what's being shown, and usually a year slider to step through time. Some maps show a single election's raw results; others show *swings* between elections, or a "current standing" composite that blends every area's most recent vote into one always-up-to-date national picture.
- **Trend charts.** The same underlying numbers as the maps, but as line charts over time instead — built for comparing a handful of specific places or parties side by side, rather than seeing the whole country at once.
- **Special-purpose demographic tools.** A population pyramid (the classic age/sex bar-chart shape), a tool for picking any age range and sex and seeing where that group is concentrated across the country, and a scatterplot tool for exploring whether any two of the collected indicators move together.
- **Narrative "stories."** A separate, scroll-driven format — fourteen of them — that walks through a specific question (how the AfD's vote share changed over a decade, how one particular state's party landscape evolved, and so on) using the same underlying data as the interactive tools, but presented as a guided read rather than something to explore freely.

### What these tools visualize

Broadly, two families of subject matter sit side by side in this project: **political** (who won, by how much, how that's shifted over time, across every level of German election — federal, state, municipal, and European) and **demographic/economic/social** (age structure, income, employment, health, housing, crime, family life, civic participation, and more). The rest of this report goes through both in more detail — first the raw material behind them, then the tools built from it, then what's actually been learned, and finally an honest account of the boundaries of what this project can and can't say.

---

## 2. Data Mining and Data Sources — What We Looked For

This section lists, in plain terms, every kind of dataset that was sought out over the course of the project — both what was successfully found and folded in, and what turned out to be a dead end. Exact source names, web addresses, and technical table codes are deliberately left out of this section and collected in the References at the end, so this reads as a list of *subjects looked into*, not a citation list.

### What we found and used

- **Election results at every level** — national (Bundestag), state (Landtag), local council (Kommunalwahl), and European Parliament — going back as far as 1949 for national elections and 1990 for most others, down to individual constituencies and municipalities.
- **Population counts and age/sex breakdown**, both as a single national snapshot and as an animated series across several recent years, down to individual counties.
- **A 2022 national census** covering age groups, household size, foreign-born share, housing type, rent levels, and vacancy rates, for every municipality in the country.
- **Income data** — average wages, household income, purchasing power, and a measure of income inequality — at both county and state level.
- **Employment and unemployment figures**, including a general rate as well as youth-specific and long-term unemployment.
- **Business and economic-structure data** — what share of a local economy is agriculture vs. industry vs. services, how many small vs. large businesses exist locally, new business registrations, and local tax capacity.
- **Health-system data** — number of hospital beds, physicians and general practitioners per resident, and overall health-sector employment, by county and by state.
- **Childcare coverage** for children under three, by county.
- **Housing data** — new construction (completions), rent levels, and — as the closest available substitute for actual home-sale data (more on this below) — how much land for new building is being bought and sold, and at what price.
- **Car ownership** rates by county.
- **Renewable electricity's share** of total power use, by state.
- **Tourism intensity** (overnight stays relative to local population) by county.
- **Crime statistics** — a standard, officially-published crime rate — by county, across several recent years.
- **Family and civic-life indicators** — marriage and divorce rates, church membership, sports-club membership, volunteering rates, and a general well-being/life-satisfaction survey — mostly at the state level.
- **Migration-related figures** — foreign-national share of the population, in- and out-migration rates, a naturalization rate, the share of university students who are international, and a basic (though limited — see below) asylum-seeker count.
- **Education outcomes** — the share of school leavers earning a university-entrance qualification versus leaving with no qualification at all, by county over nearly twenty years.

### What we looked for but could not find, or deliberately did not chase down

- **A detailed breakdown of asylum seekers and refugees** — by nationality, age, sex, occupation, or the specific reason someone is in the country (asylum, work, study, family reunification) — was actively sought out. What exists in the data already collected is only a very coarse pair of numbers (asylum seekers as a share of the population, and as a share of the foreign population), and only up to a few years ago. A more detailed official statistical table was identified as existing and appearing to be current, but was never actually opened or fetched.
- **The full catalogue of a well-known regional indicator atlas** (roughly sixty indicators — rents, land prices, broadband and mobile coverage, electric-vehicle infrastructure, drive-time accessibility to various services, part-time work rates, and more) was identified early on as a promising resource, but was never systematically worked through; only a handful of individual indicators from it ended up being pulled in.
- **A breakdown of basic-income welfare recipients by gender and nationality** was attempted directly, but abandoned. The underlying government table exists, but encodes gender and nationality jointly in a way that isn't cleanly separable without much more reverse-engineering effort than seemed worthwhile relative to other priorities.
- **Council-seat allocations, as opposed to vote shares** (i.e., how many actual seats each party won in a local council, not just its share of the vote) were looked into as a way to show how voting systems translate votes into representation. The data turned out to exist for only a few hundred local councils, concentrated in a single state and a single election year — far too narrow to build anything general-purpose from, so this was set aside.
- **A time series of homeownership rates** was searched for directly and does not appear to exist as a public dataset at all — homeownership is only ever captured as a single snapshot at each national census, roughly once a decade, never as an annual series.
- **Actual home and apartment sale prices and transaction volumes** (as opposed to rent, or as opposed to land-for-construction sales) were also searched for and confirmed not to exist as one free, unified, nationwide dataset. Germany handles this through roughly 380 independent regional committees, each publishing independently and sometimes only through paid access — there is no single free source. Land (as opposed to housing) transaction data *was* found and used as the closest available substitute.
- **Migration background (i.e., having a family history of immigration, not just current citizenship) as a multi-year trend** was identified as theoretically possible (the same question was asked in both the 2011 and 2022 national censuses), but a ready-to-use 2011 file was never located or pulled in; only the 2022 snapshot made it into the project.
- **Anything below municipality level** (e.g., individual polling stations or neighborhoods) was confirmed to not exist publicly for demographic data, by design — German privacy rules on small-area statistics prevent it.
- **Any dataset that would let a specific demographic group's actual vote choice be directly observed** (e.g., "how did people over 65 vote") does not exist and cannot exist from public data, due to ballot secrecy. The closest official approximation is a separate, sampled survey product that was identified but not pulled into this project.
- A handful of already-downloaded but never-used files sat unexplored for a long stretch of the project: some detailed local employment and land-area/population-density figures, and roughly forty additional detailed economic indicators (business turnover figures, job vacancies and employment broken out by skill level, and similar) that were bundled together with other data early on but judged, at the time, too narrow, too incomplete, or too redundant with what was already included, and simply never revisited. A pass through these during this reporting cycle recovered two of them (the youth- and long-term-unemployment figures) into an actual visualization.

---

## 3. Overview of the Data

Stepping back from the list above, the data behind this project falls into a small number of broad families:

1. **Elections.** Real, certified vote counts (not estimates or polling) for federal, state, municipal, and European elections, at multiple geographic resolutions, spanning as far back as 1949 for some series and 1990 for most others, up through 2026.
2. **Population and demographics.** How many people live where, broken down by age and sex, both as an animated multi-year series and as a detailed one-time census snapshot that adds household and housing detail.
3. **Economy and labor.** Income, unemployment (including youth and long-term breakdowns), business structure, and local tax capacity.
4. **Health and childcare.** Hospital and doctor availability, and under-three childcare coverage.
5. **Housing and land.** Rent, new construction, and land-purchase activity and pricing.
6. **Society and civic life.** Crime, marriage and divorce, religious and sports-club membership, volunteering, and general life satisfaction.
7. **Migration.** Foreign-national presence, naturalization, and a limited view of asylum-related figures.

Almost everything above is organized around Germany's roughly 400 counties or its sixteen states, since that's the finest level at which most of this kind of data is legally allowed to be published. The election data goes considerably finer — down to individual municipalities and constituencies — because vote counts aren't subject to the same small-area privacy restrictions as demographic data. A few indicators (religion, sports, life satisfaction, volunteering, and several economic ones) exist *only* at the state level, meaning every county within a state currently shows the same number for those specific indicators — a real limitation of the underlying source, not a shortcut taken in building the tools.

Time coverage is uneven by design: elections and a handful of economic series go back decades; most social and demographic indicators cover roughly the last five to twenty years; a few (childcare, hospital beds, car ownership, tourism, new housing, land sales, and the census itself) exist only as a single recent snapshot, with no earlier history pulled in.

---

## 4. Overview of Visualizations

### Political

- **Maps.** A federal-constituency results map; an all-in-one municipality map covering all four election types; a swing map showing gains/losses/flips between consecutive elections; and a "current standing" composite map that shows every area at its own most recent election, so the whole country always reads as up-to-date even though different areas last voted in different years.
- **Trend charts.** A time-series tool for comparing specific places' or parties' vote share and turnout across elections; a "blended profile" tool that combines all four election types into one picture of how a place tends to vote generally; and a trend-line version of the "current standing" composite.

### Demographic, economic, and social

- **Maps.** A general demographics & economy map (census and income/labor-market indicators); a "Society & Culture" map covering the family/crime/welfare/economic-structure/health/housing/migration indicators described above.
- **Trend chart.** A time-series comparison tool for the same demographic and economic indicators.

### Standalone / special-purpose tools

These don't fit neatly into "map" or "trend chart":

- **Population Pyramid** — the classic age-by-sex bar chart, animated across several census years, for the whole country or any single state.
- **Population by Age Group** — pick any age range and sex (for example, "women 30 to 50") and see, as a map, exactly where in the country that group is concentrated, either as a raw headcount or as a share of each area's population.
- **Correlation Explorer** — pick any two of the roughly thirty collected indicators and see a scatterplot of how they relate to each other across every county, along with a statistical correlation measure.

### Narrative stories

Fourteen scroll-driven pieces that walk through a specific storyline using the underlying election data — a primer on how to read the maps, a look at the AfD's rise over more than a decade, and individual deep-dives into several states' political histories, plus one piece specifically about the relationship between income and voting patterns.

---

## 5. Findings and Open Questions

### Things the data actually shows

- **Childcare coverage for children under three is sharply divided between the former East and West Germany** — commonly in the 50–63% range in the East versus 20–35% in the West — a pattern that traces back to very different childcare infrastructure built up before reunification.
- **Youth unemployment follows a similar East/West divide**, running higher in the East.
- **Long-term unemployment does the opposite.** Bavaria, which has very low unemployment overall, has the *highest* share of its (small number of) unemployed residents who've been out of work for over a year — a "composition" effect: where overall unemployment is low, what remains tends to be the harder, more entrenched cases.
- **Welfare receipt and the local crime rate move together fairly strongly** across counties — not proof that one causes the other, but a real, measurable statistical relationship.
- **Counties with a larger share of young children tend to have *lower* childcare coverage rates**, not higher — suggesting demand is outpacing the supply of childcare slots precisely where it's needed most.
- **Renewable electricity's share of consumption varies enormously by state** and isn't obviously related to the local crime rate or other social indicators tested so far — some sparsely-populated, wind-heavy states generate far more renewable electricity than they use themselves and technically exceed 100% of local consumption.
- **Health-sector employment has grown steadily in every state since 2008**, without exception.
- **Land prices for new construction are dramatically higher in and around major cities** (Munich and Berlin stand out clearly) than in rural areas, unsurprisingly, but the scale of the gap is large — multiple orders of magnitude in some comparisons.

### Questions this project's data could plausibly answer, but hasn't yet

- Does an area's economic profile (income, unemployment, business structure) relate to how it votes, and has that relationship changed over time? The election data and the demographic/economic data are both organized by the same county boundaries, so this is a matter of connecting two datasets that already exist in the project — not fetching anything new.
- Do areas with higher welfare receipt or higher long-term unemployment show different voting patterns than similar-income areas with more short-term/frictional unemployment?
- Is new housing construction or land-price growth concentrated in areas that are also gaining population, or is it happening independently of population trends?
- Do the East/West divides visible in childcare, unemployment type, and other social indicators line up with, or diverge from, the East/West divides already well-documented in voting behavior?

### Questions this project cannot answer, even in principle, with more data

- **How did any specific group of people actually vote** (by age, income, religion, or any other individual trait). German ballot secrecy makes this structurally unknowable from public data — any area-level correlation between, say, age and vote share only shows that the two things *co-occur* in the same places, never that older individuals actually voted a particular way.
- **What a specific individual home would sell for**, or how many homes changed hands in a given place — this level of detail isn't collected in any free, unified way anywhere in Germany.
- **Why a specific person sought asylum**, or what happened to any individual case — this project only ever works with aggregated area-level counts, never individual records, both by design and by law.

### Questions that would become answerable with more data-gathering effort (not fundamentally blocked, just not done yet)

- A full breakdown of refugees and asylum seekers by nationality, age, sex, and legal basis for being in the country — a specific, promising official data table for this was identified but never opened.
- The full ~60-indicator regional atlas mentioned above, which likely contains several more usable indicators beyond the handful already pulled in.
- Nationwide, multi-year council-seat data, to properly study how votes translate into representation (the small sample currently available isn't enough to generalize from).
- A second census-based snapshot of migration background (from the 2011 census) to allow a two-point-in-time comparison against the 2022 figure already in hand.

---

## 6. Every Source Investigated

The table below lists every place looked into for data during this project, whether or not it ultimately contributed anything, along with what kind of organization it is, what was found there, and how the data was actually obtained.

| Source | Type of organization | What was found | How it was obtained | Outcome |
|---|---|---|---|---|
| GERDA (German Election Database) | Academic research project, publishing official government election results | Federal, state, municipal, and European election results, 1949–2026, at every geographic level | Downloaded as ready-made data files from the project's public code repository | **Used** — the backbone of every election map and trend tool |
| Zeit Online historical constituency project | News organization / civic-data project | Federal election results 1949–2001, hand-matched to modern constituency boundaries | Downloaded as a data file from the project's public code repository | **Used**, with an explicit caveat that its geography is approximate for the earliest years |
| INKAR | Federal spatial-planning research institute | A wide range of county-level economic, labor-market, health, housing, and business indicators, most running from the mid-1990s to early 2020s | Bundled data extract, downloaded as ready-made files | **Used** — a large share of the demographic/economic map's indicators come from here |
| National census (2022) | Federal statistical system | A single detailed snapshot of every municipality's age structure, household composition, and housing situation | Bundled data extract, downloaded as a ready-made file | **Used** — the municipality-level demographics map |
| Joint federal/state regional statistics database (an online table-browsing tool run by Germany's statistical offices) | Government (joint federal/state statistical offices) | Dozens of individual tables: population by age and sex, marriages, divorces, education outcomes, welfare receipt, new business registrations, life expectancy, local tax capacity, income inequality, naturalization, student counts, childcare coverage, hospital beds, car ownership, renewable electricity share, tourism, new housing, and building-land sales | Manually navigated through the tool's web interface (selecting the right table, time period, and geographic level each time) and downloaded as a structured data export | **Used extensively** — the single largest source of new data added to the project |
| Federal Criminal Police Office's official crime statistics | Government (federal police agency) | An official, published crime rate by county, several recent years | Downloaded as spreadsheet files | **Used** — the crime-rate indicator |
| German Olympic Sports Confederation | Non-governmental sports federation | Sports-club membership counts by state | Read from a published report and manually copied out | **Used** — the sports-club-membership indicator |
| A research group studying religious affiliation, using official church membership records | Non-governmental research organization, sourcing from church administrative records | Combined Protestant and Catholic church membership by state, over two decades | Downloaded as a spreadsheet file | **Used** — the church-membership indicator |
| A large nationally-representative volunteering survey | Government-commissioned survey (results published as an official state report) | The share of the population who do formal volunteer work, by state, for one survey year | Read from a published report and manually copied out | **Used** — the volunteering-rate indicator |
| An annual national well-being/life-satisfaction survey and report | Privately-sponsored, professionally-run survey | Self-reported life satisfaction by state, for a handful of survey years | Read from a published article/table | **Used** — the life-satisfaction indicator |
| Asylum/refugee statistics table (identified but not opened) | Government (same regional statistics database as above) | Unknown — appeared current, with a specific table reference | Not attempted | **Not used** — a real, promising lead left unexplored |
| Regional indicator atlas (~60 indicators) | Government (federal spatial-planning institute, same as INKAR) | A broad catalogue of local indicators — housing costs, connectivity, service accessibility, and more | A handful of individual indicators were pulled from it the same way as the general statistics database above; the rest was never worked through | **Partially used** — only a few of ~60 available indicators were ever pulled in |
| Welfare-recipient breakdown by gender/nationality | Government (same regional statistics database) | A table exists, but its structure encodes gender and nationality jointly in a way that's not cleanly separable | Attempted, then abandoned as not worth the reverse-engineering effort | **Not used** |
| Local council seat-allocation data | Bundled within the GERDA election dataset described above | Seat counts (as opposed to vote shares) for local councils | Already present in a downloaded data file | **Not used** — coverage turned out to be limited to a few hundred councils in one state, one year |
| Homeownership rate over time | Searched directly in the government statistics database described above | Confirmed not to exist as an annual series — only a once-a-decade census snapshot exists | Searched exhaustively, nothing found beyond the existing census snapshot | **Does not exist as public data** |
| Home/apartment sale prices and transaction counts | Regional expert appraisal committees (~380 independent government bodies) and/or private real-estate data vendors | Confirmed not to exist as one free, unified national dataset | Researched; land-purchase data (a related but distinct dataset) was found and used instead | **Does not exist as free public data**; a substitute (land sales) was used |
| 2011 census migration-background data | Government statistical portal | A second historical data point for migration background, in principle | Identified as existing but never actually downloaded | **Not used** |
| Sampled survey linking vote choice to age/gender | Government (Federal Returning Officer) | A separate, official survey product that comes closest to answering "who voted for whom" | Identified as existing; not pulled into this project | **Not used** |
| Assorted detailed local employment/population-density files | Government (regional statistics database, bundled early in the project) | Detailed local employment-by-sector and land-area/population-density figures | Already downloaded, in a ready-made file | **Not used** — never incorporated into any tool |
| ~44 additional detailed economic indicators | Same federal spatial-planning institute as INKAR above | Business turnover, job vacancies and employment by skill level, and similar detailed figures | Already downloaded, bundled with other INKAR data | **Not used** — judged too narrow or redundant at the time; two related figures (youth- and long-term-unemployment) were separately recovered into an actual visualization |

---

## 7. References

*Grouped by the section of the report they're relevant to. This is the only place in the report where exact source names, organizations, and technical identifiers appear.*

**Elections**
- GERDA — The German Election Database. Heddesheimer, V., Hilbig, H., Sichart, F., & Wiedemann, A. (2025). *Scientific Data*, 12, 618. Repository: github.com/awiedem/german_election_data
- Zeit Online historical Bundestag constituency data: github.com/ZeitOnline/bundestagswahl-historische-wahlkreis-daten

**Economic and social indicators**
- INKAR (Indikatoren und Karten zur Raum- und Stadtentwicklung), Bundesinstitut für Bau-, Stadt- und Raumforschung (BBSR): inkar.de
- Zensus 2022 (German federal census)
- Regionalstatistik.de (Regionaldatenbank Deutschland), the joint database of Germany's federal and state statistical offices, used for: population by age/sex (table 12411 family), marriages (12611), divorces (12631), education outcomes / Regionalatlas (AI003-2), welfare receipt / Bedarfsgemeinschaften (22811-02-02-4), new business registrations / Regionalatlas (AI004-1), life expectancy (12613-06-01-4-B), tax revenue capacity (71231-01-03-4), income inequality / EU-SILC (12241-02-01), naturalization rate (12511-04-01-4), student counts (21311-01-01-4), childcare coverage (22543-03-01-4-B), hospital beds (23111-01-05-4-B), health personnel density (88121-Z-03), car ownership (46251-01-03-4-B), renewable electricity share (86251-Z-02), tourism intensity / Regionalatlas (AI012), new housing completions (31121-01-02-4), and building-land sales (61511-01-03-4-B)
- Bundeskriminalamt (BKA), Polizeiliche Kriminalstatistik, Grundtabelle "Kreise"
- Deutscher Olympischer Sportbund (DOSB), Bestandserhebung 2025
- fowid.de (Forschungsgruppe Weltanschauungen in Deutschland); Evangelische Kirche in Deutschland (EKD) membership statistics
- 5. Deutscher Freiwilligensurvey 2019, Länderbericht
- SKL Glücksatlas 2025; underlying survey work by IfD Allensbach

**Identified but not pulled in**
- Regionalstatistik.de table 12531, "Statistik zu Schutzsuchenden" (asylum/protection-seeker statistics)
- Deutschlandatlas (BBSR / Bundesministerium des Innern), full ~61-indicator catalogue
- Regionalstatistik.de table 22811-02-02-4 value-variable structure (welfare recipients by gender/nationality — encoding not resolved)
- Bundeswahlleiterin, repräsentative Wahlstatistik (sampled ballot-based demographic survey)
- Zensus 2011 (ergebnisse.zensus2011.de) — migration-background time-series candidate
- BORIS-D (bodenrichtwerte-boris.de) and individual regional Gutachterausschüsse — home/land value reference portals with inconsistent national coverage

**Geographic boundaries** (used to draw the maps, not analytical data in their own right)
- BKG (Bundesamt für Kartographie und Geodäsie), VG250 administrative boundaries
- m-ad/geofeatures-ags-germany (community-maintained county boundary geometry)

---

*End of report. For technical detail on any dataset's exact structure, coverage, or caveats, see `docs/SOURCES.md` and `docs/GAPS_AND_LIMITATIONS.md` in the project repository.*
