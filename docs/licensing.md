# Licensing and terms of use

What we may do with each source, what it obliges us to do, and under which terms we
publish our own outputs. Checked on **2026-10-12**; the providers of the models added on
2026-10-15 (ECCC, JMA, CMA, NOAA AIGFS, KNMI, DMI) and the ČHMÚ radar data on that day. This
is a summary for the project, not legal advice.

## Sources

| Source | Licence | Evidence | Obligations for us |
|---|---|---|---|
| ČHMÚ station observations and metadata (opendata.chmi.cz) | CC BY 4.0 | National Open Data Catalogue (data.gov.cz), e.g. "Meteorologická data měřená v síti stanic ČHMÚ za aktuální rok v intervalu 1 hodina" and "Aktuální meteorologická data … v intervalu 10 minut a 1 hodina": `autorské-dílo` and `databáze-jako-autorské-dílo` = CC BY 4.0, author ČHMÚ | credit ČHMÚ, link the licence, say what we changed |
| ČHMÚ ALADIN forecasts (opendata.chmi.cz/meteorology/weather/nwp_aladin) | CC BY 4.0 | National Open Data Catalogue: "Numerické předpovědi počasí modelu ALADIN/ČHMÚ" and its two product datasets (oblast ČR, projekce Lambert) | same as above |
| ČHMÚ weather radar composites (opendata.chmi.cz/meteorology/weather/radar) | CC BY 4.0 | National Open Data Catalogue, checked 2026-10-15: "Radarová data ČHMÚ", "Sloučená informace maximální radarové odrazivosti MAX_Z pro území Česka", the PseudoCAPPI_2km, ECHO_TOP and MERGE datasets and both "Extrapolační předpověď …" datasets | credit ČHMÚ on the radar page and in the release notes, link the licence, say what we changed (packing per day, cropped PNG frames, station extraction) |
| Open-Meteo API (all other forecasts, and ALADIN as served by Open-Meteo): Forecast, Previous Runs and Single Runs APIs | CC BY 4.0 | open-meteo.com/en/licence, /en/terms | credit Open-Meteo with a link **next to every place the data is shown**; free tier only for **non-commercial** use and under 600 calls/min, 5,000/hour, 10,000/day and 300,000/month, shared by all our workflows |
| UK Met Office models via Open-Meteo | **CC BY-SA 4.0** | open-meteo.com/en/licence | credit; anything we publish that is derived from it must be shared under CC BY-SA 4.0 (ShareAlike) |
| DWD (ICON-D2, ICON-EU, ICON global), ECMWF (IFS, AIFS), KNMI, DMI via Open-Meteo | CC BY 4.0 | open-meteo.com/en/licence (KNMI and DMI link CC BY 4.0) | credit the provider |
| NOAA NCEP (GFS, AIGFS) via Open-Meteo | US government work, no restrictions | open-meteo.com/en/licence (links weather.gov/disclaimer) | credit as courtesy |
| Météo-France (ARPEGE Europe and World) via Open-Meteo | Licence Ouverte 2.0 (Etalab), compatible with CC BY | data.gouv.fr datasets "Paquets Arpège", licence `lov2` | credit Météo-France |
| ECCC / Canadian Meteorological Centre (GEM Global) via Open-Meteo | Environment and Climate Change Canada Data Servers End-use Licence: worldwide, royalty-free, perpetual, commercial use allowed | open-meteo.com/en/licence links eccc-msc.github.io/open-data/licence/readme_en/ (read 2026-10-15) | attribution "Data Source: Environment and Climate Change Canada" (or "Contains information licenced under the Data Server End-use Licence of Environment and Climate Change Canada") with a link to the licence where possible; no suggestion of official status or endorsement |
| Japan Meteorological Agency (GSM) via Open-Meteo | JMA Terms of Use (Public Data License 1.0), which JMA states are **compatible with CC BY 4.0** (content may be used under CC BY 4.0 instead) | open-meteo.com/en/licence links jma.go.jp/jma/en/copyright.html (read 2026-10-15) | cite the source ("Source: Japan Meteorological Agency"), say that it was edited, and do not present edited data as made by the Government of Japan. **Unclear:** the terms are written for JMA's website content; whether they also govern the GSM model data Open-Meteo redistributes is not stated, and third-party rights are the user's to check |
| China Meteorological Administration (GRAPES) via Open-Meteo | CC BY 4.0 **as stated by Open-Meteo** | open-meteo.com/en/licence links only the CC BY 4.0 text, no CMA document | credit CMA. **Unclear:** we found no licence statement by CMA itself for this data; Open-Meteo's statement is the only evidence |
| GeoSphere Austria (AROME) via Open-Meteo | CC BY 4.0 | GeoSphere Data Hub, dataset `nwp-v1-1h-2500m` | credit GeoSphere Austria (not listed on Open-Meteo's licence page) |
| Kraj and okres boundaries (ČÚZK) | CC BY 4.0 | cuzk.gov.cz, "Otevřená data – základní informace"; converted by siwekm/czech-geojson (CC BY 4.0) | credit ČÚZK and the converter |

## What we publish, and under which licence

| Output | Where | Licence |
|---|---|---|
| Code | this repository | MIT |
| ALADIN station archive (`aladin-YYYY-MM` releases) | GitHub Release assets | CC BY 4.0, derived from ČHMÚ data only; release notes credit ČHMÚ and list our changes |
| Radar archive (`radar-YYYY-MM` releases) and live frames (branch `radar-live`) | GitHub Release assets, a git branch | CC BY 4.0, derived from ČHMÚ data only; release notes and the branch README credit ČHMÚ and list our changes |
| Single model runs at ~100 stations (`runs-YYYY-MM` releases) | GitHub Release assets | **CC BY-SA 4.0** (includes UK Met Office data); release notes credit Open-Meteo and the providers |
| Scores, rankings, web map, open data | repository and GitHub Pages | **CC BY-SA 4.0**: they combine all sources, including UK Met Office data (ShareAlike). CC BY 4.0 inputs may be included in CC BY-SA 4.0 work. |

Publishing these outputs openly is allowed: every source permits redistribution and
adaptation with attribution. Keeping them private would not change any obligation
below, and public data is the point of the project.

## Rules for the project

1. **Non-commercial.** The free Open-Meteo API may only be used for non-commercial
   purposes (no ads, no subscriptions, no commercial products; see their terms). If the
   project or its results are used commercially, an Open-Meteo API subscription
   (Professional for the Previous Runs API) is required. The Single Runs API
   (`mvd fetch-runs`, run-by-run verification of every model) is used on the same free,
   non-commercial tier without an API key; the page that shows it says so.
2. **Attribution everywhere data is shown:** README, web map and release notes credit
   Open-Meteo (with link), ČHMÚ, the model providers (since 2026-10-15 also
   Environment and Climate Change Canada, the Japan Meteorological Agency and the China
   Meteorological Administration) and ČÚZK, link the licences, and say that values were
   processed (station extraction, unit conversion, scoring).
3. **Respect rate limits:** batch locations, request 14-day windows (same cost as one
   day), back off on HTTP 429. The free tier allows 300,000 calls a month, so a full
   backfill of all stations takes months and must be spread out (roadmap 2.6). All
   workflows together stay below the daily and the monthly limit: outlook ≤ 1,600, the
   newest single runs 3,400 and 4,500 shared by the backfill and the histories a day,
   ≤ 294,500 in a 31-day month ([budget](data-sources.md#open-meteo-budget)); the single
   runs ask about 100 stations, not all ~500, to fit, and no request weighs more than 500
   (the limit is 600 a minute).
4. **The forecast page** (`forecast.html`, roadmap 6.3) asks the Open-Meteo Forecast
   API from each visitor's browser, one request per okres shown, so each visitor uses
   their own free-tier allowance; the page credits Open-Meteo and the model providers
   like the map. It stays non-commercial under rule 1. The TV-style map reads
   `outlook.json`, made twice a day for all okresy (about 420 calls with 11 weighted
   models, 732 with all 19, in at most two requests).
5. **Open data files** (`api/v1/`, roadmap 6.11) carry the licence (CC BY-SA 4.0) and
   the attribution text in every file; they are derived data (combined forecasts,
   scores), not a redistribution of the raw Open-Meteo API.
6. **Do not imply endorsement** by ČHMÚ, Open-Meteo or any model provider.
7. **GitHub:** data files live in Release assets (≤ 2 GiB each), not in git history.
   The scheduled workflows are this project's data pipeline, which GitHub Actions
   allows.
