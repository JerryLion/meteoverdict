# Development

How to run MeteoVerdict yourself: the command-line pipeline (`mvd`), the web pages and
the automated workflows. What the numbers mean is in [methodology.md](methodology.md);
file formats and API details are in [data-sources.md](data-sources.md).

## Setup and checks

Requires [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 for you) and, for the
web pages, Node 22.

```bash
uv sync                         # create .venv with dev tools
uv run mvd --help               # list commands
uv run ruff check . && uv run ruff format --check . && uv run pytest
cd web && npm ci && npm test && npm run dev   # local pages at http://localhost:5173
```

CI runs the same checks on every pull request. Tests never use the network; external
data comes from recorded fixtures in `tests/fixtures/`. Dates are `YYYY-MM-DD` in UTC.

## The pipeline

| Step | Command | Output |
|---|---|---|
| Stations | `mvd stations` | `data/stations.parquet` |
| Observations | `mvd fetch-obs`, `mvd fetch-gauges` | `data/obs/YYYY-MM.parquet` |
| Forecasts (archive) | `mvd fetch-fc`, `mvd backfill` | `data/fc/YYYY-MM.parquet` |
| Scores | `mvd score` | `data/scores/YYYY-MM.parquet` |
| Rankings | `mvd aggregate` | `data/aggregates.parquet`, `site/data/**/*.json` |
| Combined forecast | `mvd outlook` | `site/data/outlook.json`, `outlook-hourly.json` |
| Everything daily | `mvd daily` | all of the above from the stored data |
| Checks | `mvd check` | exit 1 on stale data or many silent stations |

### Stations

```bash
uv run mvd stations             # ČHMÚ station metadata → data/stations.parquet
uv run mvd models [--all]       # the compared weather models (from models.yaml)
```

`data/stations.parquet` has one row per station: `id` (WIGOS id), `gh_id` (ČHMÚ id),
`name`, `lat`, `lon`, `elevation` (m), `active`, `okres_code` (LAU 1, e.g. `CZ0642`),
`okres`, `kraj_code` (NUTS 3, e.g. `CZ064`), `kraj` and `elevation_class` (`lowland`
< 400 m, `upland` 400–800 m, `mountain` > 800 m). Active stations are those in today's
ČHMÚ list; stations closed since 2024-01-01 are kept as inactive so the backfill can
still use them. Stations outside Czechia are dropped (up to 2 km outside the border
still counts, for stations on the border line). Use `--out PATH` to write elsewhere.

### Observations

```bash
uv run mvd fetch-obs --start 2026-09-01 --end 2026-09-30   # → data/obs/2026-09.parquet
```

One Parquet file per month (`station_id`, `time` in UTC, `variable`, `value`, ČHMÚ
`quality` code, `source`) for `temperature_2m` (°C), `wind_speed_10m` (m/s) and
`precipitation` (mm in the hour ending at `time`). Running it again replaces the values
for the same station, time and variable
([details](data-sources.md#hourly-observations-mvd-fetch-obs)).

### Forecasts

```bash
uv run mvd fetch-fc --start 2026-09-01 --end 2026-09-14 --dry-run   # how many API calls?
uv run mvd fetch-fc --start 2026-09-01 --end 2026-09-14             # → data/fc/2026-09.parquet
uv run mvd backfill --from 2024-01-01 --max-calls 6000              # resumable
```

`mvd fetch-fc` stores, per station, hour, model and lead day (D+1 … D+5), the forecast
temperature, precipitation and wind from the Open-Meteo Previous Runs API. The free API
allows 10,000 weighted calls a day and 300,000 a month; 14 days for all models and
stations cost about 6,900, so `--max-calls` (default 9,000) stops a run in time and
keeps what was fetched ([details](data-sources.md#fetching-mvd-fetch-fc)).
`mvd backfill` fills the history newest first in 14-day windows and remembers its
progress, so it can run a little every day
([details](data-sources.md#backfill-mvd-backfill)).

### Scores and rankings

```bash
uv run mvd score --start 2026-09-01 --end 2026-09-30   # → data/scores/2026-09.parquet
uv run mvd aggregate                                   # → data/aggregates.parquet, site/data
uv run mvd report                                      # best model per kraj as Markdown
```

`mvd score` pairs observations and forecasts and writes one row per day, station,
model, lead day and variable with additive error sums
([details](data-sources.md#daily-scores-mvd-score)). `mvd aggregate` combines them per
station, okres, kraj, elevation class and Czechia over the last 90 days, the current
season and all time, compares models only on the station-days they all cover, and lets
okresy with fewer than three stations borrow the nearest stations of their neighbours
([details](data-sources.md#aggregates-mvd-aggregate)).

### Combined forecast

```bash
uv run mvd outlook             # → site/data/outlook.json and outlook-hourly.json
```

Asks the Open-Meteo Forecast API once for all 77 okresy and all models (about 340
weighted calls), combines them with the okres weights from `data/aggregates.parquet` and
summarises each of the next six days by night, morning, afternoon and evening (Prague
time) ([details](data-sources.md#outlook-mvd-outlook-roadmap-66)).

### Daily run

```bash
uv run mvd daily             # capture observations, re-score, aggregate, write the JSON
```

Uses no Open-Meteo calls (forecasts come from the backfill). It captures the last three
days of observations, re-scores the last 100 days, aggregates and ranks everything and
writes `site/data` and the "last updated" badge
([details](data-sources.md#daily-pipeline-mvd-daily)).

## Data store

Monthly files are kept as assets of the GitHub releases `data-YYYY-MM` (`obs-`, `fc-`
and `scores-YYYY-MM.parquet`, CC BY-SA 4.0). Each asset's label is the file's SHA-256,
so unchanged files are skipped in both directions.

```bash
export GITHUB_TOKEN=… GITHUB_REPOSITORY=JerryWoof/MeteoVerdict
uv run mvd store download --from 2026-01 --to 2026-09   # into data/obs and data/fc
uv run mvd store upload                                  # only files that changed
```

The latest results are in the release `data-latest`: `aggregates.parquet`,
`site-data.zip` (unzip it into `site/data` to run the pages locally with data),
`outlook.json` and `outlook-hourly.json`.

**ALADIN archive.** ČHMÚ keeps ALADIN runs online for only three days, so
`mvd archive-aladin --github-release` saves temperature, wind and precipitation at every
station for every run and lead hour (0–72 h) into the releases `aladin-YYYY-MM`
([format](data-sources.md#aladin-archive)).

## Automated workflows

| Workflow | When (UTC) | What |
|---|---|---|
| ALADIN archive | every 3 hours | `mvd archive-aladin --github-release` |
| Backfill | 02:41 | `mvd backfill`, 8,500 Open-Meteo calls a day |
| Daily | 05:17 | `mvd daily --github-release`, commits the badge |
| Outlook | 05:52 and 17:52 | `mvd outlook --github-release` |
| Pages | after Daily, Outlook and changes in `web/` | builds `web/` and publishes it |

## Web pages

`web/` is built with Vite, MapLibre GL and Observable Plot; boundaries are drawn on a
plain background (no third-party map tiles). The pages read `site/data` (scores,
stations, per-station series, outlook), which is published in the release
`data-latest` and not committed. Every page is in Czech or English (Czech for Czech and
Slovak browsers; a button switches and the choice is remembered) and keeps its view in
the URL.

| Page | What it shows | URL state |
|---|---|---|
| `tv.html` | combined forecast map: day tabs, parts of the day, "play the day" / "play the week" (each round switches the map colour temperature → rain → wind → cloud), values at the okresy, a panel per okres; sunrise and sunset (earliest–latest over the okresy) in the headline box and the okres's own in its panel; symbols get a moon when most of the part of day is after sunset or before sunrise | `#2026-10-13/afternoon/temperature/tpw/CZ0201` |
| `index.html` | score map: okresy and stations coloured by the best model, legend with win counts, okres finder, a panel explaining why a model wins, per-station error charts | `#temperature_2m/1/90d/CZ0201` |
| `compare.html` | model ranking for Czechia, a kraj or an okres: MAE with 95 % intervals, skill, bias, RMSE, ETS/POD/FAR, MAE by lead day | region |
| `forecast.html` | hourly combined forecast for one okres next to the best single model, with the weights (asks Open-Meteo from the browser); sunrise and sunset per day and the nights shaded in the charts, from `outlook.json` | okres |
| `api.html` | open data: JSON and CSV per okres under `api/v1/` ([docs](open-data.md)) | – |

GitHub Pages: Settings → Pages → Source: GitHub Actions. A fork without Pages enabled
only builds.
