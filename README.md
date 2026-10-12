# meteoverdict 🐸

[![CI](https://github.com/JerryLion/meteoverdict/actions/workflows/ci.yml/badge.svg)](https://github.com/JerryLion/meteoverdict/actions/workflows/ci.yml)

**Which weather model gets Czechia right?**
Daily verification of ALADIN, ICON, ECMWF, GFS & more against ČHMÚ station observations, with a per-region leaderboard and map.

> 🚧 Early development. See [ROADMAP.md](ROADMAP.md) for the architecture and plan.

## Status

- **Works today:** project skeleton (uv, ruff, pytest), CI on every pull request,
  the `mvd` CLI with all pipeline commands as validated stubs, and documented ČHMÚ
  data sources ([docs/data-sources.md](docs/data-sources.md)) with recorded samples,
  `mvd stations`, which builds the ČHMÚ station table with each station's okres, kraj
  and elevation class (782 stations in all 77 okresy on 2026-10-12), and the model catalogue (`mvd models`):
  11 Open-Meteo models that cover Czechia, with archive start dates and lead days
  measured against the live API.
- **Not yet:** no observations or forecasts are fetched or scored; the leaderboard is
  still empty.
- **Archiving:** every ALADIN run (1 km and 2.3 km) is saved at all stations every three
  hours, since ČHMÚ deletes runs after three days.
- **Observations:** `mvd fetch-obs` turns ČHMÚ 10-minute data into hourly
  temperature, wind and precipitation for ~470 automatic stations.
- **Next:** fetching forecasts from Open-Meteo (1.6).
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

The commands below exist as stubs: they validate their options and exit with
code 1, naming the roadmap item that will implement them.

| Command | Purpose | Roadmap |
|---|---|---|
| `mvd fetch-fc --start D --end D [--model M ...]` | Open-Meteo Previous Runs forecasts | 1.6 |
| `mvd score --start D --end D` | daily scores table | 2.3 |
| `mvd report [--readme]` | leaderboard (optionally into this README) | 3.1 |
| `mvd daily [--date D]` | whole pipeline for one day (default: yesterday, UTC) | 3.2 |
| `mvd backfill --from D [--to D]` | history, month by month | 2.6 |

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
