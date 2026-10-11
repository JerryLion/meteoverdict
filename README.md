# meteoverdict 🐸

[![CI](https://github.com/JerryLion/meteoverdict/actions/workflows/ci.yml/badge.svg)](https://github.com/JerryLion/meteoverdict/actions/workflows/ci.yml)

**Which weather model gets Czechia right?**
Daily verification of ALADIN, ICON, ECMWF, GFS & more against ČHMÚ station observations, with a per-region leaderboard and map.

> 🚧 Early development. See [ROADMAP.md](ROADMAP.md) for the architecture and plan.

## Status

- **Works today:** project skeleton (uv, ruff, pytest), CI on every pull request,
  the `mvd` CLI with all pipeline commands as validated stubs, and documented ČHMÚ
  data sources ([docs/data-sources.md](docs/data-sources.md)) with recorded samples,
  and `mvd stations`, which builds the ČHMÚ station table.
- **Not yet:** no observations or forecasts are fetched or scored; the leaderboard is
  still empty.
- **Next:** Open-Meteo model coverage (1.3), station → kraj mapping (1.4).
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
| [ČHMÚ open data](https://opendata.chmi.cz/) | station metadata and hourly observations (truth) | likely CC BY 4.0, not yet confirmed ([details](docs/data-sources.md#licence-and-attribution)) |
| [Open-Meteo Previous Runs API](https://open-meteo.com/en/docs/previous-runs-api) | forecasts issued 1–5 days before each hour, per model | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |

Forecasts are requested at each station's latitude, longitude **and elevation**, so
Open-Meteo applies its elevation correction. This matters most for mountain stations.
Which models are included is decided in roadmap 1.3 after checking their coverage of
Czechia.

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
```

`data/stations.parquet` has one row per station: `id` (WIGOS id), `gh_id` (ČHMÚ
id), `name`, `lat`, `lon`, `elevation` (m) and `active`. Active stations are those in
today's ČHMÚ list; stations closed since 2024-01-01 are kept as inactive so the
backfill can still use them. Foreign stations are dropped with a coarse bounding box
(exact borders come in roadmap 1.4). Use `--out PATH` to write elsewhere.

The commands below exist as stubs: they validate their options and exit with
code 1, naming the roadmap item that will implement them.

| Command | Purpose | Roadmap |
|---|---|---|
| `mvd fetch-obs --start D --end D` | ČHMÚ hourly observations | 1.5 |
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
- Observations: Czech Hydrometeorological Institute (ČHMÚ / CHMI),
  [opendata.chmi.cz](https://opendata.chmi.cz/). The licence is probably CC BY 4.0 but
  not yet confirmed (see [docs/data-sources.md](docs/data-sources.md#licence-and-attribution)).
- Generated scores and maps: CC BY 4.0.
- Code: [MIT](LICENSE).

This is a non-commercial, independent project, not affiliated with ČHMÚ or Open-Meteo.
