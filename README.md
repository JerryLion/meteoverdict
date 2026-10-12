# meteoverdict 🐸

[![CI](https://github.com/JerryLion/meteoverdict/actions/workflows/ci.yml/badge.svg)](https://github.com/JerryLion/meteoverdict/actions/workflows/ci.yml)
[![Last updated](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FJerryLion%2Fmeteoverdict%2Fmain%2Fsite%2Fdata%2Fbadge.json)](https://github.com/JerryLion/meteoverdict/actions/workflows/daily.yml)

**Which weather model gets Czechia right?**
Daily verification of ALADIN, ICON, ECMWF, GFS & more against ČHMÚ station observations, with a per-region leaderboard and map.

**Forecast map:** [tv.html](https://jerrylion.github.io/meteoverdict/tv.html) ·
**score map:** [jerrylion.github.io/meteoverdict](https://jerrylion.github.io/meteoverdict/) ·
**model comparison:** [compare.html](https://jerrylion.github.io/meteoverdict/compare.html) ·
**detailed forecast per okres:** [forecast.html](https://jerrylion.github.io/meteoverdict/forecast.html)

> 🚧 Early development. See [ROADMAP.md](ROADMAP.md) for the architecture and plan.

## Status

- **Works today:** the whole pipeline. Station table with okres, kraj and elevation
  class (782 stations); hourly ČHMÚ observations (~470 automatic stations) and daily
  totals of the ~280 manual rain gauges, scored over ČHMÚ's 06–06 UTC climatological
  day; forecasts of 11 models from Open-Meteo at D+1…D+5 (archive starts and lead days
  measured live); pairing at each model's native time resolution; additive daily scores
  (with hit rates for wet, ≥ 5 mm and heavy ≥ 20 mm days, and for heat days ≥ 30 °C);
  aggregates per station, okres, kraj, elevation class and Czechia with bootstrap
  confidence intervals; the leaderboard below and JSON for the web map; a mean of all
  models as a baseline that every model has to beat.
- **Running automatically:** ALADIN runs are archived every 3 hours (ČHMÚ keeps them 3
  days); the backfill fills the history since 2024, stations and rain gauges, newest
  first within the free Open-Meteo quota (about two months in total); the daily workflow
  captures observations, re-scores, and updates this README every morning.
- **Not yet:** the first real results (12 Oct 2026) cover late September only; the
  leaderboard fills as the backfill and ČHMÚ's monthly publication of checked
  observations progress. ALADIN has forecast history only from June 2026.
- **Data quality:** implausible observations are dropped; stale data or many silent
  stations make the daily run fail loudly instead of publishing an outdated table
  (`mvd check`).
- **Freshness:** the "last updated" badge above and a line under the leaderboard show
  when the daily run last updated the table and how recent the scores are.
- **Web map:** regions and stations coloured by the best model, controls for variable,
  lead time and period, per-station error charts, a model comparison page, in Czech and
  English, live at [jerrylion.github.io/meteoverdict](https://jerrylion.github.io/meteoverdict/)
  and updated after every daily run.
- **Every okres ranked:** okresy with fewer than three stations borrow the nearest
  stations of their neighbours (up to 30 km beyond the border), so the map has no grey
  "too few stations" okresy left.
- **Forecast map:** the [TV-style map](https://jerrylion.github.io/meteoverdict/tv.html)
  shows our combined forecast for every okres for six days, by night, morning,
  afternoon and evening: weather symbols, temperature, chance of rain, wind and cloud
  layers, a "play" button, and a panel per okres; refreshed twice a day.
- **Own forecast:** the [forecast page](https://jerrylion.github.io/meteoverdict/forecast.html)
  shows, for a chosen okres, the next six days combined from all models, each weighted
  and bias-corrected by how well it did there over the last 90 days, next to the best
  single model ([method](docs/methodology.md#our-own-forecast-roadmap-62-63)). The
  approach follows operational consensus forecasts (Bureau of Meteorology, NOAA's
  National Blend of Models; [review](docs/forecast-research.md)); not yet verified to
  beat the best model (roadmap 6.4).
- **Upstream:** wetterdienst already reads ČHMÚ data, but only closed years; what we
  learned about the current-year files could fill that gap
  ([docs/upstream.md](docs/upstream.md)).
- **Next:** checking the combined forecast against the best single model (roadmap 6.4); results fill in as the backfill progresses (each run's
  progress is on its workflow page); then a write-up of the findings (roadmap 5.6).
  See [ROADMAP.md](ROADMAP.md).

## Leaderboard

Best model per region (D+1, rolling 90 days):

<!-- LEADERBOARD:START -->
Best model per region, forecasts for the next day (D+1), last 90 days (2026-09-07 to 2026-09-30). Mean absolute error in brackets (°C, m/s, mm/day); "≈" lists models whose difference from the best is not significant (95 % bootstrap interval).

| Region | Temperature (2 m) | Wind (10 m) | Precipitation (24 h) |
|---|---|---|---|
| **Česko** | **GeoSphere Austria AROME 2.5 km** (1.30) | **DWD ICON-D2** (1.08) | ČHMÚ ALADIN CZ 1 km ≈ ČHMÚ ALADIN Central Europe 2.3 km ≈ UK Met Office Global 10 km ≈ NOAA GFS 0.11°/0.25° ≈ +4 |
| Hlavní město Praha | DWD ICON-D2 ≈ GeoSphere Austria AROME 2.5 km ≈ DWD ICON-EU | DWD ICON-D2 ≈ DWD ICON-EU ≈ GeoSphere Austria AROME 2.5 km | DWD ICON-D2 ≈ Météo-France ARPEGE Europe ≈ DWD ICON-EU ≈ ČHMÚ ALADIN Central Europe 2.3 km ≈ +4 |
| Středočeský kraj | GeoSphere Austria AROME 2.5 km ≈ DWD ICON-D2 ≈ ECMWF AIFS 0.25° | **DWD ICON-EU** (0.95) | Météo-France ARPEGE Europe ≈ UK Met Office Global 10 km ≈ NOAA GFS 0.11°/0.25° ≈ DWD ICON-EU ≈ +2 |
| Jihočeský kraj | **GeoSphere Austria AROME 2.5 km** (1.39) | DWD ICON-D2 ≈ DWD ICON-EU | Météo-France ARPEGE Europe ≈ NOAA GFS 0.11°/0.25° ≈ UK Met Office Global 10 km ≈ ČHMÚ ALADIN Central Europe 2.3 km ≈ +4 |
| Plzeňský kraj | GeoSphere Austria AROME 2.5 km ≈ DWD ICON-D2 | DWD ICON-EU ≈ DWD ICON-D2 | NOAA GFS 0.11°/0.25° ≈ Météo-France ARPEGE Europe ≈ ČHMÚ ALADIN CZ 1 km ≈ ČHMÚ ALADIN Central Europe 2.3 km ≈ +3 |
| Karlovarský kraj | GeoSphere Austria AROME 2.5 km ≈ DWD ICON-D2 ≈ ECMWF IFS 0.25° ≈ ECMWF IFS HRES 9 km | **DWD ICON-D2** (1.02) | Météo-France ARPEGE Europe ≈ GeoSphere Austria AROME 2.5 km ≈ UK Met Office Global 10 km ≈ ČHMÚ ALADIN CZ 1 km ≈ +6 |
| Ústecký kraj | **DWD ICON-D2** (1.18) | DWD ICON-D2 ≈ DWD ICON-EU | UK Met Office Global 10 km ≈ DWD ICON-D2 ≈ ČHMÚ ALADIN Central Europe 2.3 km ≈ Météo-France ARPEGE Europe ≈ +4 |
| Liberecký kraj | GeoSphere Austria AROME 2.5 km ≈ DWD ICON-D2 ≈ ČHMÚ ALADIN CZ 1 km ≈ ČHMÚ ALADIN Central Europe 2.3 km ≈ +1 | DWD ICON-D2 ≈ DWD ICON-EU | DWD ICON-D2 ≈ ČHMÚ ALADIN Central Europe 2.3 km ≈ ČHMÚ ALADIN CZ 1 km ≈ ECMWF IFS 0.25° ≈ +4 |
| Královéhradecký kraj | **GeoSphere Austria AROME 2.5 km** (1.24) | **DWD ICON-D2** (1.23) | ČHMÚ ALADIN CZ 1 km ≈ ČHMÚ ALADIN Central Europe 2.3 km ≈ GeoSphere Austria AROME 2.5 km ≈ NOAA GFS 0.11°/0.25° ≈ +4 |
| Pardubický kraj | GeoSphere Austria AROME 2.5 km ≈ DWD ICON-D2 ≈ ČHMÚ ALADIN Central Europe 2.3 km ≈ ČHMÚ ALADIN CZ 1 km ≈ +1 | DWD ICON-D2 ≈ GeoSphere Austria AROME 2.5 km | Météo-France ARPEGE Europe ≈ DWD ICON-EU ≈ ECMWF AIFS 0.25° ≈ GeoSphere Austria AROME 2.5 km ≈ +6 |
| Kraj Vysočina | GeoSphere Austria AROME 2.5 km ≈ DWD ICON-D2 ≈ Météo-France ARPEGE Europe ≈ ECMWF AIFS 0.25° ≈ +4 | DWD ICON-D2 ≈ DWD ICON-EU | Météo-France ARPEGE Europe ≈ UK Met Office Global 10 km ≈ ECMWF AIFS 0.25° ≈ ČHMÚ ALADIN Central Europe 2.3 km ≈ +3 |
| Jihomoravský kraj | GeoSphere Austria AROME 2.5 km ≈ ECMWF AIFS 0.25° | DWD ICON-D2 ≈ DWD ICON-EU | NOAA GFS 0.11°/0.25° ≈ DWD ICON-EU ≈ DWD ICON-D2 ≈ Météo-France ARPEGE Europe ≈ +3 |
| Olomoucký kraj | GeoSphere Austria AROME 2.5 km ≈ DWD ICON-D2 ≈ ČHMÚ ALADIN Central Europe 2.3 km ≈ ČHMÚ ALADIN CZ 1 km ≈ +1 | DWD ICON-D2 ≈ DWD ICON-EU | GeoSphere Austria AROME 2.5 km ≈ ČHMÚ ALADIN CZ 1 km ≈ DWD ICON-EU ≈ ČHMÚ ALADIN Central Europe 2.3 km ≈ +7 |
| Zlínský kraj | **GeoSphere Austria AROME 2.5 km** (1.31) | DWD ICON-EU ≈ DWD ICON-D2 | UK Met Office Global 10 km ≈ DWD ICON-EU ≈ ECMWF AIFS 0.25° ≈ ČHMÚ ALADIN CZ 1 km ≈ +4 |
| Moravskoslezský kraj | ČHMÚ ALADIN Central Europe 2.3 km ≈ GeoSphere Austria AROME 2.5 km | **DWD ICON-D2** (1.32) | ECMWF AIFS 0.25° ≈ ČHMÚ ALADIN CZ 1 km ≈ UK Met Office Global 10 km ≈ ČHMÚ ALADIN Central Europe 2.3 km ≈ +7 |

The mean of all models beats the best single model in: temperature (2 m) 1 of 15 (0 significantly); wind (10 m) 0 of 15 (0 significantly); precipitation (24 h) 7 of 15 (1 significantly).

_Last updated 2026-10-12 08:12 UTC; scores up to 2026-09-30._

Forecasts: [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0; UK Met Office data CC BY-SA 4.0). Observations: [ČHMÚ](https://opendata.chmi.cz/) (CC BY 4.0). Table: CC BY-SA 4.0.
<!-- LEADERBOARD:END -->

## Goal

Public weather apps disagree, and nobody tells you which model to trust where you live.
meteoverdict checks every day how well each freely available numerical weather
prediction (NWP) model forecast the weather at ČHMÚ stations, and ranks the models
per kraj (region) and elevation class. Scope of v1: 2 m temperature, precipitation and
10 m wind speed, at lead times of 1–3 days (up to 5 where available).

## How it works

1. Fetch hourly station observations from ČHMÚ open data.
2. Fetch what each model forecast 1–5 days earlier for the same hours and places via the
   Open-Meteo Previous Runs API.
3. Score each model (MAE, bias, RMSE, precipitation hit rates), then aggregate by region
   (kraj) and elevation.
4. Publish the results to this README and to a web map (GitHub Pages).

What the results mean and where they can mislead (point versus grid cell, Open-Meteo's
elevation correction, manual gauge timing, statistics):
[docs/methodology.md](docs/methodology.md).

## Data sources

| Source | What we use | Licence |
|---|---|---|
| [ČHMÚ open data](https://opendata.chmi.cz/) | station metadata, observations (truth) and ALADIN forecasts | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| [Open-Meteo Previous Runs API](https://open-meteo.com/en/docs/previous-runs-api) | forecasts issued 1–5 days before each hour, per model | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |

Forecasts are requested at each station's latitude, longitude **and elevation**, so
Open-Meteo applies its elevation correction. This matters most for mountain stations.
The models are listed in [`models.yaml`](src/meteoverdict/models.yaml) (`mvd models`):
ČHMÚ ALADIN (1 km and 2.3 km), DWD ICON-D2 and ICON-EU, ECMWF IFS HRES, IFS 0.25° and
AIFS, NOAA GFS, UK Met Office global, Météo-France ARPEGE Europe and GeoSphere AROME
Austria. All cover Czechia. Their archived history and lead days differ, measured
against the live API: ALADIN only from 2026-06-24 and up to D+2; ICON-D2 and GeoSphere
AROME only D+1 ([details](docs/data-sources.md#models), re-check with
`uv run scripts/probe_archive.py`).

Paths, file formats and caveats: [docs/data-sources.md](docs/data-sources.md).

## Development

Requires [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 for you).

```bash
uv sync                         # create .venv with dev tools
uv run mvd --help               # list commands
uv run ruff check . && uv run ruff format --check . && uv run pytest
```

```bash
uv run mvd stations             # download ČHMÚ station metadata → data/stations.parquet
uv run mvd models [--all]       # list the compared weather models (from models.yaml)
uv run mvd archive-aladin --out-dir data/aladin   # save ALADIN station forecasts locally
```

**Web map** (`web/`, Vite + MapLibre, Node 22). It colours each okres (or kraj, where
the okres level is not published) and each station by its best model, and explains a
region on click. An okres with fewer than three stations borrows the nearest ones of its
neighbours, so every okres is ranked; the popup says how many are borrowed and links
to that okres's forecast. `forecast.html` combines today's forecasts of all models
for one okres with weights from their scores there (it asks the Open-Meteo Forecast API
from the browser). `tv.html` is a TV-style forecast map from `outlook.json` (see
`mvd outlook` below): days and parts of the day as tabs, the okresy coloured by
temperature, chance of rain, wind or cloud, weather symbols drawn on a canvas, a play
button that steps through the next days, and a panel per okres with its six days and a
link to the detailed page; the URL keeps the view (`#2026-10-13/afternoon/temperature/CZ0201`). Variable, lead time and period
(last 90 days, this season, all time, all winters …) are chosen in the header and kept
in the URL (`#temperature_2m/1/90d`). Clicking a station charts each model's daily error
there over the last 90 days (D+1 and D+2). A second page, `compare.html`, ranks the
models for all of Czechia (MAE, difference to the best with its interval, bias, RMSE,
and the mean of all models as a baseline) and charts their bias by elevation class. Both
pages are in Czech or English (Czech for Czech and Slovak browsers; a button switches
and the choice is remembered in the browser). Boundaries are drawn on a plain background
(no third-party map tiles). It reads the scores and `stations.json` and the per-station
series from `site/data`, which is published in the release `data-latest`
(`site-data.zip`; unzip it into `site/data` to run the map locally with data) and not
committed. `.github/workflows/pages.yml` builds it after every daily update and
publishes it on GitHub Pages (Settings → Pages → Source: GitHub Actions) at
<https://jerrylion.github.io/meteoverdict/>; a fork without Pages enabled only builds.

```bash
cd web && npm ci && npm test && npm run dev   # local map at http://localhost:5173
```

**ALADIN archive.** ČHMÚ keeps ALADIN runs online for only three days, so a GitHub
Actions workflow runs `mvd archive-aladin --github-release` every three hours. It saves
2 m temperature, 10 m wind and precipitation at every station for every run and lead
hour (0–72 h) as Parquet files in the releases `aladin-YYYY-MM`. Format:
[docs/data-sources.md](docs/data-sources.md#aladin-archive).

`data/stations.parquet` has one row per station: `id` (WIGOS id), `gh_id` (ČHMÚ
id), `name`, `lat`, `lon`, `elevation` (m), `active`, `okres_code` (LAU 1, e.g.
`CZ0642`), `okres`, `kraj_code` (NUTS 3, e.g. `CZ064`), `kraj` and `elevation_class` (`lowland` < 400 m, `upland` 400–800 m,
`mountain` > 800 m). Active stations are those in today's ČHMÚ list; stations closed
since 2024-01-01 are kept as inactive so the backfill can still use them. Stations
outside Czechia are dropped (up to 2 km outside the border still counts, for stations
on the border line). Use `--out PATH` to write elsewhere.

```bash
uv run mvd fetch-obs --start 2026-09-01 --end 2026-09-30   # hourly observations → data/obs/2026-09.parquet
```

`mvd fetch-obs` writes one Parquet file per month (`station_id`, `time` in UTC,
`variable`, `value`, ČHMÚ `quality` code, `source`) for `temperature_2m` (°C),
`wind_speed_10m` (m/s) and `precipitation` (mm in the hour ending at `time`). Running it
again replaces the values for the same station, time and variable. How the hourly
values are built: [docs/data-sources.md](docs/data-sources.md#hourly-observations-mvd-fetch-obs).

```bash
uv run mvd fetch-fc --start 2026-09-01 --end 2026-09-14 --dry-run   # how many API calls?
uv run mvd fetch-fc --start 2026-09-01 --end 2026-09-14             # → data/fc/2026-09.parquet
```

`mvd fetch-fc` stores, per station, hour, model and lead day (D+1 … D+5), the forecast
`temperature_2m`, `precipitation` and `wind_speed_10m` from the Open-Meteo Previous Runs
API. The free API allows 10,000 weighted calls a day and 300,000 a month; one to 14 days
for all models and stations costs about 6,900, so `--max-calls` (default 9,000) stops a
run in time and keeps what was fetched ([details](docs/data-sources.md#fetching-mvd-fetch-fc)).

**Raw data store.** Monthly files are kept as assets of the GitHub release
`data-YYYY-MM` (`obs-`, `fc-` and `scores-YYYY-MM.parquet`, CC BY-SA 4.0):

```bash
export GITHUB_TOKEN=… GITHUB_REPOSITORY=JerryLion/meteoverdict
uv run mvd store download --from 2026-01 --to 2026-09   # into data/obs and data/fc
uv run mvd store upload                                  # only files that changed
```

Each asset's label is the file's SHA-256, so unchanged files are skipped in both
directions; a changed file replaces the stored one.

```bash
uv run mvd score --start 2026-09-01 --end 2026-09-30   # → data/scores/2026-09.parquet
```

`mvd score` pairs the stored observations and forecasts and writes one row per day,
station, model, lead day and variable with additive error sums (and rain/no-rain
counts for daily precipitation) ([details](docs/data-sources.md#daily-scores-mvd-score)).

```bash
uv run mvd aggregate      # → data/aggregates.parquet and site/data/**/*.json
```

`mvd aggregate` combines the daily scores per station, okres, kraj, elevation class and
for all of Czechia over the last 90 days, the current season and all time. Models are
compared only on the station-days they all cover, and regions with fewer than 3
stations are flagged ([details](docs/data-sources.md#aggregates-mvd-aggregate)).

```bash
uv run mvd backfill --from 2024-01-01 --max-calls 6000   # resumable; run again to continue
```

`mvd backfill` fills the history newest first in 14-day windows within the free
Open-Meteo quota and remembers its progress, so it can run a little every day; a GitHub
Actions workflow does that with 8,500 calls a day (all history takes about two months)
([details](docs/data-sources.md#backfill-mvd-backfill)).

```bash
uv run mvd outlook                   # TV-style forecast for every okres → site/data/outlook.json
```

`mvd outlook` asks the Open-Meteo Forecast API once for all 77 okresy and all models
(about 340 weighted calls), combines them with the okres weights from
`data/aggregates.parquet` and summarises each of the next six days by night, morning,
afternoon and evening (Prague time): temperature range, rain, probability of
precipitation, wind, cloud cover and a weather symbol. A workflow runs it at 05:52 and
17:52 UTC and puts `outlook.json` into the release `data-latest` for the map
([details](docs/data-sources.md#outlook-mvd-outlook-roadmap-66)).

```bash
uv run mvd report            # print the leaderboard
uv run mvd report --readme   # rewrite the block between the LEADERBOARD markers above
```

```bash
uv run mvd daily             # capture observations, re-score, aggregate, update README
```

`mvd daily` (run every morning by `.github/workflows/daily.yml` with `--github-release`)
uses no Open-Meteo calls: forecasts come from the backfill. It captures the last three
days of observations, re-scores the last 100 days, aggregates and ranks everything,
writes `site/data` and the leaderboard above, and publishes the full data to the release
`data-latest` ([details](docs/data-sources.md#daily-pipeline-mvd-daily)).

Dates are `YYYY-MM-DD` in UTC.

CI runs the same checks on every pull request. Tests never use the network;
external data comes from recorded fixtures in `tests/fixtures/`.

## Attribution & licence

- Weather data by [Open-Meteo.com](https://open-meteo.com/), licensed under
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- Observations and ALADIN forecasts: Czech Hydrometeorological Institute (ČHMÚ / CHMI),
  [opendata.chmi.cz](https://opendata.chmi.cz/), licensed under
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). We extract station values
  and convert units.
- Forecast models via Open-Meteo: DWD (ICON), ECMWF (IFS, AIFS), NOAA (GFS),
  Météo-France (ARPEGE, Licence Ouverte 2.0), GeoSphere Austria (AROME), KNMI and DMI,
  and the UK Met Office ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)).
- Okres and kraj boundaries: © ČÚZK (INSPIRE Administrative Units), CC BY 4.0, via
  [siwekm/czech-geojson](https://github.com/siwekm/czech-geojson); simplified by
  `scripts/build_regions.py`.
- ALADIN station archive (release assets `aladin-YYYY-MM`): CC BY 4.0.
- Generated scores and maps: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/),
  because they include UK Met Office data (ShareAlike).
- Details and rules (non-commercial use, rate limits): [docs/licensing.md](docs/licensing.md).
- Code: [MIT](LICENSE).

This is a non-commercial, independent project, not affiliated with ČHMÚ or Open-Meteo.
