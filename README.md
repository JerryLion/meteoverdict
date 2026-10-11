# meteoverdict 🐸

[![CI](https://github.com/JerryLion/meteoverdict/actions/workflows/ci.yml/badge.svg)](https://github.com/JerryLion/meteoverdict/actions/workflows/ci.yml)

**Which weather model gets Czechia right?**
Daily verification of ALADIN, ICON, ECMWF, GFS & more against ČHMÚ station observations, with a per-region leaderboard and map.

> 🚧 Early development. See [ROADMAP.md](ROADMAP.md) for the architecture and plan.

## Status

- **Works today:** project skeleton (uv, ruff, pytest), CI on every pull request,
  and the `mvd` CLI with all pipeline commands as validated stubs.
- **Not yet:** no data is fetched or scored; the leaderboard is still empty.
- **Next:** README skeleton (0.4), then the ČHMÚ data-source exploration (1.1)
  and station metadata (1.2). See [ROADMAP.md](ROADMAP.md).

## Leaderboard

Best model per region (D+1, rolling 90 days):

<!-- LEADERBOARD:START -->
_Coming soon. Generated automatically by the daily pipeline._
<!-- LEADERBOARD:END -->

## How it works

1. Fetch hourly station observations from [ČHMÚ open data](https://opendata.chmi.cz/).
2. Fetch what each model forecast 1–5 days earlier for the same hours and places via the [Open-Meteo Previous Runs API](https://open-meteo.com/en/docs/previous-runs-api).
3. Score each model (MAE, bias, RMSE, precipitation hit rates), then aggregate by region (kraj) and elevation.
4. Publish the results to this README and to a web map (GitHub Pages).

## Development

Requires [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 for you).

```bash
uv sync                         # create .venv with dev tools
uv run mvd --help               # list commands
uv run ruff check . && uv run ruff format --check . && uv run pytest
```

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

## Data & attribution

- Forecast data: [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0)
- Observations: Czech Hydrometeorological Institute (ČHMÚ / CHMI) open data
- Generated scores and maps: CC BY 4.0
- Code: [MIT](LICENSE)

This is a non-commercial, independent project.
