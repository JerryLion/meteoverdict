# meteoverdict: Architecture & Roadmap

> Which weather model is most accurate where in Czechia?
> Daily verification of public NWP models against ČHMÚ station observations,
> published as an auto-updated README leaderboard and a static web map.

Package: `meteoverdict` · CLI: `mvd`

---

## 1. How it works

```
          ┌──────────────────────┐        ┌───────────────────────────┐
          │ ČHMÚ open data       │        │ Open-Meteo Previous Runs  │
          │ opendata.chmi.cz     │        │ API (forecasts issued     │
          │ station observations │        │ 1–5 days before each hour)│
          └──────────┬───────────┘        └─────────────┬─────────────┘
                     │  fetch-obs                       │  fetch-fc
                     ▼                                  ▼
              ┌─────────────────────────────────────────────────┐
              │  Raw store: Parquet, partitioned by month       │
              │  obs/YYYY-MM.parquet   fc/YYYY-MM.parquet       │
              └───────────────────────┬─────────────────────────┘
                                      │  score
                                      ▼
              ┌─────────────────────────────────────────────────┐
              │  Scores: per station × model × variable ×       │
              │  lead day × day  (small, committed to repo)     │
              └───────────┬───────────────────────┬─────────────┘
                          │ report                │ build-site
                          ▼                       ▼
                 README leaderboard        GitHub Pages web map
```

**The key trick:** Open-Meteo's Previous Runs API returns, for any past hour, what
each model predicted 1, 2, 3… days earlier (`temperature_2m_previous_day1`, …).
Most models are archived since January 2024. So we do not need to archive
forecasts ourselves, and we can **backfill ~2 years of history on day one**.

### Components

| Part | Tech | Where it runs |
|---|---|---|
| Python package + CLI (`mvd`) | Python 3.12, `uv`, `httpx`, `polars`, `duckdb` | anywhere |
| Daily data pipeline | GitHub Actions cron (free for public repos) | GitHub |
| Raw data store | Monthly Parquet files as GitHub Release assets (`data-YYYY-MM`) | GitHub Releases |
| Aggregated scores | `site/data/*.json` committed by the pipeline bot | repo |
| README leaderboard | Generated block between `<!-- LEADERBOARD:START/END -->` | repo |
| Web app | Static: Vite + MapLibre GL + Observable Plot, reads JSON | GitHub Pages |
| Development | Claude scheduled task, weekdays, works from this roadmap, opens PRs | Claude (Cowork) |

Two separate loops:

- **Data loop (no AI):** GitHub Actions runs `mvd daily` every morning and commits fresh scores.
- **Development loop:** Claude takes the next unchecked roadmap item, opens a PR, and the maintainer reviews and merges it.

### Running it

```bash
uv sync
uv run mvd backfill --from 2024-01-01      # one-off history
uv run mvd daily                           # fetch yesterday + score + report
uv run mvd report --readme                 # regenerate README leaderboard
cd web && npm i && npm run dev              # local web map
```

### Scope v1

- **Variables:** 2 m temperature (hourly), precipitation (hourly → daily sums), 10 m wind speed.
- **Lead times:** D+1, D+2, D+3 (D+4, D+5 where available).
- **Regions:** 14 kraje, plus an elevation class (lowland < 400 m, upland 400–800 m, mountain > 800 m).
- **Candidate models** (coverage over CZ to be verified in task 1.3):
  - ČHMÚ ALADIN CZ 1 km and ALADIN Central Europe 2 km
  - DWD ICON-D2 and ICON-EU
  - ECMWF IFS HRES 9 km and ECMWF AIFS
  - NOAA GFS
  - UK Met Office global
  - Météo-France ARPEGE Europe
  - GeoSphere Austria AROME (if its domain covers CZ)
- **Metrics:**
  - Temperature and wind: MAE, bias, RMSE.
  - Precipitation: MAE of daily sums, plus POD, FAR and ETS for events of at least 0.1 mm/day and at least 5 mm/day.
- **Ranking:** each kraj and variable gets the model with the lowest MAE over a rolling 90 days and over all time. The ranking only shows a model as better when the difference is significant (bootstrap CI).

### Data & licensing

- **Code:** MIT.
- **Open-Meteo:** CC BY 4.0. Free tier is non-commercial and limited to <10k calls/day. Keep the project non-profit, with no ads, and batch locations per call.
- **ČHMÚ open data:** confirm licence/attribution terms (task 1.1) and credit ČHMÚ in the README and on the site.
- **Point verification:** forecasts are requested at station lat/lon *with station elevation* (Open-Meteo applies elevation downscaling). Document this, since it affects mountain stations.

---

## 2. Roadmap

Each item should fit one PR (≈ one working session). Check items off in the PR that completes them.

### Phase 0: Skeleton
- [x] 0.1 `pyproject.toml` (uv), package `meteoverdict` (CLI `mvd`), `ruff` + `pytest` config, MIT licence, `.gitignore`
- [x] 0.2 CI workflow: lint + tests on PR
- [x] 0.3 CLI entry point (`typer`) with stub commands: `fetch-obs`, `fetch-fc`, `score`, `report`, `daily`, `backfill`
- [x] 0.4 README skeleton: goal, data sources, attribution, empty leaderboard markers

### Phase 1: Data in
- [ ] 1.1 Explore `opendata.chmi.cz/meteorology/climate/{now,recent,historical}`: document paths, formats and licence in `docs/data-sources.md`
- [ ] 1.2 Station metadata loader → `stations.parquet` (id, name, lat, lon, elevation, active)
- [ ] 1.3 Verify which Open-Meteo models cover CZ and their Previous Runs history start; write `models.yaml`
- [ ] 1.4 Station → kraj mapping (point-in-polygon with open kraj boundaries) + elevation class
- [ ] 1.5 `fetch-obs`: hourly T2m, precip, wind for a date range → normalized Parquet (UTC)
- [ ] 1.6 `fetch-fc`: Previous Runs client, batched locations, retries, rate-limit aware
- [ ] 1.7 Raw store: monthly Parquet partitions; upload/download to GitHub Release assets
- [ ] 1.8 Unit tests with recorded fixtures (no network in CI)

### Phase 2: Scoring
- [ ] 2.1 Align obs/fc (time zones, accumulation periods for precip)
- [ ] 2.2 Metrics module (MAE, bias, RMSE, POD/FAR/ETS) + tests against hand-computed cases
- [ ] 2.3 `score`: daily scores table → `scores/YYYY-MM.parquet`
- [ ] 2.4 Aggregations: kraj × model × variable × lead × window (90 d, season, all) → JSON
- [ ] 2.5 Bootstrap confidence intervals for ranking
- [ ] 2.6 `backfill --from 2024-01-01` (resumable, chunked by month)

### Phase 3: Publish
- [ ] 3.1 `report --readme`: leaderboard table (kraj → best model per variable, D+1)
- [ ] 3.2 GitHub Actions daily cron: `mvd daily` → commit JSON + README, upload raw data
- [ ] 3.3 Data quality checks (missing stations, outliers, stale data) that fail loudly
- [ ] 3.4 Badge / "last updated" timestamp in README

### Phase 4: Web app
- [ ] 4.1 Vite + MapLibre scaffold, GitHub Pages deploy workflow
- [ ] 4.2 Choropleth of kraje coloured by best model; legend
- [ ] 4.3 Controls: variable, lead time, window (90 d / season / all)
- [ ] 4.4 Station layer + click → per-model error time series (Observable Plot)
- [ ] 4.5 Model comparison page: overall ranking, bias by elevation class
- [ ] 4.6 Czech / English toggle

### Phase 5: Depth & outreach
- [ ] 5.1 Seasonal and diurnal breakdowns (e.g. ALADIN vs ICON-D2 at night inversions)
- [ ] 5.2 Extreme-event verification (heavy precipitation days, heat days)
- [ ] 5.3 Ensemble/"best blend" baseline: does a simple mean beat every single model?
- [ ] 5.4 Methodology doc (`docs/methodology.md`) with limitations
- [ ] 5.5 Upstream contributions where useful (e.g. CHMI coverage in `wetterdienst`, after checking their AI policy)
- [ ] 5.6 Write-up / blog post with findings

---

## 3. Rules for the daily development task

1. Pull `main` and pick the **first unchecked item** whose prerequisites are done.
2. Work on a branch `roadmap/<item-id>-<slug>`. Keep the PR small and focused.
3. Tests and `ruff` must pass locally before opening the PR.
4. PR description covers what changed, how it was tested and any open questions. Tick the roadmap item in the same PR.
5. If an item is too big, split it into sub-items in the roadmap instead of shipping a giant PR.
6. Never push to `main` directly and never merge your own PR.
7. If blocked (API change, unclear decision), open an issue describing the blocker and move to the next independent item.
