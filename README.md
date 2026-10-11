# meteoverdict 🐸

**Which weather model gets Czechia right?**
Daily verification of ALADIN, ICON, ECMWF, GFS & more against ČHMÚ station observations, with a per-region leaderboard and map.

> 🚧 Early development. See [ROADMAP.md](ROADMAP.md) for the architecture and plan.

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

## Data & attribution

- Forecast data: [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0)
- Observations: Czech Hydrometeorological Institute (ČHMÚ / CHMI) open data
- Generated scores and maps: CC BY 4.0
- Code: [MIT](LICENSE)

This is a non-commercial, independent project.
