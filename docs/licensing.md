# Licensing and terms of use

What we may do with each source, what it obliges us to do, and under which terms we
publish our own outputs. Checked on **2026-10-12**. This is a summary for the project,
not legal advice.

## Sources

| Source | Licence | Evidence | Obligations for us |
|---|---|---|---|
| ČHMÚ station observations and metadata (opendata.chmi.cz) | CC BY 4.0 | National Open Data Catalogue (data.gov.cz), e.g. "Meteorologická data měřená v síti stanic ČHMÚ za aktuální rok v intervalu 1 hodina" and "Aktuální meteorologická data … v intervalu 10 minut a 1 hodina": `autorské-dílo` and `databáze-jako-autorské-dílo` = CC BY 4.0, author ČHMÚ | credit ČHMÚ, link the licence, say what we changed |
| ČHMÚ ALADIN forecasts (opendata.chmi.cz/meteorology/weather/nwp_aladin) | CC BY 4.0 | National Open Data Catalogue: "Numerické předpovědi počasí modelu ALADIN/ČHMÚ" and its two product datasets (oblast ČR, projekce Lambert) | same as above |
| Open-Meteo API (all other forecasts, and ALADIN as served by Open-Meteo) | CC BY 4.0 | open-meteo.com/en/licence, /en/terms | credit Open-Meteo with a link **next to every place the data is shown**; free tier only for **non-commercial** use and under 600 calls/min, 5,000/hour, 10,000/day and 300,000/month |
| UK Met Office models via Open-Meteo | **CC BY-SA 4.0** | open-meteo.com/en/licence | credit; anything we publish that is derived from it must be shared under CC BY-SA 4.0 (ShareAlike) |
| DWD (ICON), ECMWF (IFS, AIFS), KNMI, DMI via Open-Meteo | CC BY 4.0 | open-meteo.com/en/licence | credit the provider |
| NOAA NCEP (GFS) via Open-Meteo | US government work, no restrictions | open-meteo.com/en/licence | credit as courtesy |
| Météo-France (ARPEGE) via Open-Meteo | Licence Ouverte 2.0 (Etalab), compatible with CC BY | data.gouv.fr datasets "Paquets Arpège", licence `lov2` | credit Météo-France |
| GeoSphere Austria (AROME) via Open-Meteo | CC BY 4.0 | GeoSphere Data Hub, dataset `nwp-v1-1h-2500m` | credit GeoSphere Austria (not listed on Open-Meteo's licence page) |
| Kraj and okres boundaries (ČÚZK) | CC BY 4.0 | cuzk.gov.cz, "Otevřená data – základní informace"; converted by siwekm/czech-geojson (CC BY 4.0) | credit ČÚZK and the converter |

## What we publish, and under which licence

| Output | Where | Licence |
|---|---|---|
| Code | this repository | MIT |
| ALADIN station archive (`aladin-YYYY-MM` releases) | GitHub Release assets | CC BY 4.0, derived from ČHMÚ data only; release notes credit ČHMÚ and list our changes |
| Scores, rankings, README leaderboard, web map | repository and GitHub Pages | **CC BY-SA 4.0**: they combine all sources, including UK Met Office data (ShareAlike). CC BY 4.0 inputs may be included in CC BY-SA 4.0 work. |

Publishing these outputs openly is allowed: every source permits redistribution and
adaptation with attribution. Keeping them private would not change any obligation
below, and public data is the point of the project.

## Rules for the project

1. **Non-commercial.** The free Open-Meteo API may only be used for non-commercial
   purposes (no ads, no subscriptions, no commercial products; see their terms). If the
   project or its results are used commercially, an Open-Meteo API subscription
   (Professional for the Previous Runs API) is required.
2. **Attribution everywhere data is shown:** README, web map and release notes credit
   Open-Meteo (with link), ČHMÚ, the model providers and ČÚZK, link the licences, and
   say that values were processed (station extraction, unit conversion, scoring).
3. **Respect rate limits:** batch locations, request 14-day windows (same cost as one
   day), back off on HTTP 429. The free tier allows 300,000 calls a month, so a full
   backfill of all stations takes months and must be spread out (roadmap 2.6).
4. **The forecast page** (`forecast.html`, roadmap 6.3) asks the Open-Meteo Forecast
   API from each visitor's browser, one request per okres shown, so each visitor uses
   their own free-tier allowance; the page credits Open-Meteo and the model providers
   like the map. It stays non-commercial under rule 1. The TV-style map reads
   `outlook.json`, made twice a day by one request for all okresy (about 340 calls).
5. **Do not imply endorsement** by ČHMÚ, Open-Meteo or any model provider.
6. **GitHub:** data files live in Release assets (≤ 2 GiB each), not in git history.
   The scheduled workflows are this project's data pipeline, which GitHub Actions
   allows.
