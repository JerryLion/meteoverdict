# meteoverdict 🐸

[![CI](https://github.com/JerryLion/meteoverdict/actions/workflows/ci.yml/badge.svg)](https://github.com/JerryLion/meteoverdict/actions/workflows/ci.yml)
[![Last updated](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FJerryLion%2Fmeteoverdict%2Fmain%2Fsite%2Fdata%2Fbadge.json)](https://github.com/JerryLion/meteoverdict/actions/workflows/daily.yml)

**Which weather model gets Czechia right?**
Daily verification of ALADIN, ICON, ECMWF, GFS & more against ČHMÚ station observations, with a per-region leaderboard and map.

> 🚧 Early development. See [ROADMAP.md](ROADMAP.md) for the architecture and plan.

## Status

- **Works today:** the whole pipeline. Station table with okres, kraj and elevation
  class (782 stations); hourly ČHMÚ observations (~470 automatic stations) and daily
  totals of the ~280 manual rain gauges, scored over ČHMÚ's 06–06 UTC climatological
  day; forecasts of
  11 models from Open-Meteo at D+1…D+5 (archive starts and lead days measured live);
  pairing at each model's native time resolution; additive daily scores; aggregates per
  station, okres, kraj, elevation class and Czechia with bootstrap confidence intervals;
  the leaderboard below and JSON for the web map; a mean of all models as a baseline
  that every model has to beat.
- **Running automatically:** ALADIN runs are archived every 3 hours (ČHMÚ keeps them 3
  days); the backfill fills the history since 2024, stations and rain gauges, newest
  first within the free Open-Meteo quota (about 3 months in total); the daily workflow
  captures observations, re-scores, and updates this README every morning.
- **Not yet:** the leaderboard fills as the backfill and ČHMÚ's monthly publication of
  checked observations progress. ALADIN has forecast history only from June 2026.
- **Data quality:** implausible observations are dropped; stale data or many silent
  stations make the daily run fail loudly instead of publishing an outdated table
  (`mvd check`).
- **Freshness:** the "last updated" badge above and a line under the leaderboard show
  when the daily run last updated the table and how recent the scores are.
- **Next:** the web map (phase 4).
  See [ROADMAP.md](ROADMAP.md).

## Leaderboard

Best model per region (D+1, rolling 90 days):

<!-- LEADERBOARD:START -->
_Coming soon. Generated automatically by the daily pipeline._
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
Actions workflow does that with 6,000 calls a day (all history takes 2–3 months)
([details](docs/data-sources.md#backfill-mvd-backfill)).

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
