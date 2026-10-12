# Data sources

This page records what we verified about the external data, where it lives and under
which terms. Everything here was checked on **2026-10-11**, by downloading the real
files and calling the real API. Claims we could not verify are marked **unverified**;
do not build on them without checking. Both sources are reachable without
authentication from the development machine and from GitHub Actions.

## ČHMÚ climatological open data (observations)

Base URL: `https://opendata.chmi.cz/meteorology/climate/`

Primary reference: the official description
[`Klimatologicka_data_popis.pdf`](https://opendata.chmi.cz/meteorology/climate/Klimatologicka_data_popis.pdf)
(Czech, last modified 2024-07-08). The sections below summarise it and add what we saw in
real files.

### Directory layout

| Path | Contents | Update cadence (per the PDF) |
|---|---|---|
| `now/data/` | 10-minute (`10m-…`) and hourly (`1h-…`) files per station and day | regenerated hourly and overwritten; on 2026-10-12 it held the last three days (09–11 Oct for 10-minute files) |
| `now/metadata/` | `meta1`…`meta4`, named `metaN-YYYYMMDD.json` | daily; deleted after 10 days |
| `recent/data/{10min,1hour,daily,monthly,pentadic,phenomena}/` | current year, month folders `01/`…`12/` | 10 min / 1 h: twice a day, and the previous two months are regenerated on the 3rd of each month; daily: after each day; monthly / pentadic: start of the next month, re-uploaded after two months |
| `historical/data/{10min,1hour,daily,monthly,pentadic,yearly,phenomena}/` | closed years; 10 min and 1 h data from 2018 | once a year, by the end of February |
| `historical/metadata/` | station and element metadata | once a year |
| `historical_csv/data/…` | the same as CSV, one file per element | once a year |

Implications for us:

- **Backfill (2.6)** reads `historical/` for closed years and `recent/` for the months
  of the last year. `historical/` has 10-minute and hourly data from 2018, which covers
  our 2024+ window.
- **The current month is not in `recent/` yet** (on 2026-10-12, `recent/data/10min/10/`
  still held October 2025, `09/` held September 2026). Until it is published, the only
  source is `now/`, which keeps about three days. **Daily runs (3.2) must therefore
  fetch yesterday from `now/` every day** and re-fetch the month from `recent/` once it
  appears (checked data replaces the unchecked values; `mvd fetch-obs` merges by
  station, time and variable).

### File names

`{WSI}` is the WIGOS Station Identifier (e.g. `0-20000-0-11520`, Praha-Libuš) and
`{PRVEK}` is the element code.

| Data | Pattern |
|---|---|
| `now/` 10 min / 1 h (JSON) | `10m-{WSI}-{YYYYMMDD}.json`, `1h-{WSI}-{YYYYMMDD}.json` (one file per station and day) |
| `historical/` 10 min / 1 h (JSON) | `{YYYY}/10m-{WSI}-{YYYYMM}.json` (one file per station and **month**; the PDF says `YYYYMMDD`, but the real files are monthly, e.g. `historical/data/10min/2025/10m-0-20000-0-11520-202503.json`, 5.8 MB) |
| `recent/` 10 min / 1 h | `10m-{WSI}-{YYYYMM}.json`, `1h-{WSI}-{YYYYMM}.json` (one file per station and **month**, in month folders `01/`…`12/`; a folder holds the latest published year for that month, e.g. `10/` still held `202510` on 2026-10-11) |
| daily | `recent/`: `dly-{WSI}-{YYYYMM}.json`; `historical/`: `dly-{WSI}.json` |
| `historical_csv/` 10 min / 1 h | `10m-{WSI}-{PRVEK}.csv`, `1h-{WSI}-{PRVEK}.csv` |

Example (fetched successfully):
`now/data/1h-0-20000-0-11520-20261011.json`.

### JSON envelope

All JSON files we read (metadata and data) share one envelope:

```json
{
  "zaznamID": "<uuid>",
  "datovyZdrojID": "meteorologie",
  "datovyTokID": "Open.Data.1H",
  "datumVytvoreni": "2026-10-11T23:11:29.159Z",
  "verzeDat": "1.0",
  "data": {
    "type": "DataCollection",
    "data": {
      "header": "STATION,ELEMENT,DT,VAL,FLAG,QUALITY",
      "values": [["0-20000-0-11520", "C-C1Av", "2026-10-11T00:00:00Z", 9074.0, "", 5.0]]
    }
  }
}
```

- `header` is a **comma-separated string**, and `values` is a list of row arrays in
  that column order.
- `datovyTokID` names the stream: `Open.Data.Metadata` for metadata, `Open.Data.1H` for
  hourly data.
- Timestamps are ISO 8601 with a `Z` suffix. The PDF states: "Časy jsou v UTC" (times
  are in UTC).

### Data files (10 min and 1 h)

Columns: `STATION` (WSI), `ELEMENT`, `DT` (UTC timestamp), `VAL` (number), `FLAG`
(string, often empty), `QUALITY` (number, codes from `meta4`: 0 Good, 1 Suspect,
2 Poor, 3 Estimated, 4 Missing, 5 Unknown). `now/` data is mostly unchecked (`5.0`,
some values already `0.0` or `3.0`), `recent/` data is checked (`0.0` for good values).
**Missing values come as an empty string `""`** with `QUALITY` 4, so `VAL` is not always
a number. The rows are long-format: one row per
station × element × time.

Which elements go where (from `meta2`'s `OBS_TYPE` column and real files):

- **Hourly (`1H`) elements** include `SRA1H` (precipitation, 1 h, mm), `P`, `E`, `Td`,
  `N`, `ww`, `VV`, `SSV1H` and the ceilometer `C-…` elements.
- **10-minute (`10M`) elements**, per `meta2` for Praha-Libuš: `T` (Teplota, °C,
  sensor at 2 m), `TMA`/`TMI` (max/min), `F` (Rychlost větru, m/s, 10 m), `Fprum`
  (Rychlost prům, m/s, 10 m), `Fmax`, `D` (direction), `SRA10M` (precipitation, mm),
  plus soil temperatures.
- Element names, units and sensor heights come from `meta2` (`NAME`, `UN_DESCRIPTION`,
  `HEIGHT`). The PDF lists codes without definitions.

### Hourly observations (`mvd fetch-obs`)

2 m temperature and 10 m wind exist only in the 10-minute files, so `mvd fetch-obs`
builds hourly values from them:

| Variable | From | Matches the forecast because |
|---|---|---|
| `temperature_2m` | `T` at HH:00 | Open-Meteo's `temperature_2m` is the value at the hour |
| `wind_speed_10m` | `F` at HH:00 (m/s) | model wind at the hour; `F` is ČHMÚ's main wind speed element |
| `precipitation` | sum of the six `SRA10M` values stamped HH-1:10 … HH:00, only if all six exist | Open-Meteo's hourly precipitation is the sum over the preceding hour |

Checks on real data (Praha-Libuš, September 2026): the hourly precipitation equals
ČHMÚ's own `SRA1H` for all 720 hours (22.6 mm both), which also confirms that
timestamps mark the end of each interval. `F` is on average 0.1 m/s above `Fprum`
(equal in 32 % of slots); ČHMÚ does not document how the two are averaged
(**unverified**; possibly scalar vs. vector mean), and the difference is small for
ranking models.

Values with `QUALITY` 1 (suspect), 2 (poor) or 4 (missing) are dropped; 0, 3 and 5 are
kept with their code, so scoring can exclude estimated values. Every value also records
its `source` (`recent`, `historical`, `now`).

Only stations with a 10-minute `T`, `F` or `SRA10M` in today's `meta2` are fetched
(about 475; the other ~280 active stations are manual rain gauges with daily data
only, roadmap 1.5b), plus inactive stations (not in today's `meta2`). One day for all
stations from `now/` took about a minute (468 stations returned data on 2026-10-10).
A monthly `recent/` or `historical/` file is about 5 MB per station, so a month of
history for all stations is about 2.5 GB to download; `historical_csv/` (one file per
element) may be cheaper for the backfill (2.6).

### Metadata files

| File | Header (as seen in real files) | Notes |
|---|---|---|
| `meta1` (`now/`) | `WSI,GH_ID,FULL_NAME,GEOGR1,GEOGR2,ELEVATION,BEGIN_DATE` | stations operating today (760 rows on 2026-10-11, of which 3 WIGOS ids appear twice: two re-equipped stations with a new `GH_ID` and `BEGIN_DATE` in 2026, one with two slightly different positions; `mvd stations` keeps the row with the latest `BEGIN_DATE`). **`GEOGR1` is longitude, `GEOGR2` is latitude** (e.g. Cheb 12.39, 50.07). Elevation in m. The PDF omits `BEGIN_DATE`. It includes at least one non-Czech station (Reykjavik), so filter to Czechia. |
| `meta1` (`historical/metadata/meta1.json`) | `WSI,GH_ID,BEGIN_DATE,END_DATE,FULL_NAME,GEOGR1,GEOGR2,ELEVATION` | **one row per validity period**: a station's position and elevation can change between periods (Cheb has six). An open period ends at `3999-12-31T23:59:00Z`. Also lists closed stations. 5,539 rows (created 2026-02-12, so it lags behind closures during the current year). Note the different column order. |
| `meta2` | `OBS_TYPE,WSI,EG_EL_ABBREVIATION,NAME,UN_DESCRIPTION,HEIGHT,SCHEDULE` | elements measured per station, with sensor height in m. The PDF omits `OBS_TYPE` and `SCHEDULE`. |
| `meta3` | `EL_ABBREVIATION,FLAG,DESCRIPTION` | meaning of the `FLAG` column per element (32 rows) |
| `meta4` | `FLAG2,DESCRIPTION` | quality codes 0–5 (see above) |

Neither `meta1` has an "active" flag. `mvd stations` (roadmap 1.2) treats a station
as active when it is in the current `now/metadata/meta1`, and takes its position from
there. Stations only in the historical file are kept as inactive at the position of
their last period, if that period ended on or after 2024-01-01. The historical file
is not reliable as the only source of "active": it is regenerated once a year.

Foreign stations also show up in the historical file, and not always with sensible
coordinates: Marambio (Antarctica) is listed at `GEOGR1` 56.62, `GEOGR2` 64.23, so
latitude and longitude look swapped and unsigned. A Czech bounding box drops them
first, then the kraj polygons drop anything outside Czechia (see below).

On 2026-10-11 `mvd stations` produced 782 stations (756 active, 26 closed since
2024-01-01) in all 14 kraje; none was outside Czechia or needed the border tolerance.

Small real excerpts are in `tests/fixtures/chmi/` (see the README there).

### Access notes

- Directory listings work with plain HTTP (they are large HTML pages). The fetcher
  should still build URLs from the patterns above rather than scrape listings, and
  retry on errors.
- No authentication is needed.

### Licence and attribution

- The PDF and the server do not state a licence. The PDF only says these data replace
  data published under Act No. 123/1998 Coll. (on the right to environmental
  information).
- The ČHMÚ page ["Mohu získat vaše data pro svůj projekt?"](https://www.chmi.cz/-/mohu-z%C3%ADskat-va%C5%A1e-data-pro-sv%C5%AFj-projekt-)
  sends open-data users to opendata.chmi.cz and carries a **CC BY 4.0** badge in its
  footer. This suggests CC BY 4.0, but it is not an explicit statement for the dataset.
- **Confirmed: CC BY 4.0.** The National Open Data Catalogue (data.gov.cz) records
  for the ČHMÚ station data and the ALADIN forecasts list CC BY 4.0, author ČHMÚ
  (checked 2026-10-12, see [licensing.md](licensing.md)). Credit "Czech
  Hydrometeorological Institute (ČHMÚ), opendata.chmi.cz, CC BY 4.0".

## Metrics

`meteoverdict.metrics` (roadmap 2.2). Error = forecast − observed.

| Metric | Formula | Used for |
|---|---|---|
| MAE | Σ\|error\| / n | temperature, wind, precipitation amounts |
| bias | Σ error / n (positive = forecast too high) | same |
| RMSE | √(Σ error² / n) | same |
| POD | a / (a + c) | daily precipitation ≥ 0.1 mm and ≥ 5 mm |
| FAR | b / (a + b) | same |
| ETS | (a − a_r) / (a + b + c − a_r), a_r = (a + b)(a + c) / n | same |

a = hits, b = false alarms, c = misses, d = correct negatives; an event is "at least the
threshold". Scores are stored as additive sums (`n`, `sum_err`, `sum_abs_err`,
`sum_sq_err`, `a_*`, `b_*`, `c_*`, `d_*`), so they can be summed over days, stations and
regions before the metrics are computed; a metric whose denominator is zero is null.
Checked against Finley's (1884) tornado forecasts (a = 28, b = 72, c = 23, d = 2680:
POD 0.549, FAR 0.72, ETS 0.216).

## Daily scores (`mvd score`)

`mvd score --start D --end D` reads `data/obs` and `data/fc` (the months of the range
plus the next day, for the last day's precipitation) and writes
`data/scores/YYYY-MM.parquet`: one row per `date`, `station_id`, `model`, `lead_day`
and `variable` with `period_h` and the additive sums (`n`, `sum_err`, `sum_abs_err`,
`sum_sq_err`; for `precipitation_daily` also `a_*`, `b_*`, `c_*`, `d_*` for 0.1 and 5 mm).

| `variable` | `period_h` | Day of a pair |
|---|---|---|
| `temperature_2m`, `wind_speed_10m` | 0 | UTC date of the hour |
| `precipitation` | 1, 3 or 6 (the model's native period) | UTC date the period ends in (01:00 … 24:00) |
| `precipitation_daily` | 24 | the UTC day |

Hourly precipitation MAEs of different periods are not comparable, so models are
ranked on `precipitation_daily`. A day can only be scored once its observations are
published: on 2026-10-12 the latest complete checked month was September 2026 (see
"File names" above). A run over 20 stations and 14 days took 0.2 s.

## Aggregates (`mvd aggregate`)

`mvd aggregate` sums the daily scores per **level** (`station`, `okres`, `kraj`,
`elevation` class, `cz`) and **window** ending at the last scored day (`90d`, `season`
= meteorological season so far, `all`), then derives the metrics.

- **Fair comparison:** within a window, variable and lead day only the station-days
  that every model with that lead day has scores for are used, so models with a shorter
  archive or gaps are compared on the same days as the rest. (Consequence: the `all`
  window for D+1 and D+2 starts when the newest model's archive starts, ALADIN in June
  2026.)
- A region needs at least 3 stations (`enough_stations`); stations are always
  rankable on their own.
- Output: `data/aggregates.parquet` (all columns, including the sums) and
  `site/data/meta.json` plus `site/data/<window>/<level>/<variable>.json` as
  `{"columns": […], "rows": […]}` with floats rounded to 3 decimals.

## Ranking with confidence intervals (roadmap 2.5)

`meteoverdict.ranking` (run by `mvd aggregate`) ranks the models of every level,
region, window, variable and lead day by MAE, on the same fair station-days as the
aggregates. Ranked variables: `temperature_2m`, `wind_speed_10m`,
`precipitation_daily` (hourly precipitation periods differ between models).

- **Bootstrap:** 1,000 resamples of whole **days** with replacement. All stations and
  models of a day stay together, because forecast errors on one day are correlated
  across stations; resampling hours or stations would make the intervals too narrow
  (a test checks that copying the same errors to more stations does not narrow them).
- `diff_to_best`, `diff_ci_low`, `diff_ci_high`: the MAE difference to the best model
  and its 95 % interval. `tied_with_best` when that interval contains 0;
  `clear_winner` for the best model when no other model is tied with it (never with a
  single model).
- Each group draws from its own seed (from `--seed` and the group's key), so results
  are reproducible and do not depend on which other groups are computed.
- **Not handled:** autocorrelation between consecutive days (a moving-block bootstrap
  would widen intervals slightly).
- Cost: about 10 s per window for 100 stations × 90 days × all models (measured); the
  full network takes a few minutes, mostly at station level.

## Raw data store

`mvd store upload` and `mvd store download --from YYYY-MM [--to YYYY-MM]` keep
`data/{obs,fc,scores}/YYYY-MM.parquet` as the assets `{obs,fc,scores}-YYYY-MM.parquet`
of the release `data-YYYY-MM`. GitHub
cannot overwrite a release asset, so a changed file is deleted and uploaded again; the
asset label holds the file's SHA-256 so unchanged files are skipped. Downloads go
through the API (`Accept: application/octet-stream`), which redirects to GitHub's storage
host; httpx drops the token on that redirect. Checked end to end on 2026-10-12 with a
throwaway release (upload, skip, replace, download byte for byte, then deleted). Release
assets may be up to 2 GiB each.

## ALADIN archive

ČHMÚ publishes ALADIN runs (00, 06, 12, 18 UTC) at
`opendata.chmi.cz/meteorology/weather/nwp_aladin/{CZ_1km,Lambert_2.3km}/{HH}/`, one
bz2-compressed GRIB1 file per field and run, e.g.
`ALADCZ1K4opendata_2026101100_CLSTEMPERATURE.grb.bz2`. Field names and units are in
`Popis_obsahu.xlsx` in that folder. **Only the last three days are kept** (runs from
2026-10-09 to 2026-10-11 on 2026-10-11), so older runs are gone for good unless someone
archived them. Licence: CC BY 4.0, author ČHMÚ (National Open Data Catalogue datasets
"Numerické předpovědi počasí modelu ALADIN/ČHMÚ: produkty na oblasti ČR" and
"… produkty v projekci Lambert").

What we verified in the files (run 2026-10-11 00 UTC):

| Domain | Grid | Steps |
|---|---|---|
| `CZ_1km` (`chmi_aladin_cz_1km`) | regular lat/lon, 501 × 290, 0.014° × 0.009°, lat 48.5–51.098, lon 12.0–18.995 | 0–72 h hourly |
| `Lambert_2.3km` (`chmi_aladin_central_europe_2km`) | Lambert conformal, 1053 × 837 | 0–72 h hourly |

- `CLSTEMPERATURE`: 2 m temperature, K, instantaneous.
- `CLSWIND_SPEED`: 10 m wind speed, m/s, instantaneous.
- `SURFPREC_TOTAL`: total precipitation in kg/m² (= mm), **accumulated since the start
  of the run**; there is no step 0.
- `SURFGEOPOTENTIEL`: model orography as geopotential (m²/s²); ÷ 9.80665 gives the
  model terrain height.
- About 55 MB per run for these fields on the 1 km grid, about 250 MB on the 2.3 km grid.

`mvd archive-aladin` (run every three hours by `.github/workflows/archive-aladin.yml`)
stores, for each run still on the server, one Parquet file per domain and run with one
row per station and lead hour:

| Column | Meaning |
|---|---|
| `model`, `run`, `lead_h`, `valid_time` | model id, run time (UTC), lead in hours (0–72), `run + lead_h` |
| `station_id` | WIGOS id from `mvd stations` |
| `temperature_2m` | °C (converted from K) |
| `wind_speed_10m` | m/s |
| `precipitation_accum` | mm since the run started; null at lead 0. Hourly sums are differences of consecutive leads. |
| `grid_lat`, `grid_lon`, `grid_elevation`, `grid_distance_km` | the grid point used (nearest to the station), its model terrain height (m) and its distance from the station |

Values are taken at the **nearest grid point, without elevation correction**, unlike
Open-Meteo, which downscales to the station elevation. `grid_elevation` makes a
correction possible later. Stations more than 3 km from every grid point are skipped
(none in Czechia: the largest distance was 0.7 km on the 1 km grid, 1.6 km on the 2.3 km
grid). Files are about 0.5 MB per run and domain, so roughly 4 MB a day.

Check against Open-Meteo, Praha-Libuš, run 2026-10-11 18 UTC + 24 h and + 25 h, compared
with Open-Meteo's `chmi_aladin_cz_1km` `_previous_day1` at the same grid cell
(`cell_selection=nearest`, `elevation=290`): 8.53 °C vs 8.6 °C and 7.40 °C vs 7.4 °C;
wind 1.20 vs 1.2 m/s and 0.93 vs 0.9 m/s.

The files are published as assets of the GitHub release `aladin-YYYY-MM` of this
repository (`chmi_aladin_cz_1km_2026101100.parquet`, …), with the CC BY 4.0
attribution and our changes stated in the release notes.

ČHMÚ station observations do not need archiving: `recent/` keeps the current year and
`historical/` all closed years.

## Okres and kraj boundaries

`src/meteoverdict/data/kraje.geojson` holds the 14 kraje with their NUTS 3 code
(`CZ010` … `CZ080`) and name; `okresy.geojson` the 77 okresy with their LAU 1 code
(`CZ0100` for Praha, `CZ0201` … `CZ0806`) and name. The first five characters of an
okres code are its kraj's code. Built by `scripts/build_regions.py` from:

- ČÚZK INSPIRE Administrative Units (`services.cuzk.gov.cz/gml/inspire/au/`). ČÚZK
  publishes its open data under CC BY 4.0 ("ČÚZK poskytuje otevřená data pod licencí
  Creative Commons CC-BY 4.0", cuzk.gov.cz, Otevřená data – základní informace).
- converted to GeoJSON by [siwekm/czech-geojson](https://github.com/siwekm/czech-geojson)
  (CC BY 4.0), pinned to commit `6e77140c`. Names and ids are top-level feature fields
  there (`name`, `id` = `CZ0100000000`), not `properties`.

The script simplifies each level as one coverage (`shapely.coverage_simplify`,
tolerance 0.002°) so neighbours keep identical shared borders, and rounds to 4
decimals: 9 MB → 240 KB for kraje, 20 MB → 550 KB for okresy; borders move by at most
~0.006° (about 0.6 km). Středočeský kraj has a hole (Praha), Brno-venkov too
(Brno-město), Louny one more, and Litoměřice is a MultiPolygon (an exclave). In the
source data Praha's okres is called "území Hlavního města Prahy".

`mvd stations` gives a station the okres whose polygon contains it, or the nearest
okres if the station is at most 2 km outside the national border, and takes the kraj
from the okres code, so both levels always agree. On 2026-10-12 every okres had
stations (2 to 25, median 9).

## Open-Meteo Previous Runs API (forecasts)

Checked on **2026-10-11** against the Open-Meteo documentation, its source code
(open-meteo-website at `1755598c7ac9`, open-meteo server at `f625df2c2b2d`) and live
requests. The free tier also has per-minute and per-hour limits: a burst of a few
hundred requests got `429 Too Many Requests`, so the client must batch and back off.

- Endpoint: `https://previous-runs-api.open-meteo.com/v1/forecast`, same parameters as
  the Forecast API (`latitude`, `longitude`, `elevation`, `hourly`, `models`,
  `start_date`/`end_date` or `past_days`).
- `<variable>_previous_dayN` is the value predicted 24·N hours before the valid time,
  N = 1…7; `_previous_day0` is the latest run. For models with a short forecast horizon
  only the offsets within the horizon are filled ("a model with a 3-day horizon will
  have at most `_previous_day3` populated").
- Variables with offsets include `temperature_2m`, `precipitation` and
  `wind_speed_10m`, the three we verify.
- Archive: the docs say "most models are archived from January 2024"; measured per
  model below.
- Licence: CC BY 4.0 (UK Met Office data: CC BY-SA 4.0). Free tier: non-commercial
  only, 600 calls/min, 5,000/hour, 10,000/day, 300,000/month. A call is weighted:
  locations × max(1, variables × models / 10 × max(1, days / 14)), so a 14-day window
  costs the same as one day. Commercial use of this API needs the Professional
  subscription. See [licensing.md](licensing.md).

### Fetching (`mvd fetch-fc`)

- Several locations go in one request as comma-separated `latitude`, `longitude` and
  `elevation` lists; the answer is a JSON **list** in the same order (every item but
  the first carries `location_id`). We send the station elevation, which Open-Meteo
  echoes back and uses for its elevation correction; `elevation=nan` makes it use its
  own terrain height instead (checked: 286 m at Praha-Libuš).
- Errors come as HTTP 400 `{"error": true, "reason": "…"}`; the daily limit as HTTP
  429 with "Daily API request limit exceeded". Days before a model's archive start
  return `null` values.
- `mvd fetch-fc` asks one model per request, with only its measured lead days, for up
  to 14 days and 100 stations, and stores one row per station × hour × model × lead
  day with `temperature_2m` (°C), `precipitation` (mm in the hour ending at `time`) and
  `wind_speed_10m` (m/s) in `data/fc/YYYY-MM.parquet`.
- **Cost** (weighted calls, Open-Meteo's formula): about **6,900 calls for one day** of
  all 11 enabled models at the ~500 verified stations, the same for any window up to 14
  days, about 20,600 for a month and about 333,000 for 2024-01-01 to 2026-10-10. So the
  daily pipeline should fetch forecasts in 14-day windows (≈ 15,000 calls a month), and
  the full backfill needs more than one month of the free quota (300,000 a month,
  10,000 a day). `mvd fetch-fc --dry-run` prints the estimate; `--max-calls` stops a
  run before it uses more and keeps what was fetched.
- **Interpolated hours:** Open-Meteo returns a value for every hour even for AIFS
  (6-hourly output) and IFS 0.25° (3-hourly), and for models whose output becomes
  3-hourly at longer lead times (ICON-EU after 78 h, IFS HRES after 90 h, GFS after
  120 h, UK Met Office after 54 h; `coarser_after_h` in models.yaml). The in-between
  hours are interpolated: on 20 stations over 14 days (Sept 2026) the mean temperature
  curvature at 3-hourly hours is 1.5–1.7 times that at the other hours exactly from the
  lead day where the step changes (ICON-EU D+4, IFS D+4, GFS D+5, UKMO D+3), and about
  1.0–1.25 before. See "Pairing" below.

### Pairing (`meteoverdict.align`, roadmap 2.1)

Open-Meteo's docs: temperature and wind are "Instant" values, precipitation the
"Preceding hour sum". The observations follow the same conventions, so pairs join on
station, UTC hour and variable. For a model and lead day whose native step is 3 or 6
hours (`Model.native_step`: the run behind `_previous_dayN` is at least 24·N h old, plus
6 h for run spacing and delivery), temperature and wind are compared only at native
hours and precipitation as sums over native periods (`period_h`); incomplete periods
are dropped. Daily precipitation sums use the UTC day (hours ending 01:00–24:00) and
need all 24 hours. **Unverified:** whether Open-Meteo's hourly precipitation for
6-hourly models adds up exactly to the model's 6-hour totals.

### Models

The catalogue is [`src/meteoverdict/models.yaml`](../src/meteoverdict/models.yaml)
(`mvd models --all` prints it).

**Coverage of Czechia** was checked by testing five points (the westernmost, easternmost,
northernmost and southernmost points of Czechia, plus the centre) against each model's
grid as defined in the Open-Meteo server code (`Sources/App/*/…Domain.swift`); projected
grids (ALADIN Central Europe, DMI, KNMI) were transformed with pyproj. Global models
cover Czechia by definition.

| Model id | Grid extent from the server code | Czechia |
|---|---|---|
| `chmi_aladin_cz_1km` | lat 48.5–51.098, lon 12.0–18.995 | covered |
| `chmi_aladin_central_europe_2km` | Lambert conformal, 1053 × 837 × 2.325 km | covered |
| `dwd_icon_d2` | lat 43.18–58.08, lon −3.94–20.34 | covered |
| `dwd_icon_eu` | lat 29.5–70.5, lon −23.5–62.5 | covered |
| `meteofrance_arpege_europe` | lat 20–72, lon −32–42 | covered |
| `geosphere_arome_austria` | lat 42.98–51.82, lon 5.50–22.10 | covered |
| `knmi_harmonie_arome_europe` | rotated grid, 676 × 564 × 0.05° | covered |
| `dmi_harmonie_arome_europe` | Lambert conformal, 1906 × 1606 × 2 km | covered |
| `meteofrance_arome_france` | lat 37.5–55.4, lon −12.0–16.0 | **partly** (not east of 16° E): excluded |
| `italia_meteo_arpae_icon_2i` | lat 33.7–48.9, lon 3–22 | **only the far south**: excluded |

The UK Met Office UKV 2 km model covers only the UK and Ireland (excluded).
KNMI and DMI HARMONIE-AROME cover Czechia but are disabled for v1 (not in the roadmap's
candidate list); `ecmwf_ifs025` is enabled because IFS HRES (`ecmwf_ifs`) only joined
Open-Meteo in September 2025, so the open-data IFS is our only ECMWF history before that.

**Forecast length, grid and output step** come from the model tables in the Open-Meteo
docs (e.g. ICON-D2 2 days, ALADIN 3 days, ARPEGE Europe 4 days, GeoSphere AROME,
KNMI and DMI 2.5 days).

**Lead days** (`max_lead_day`) were measured: share of September 2026 hours with a
`temperature_2m_previous_dayN` value at Praha-Libuš. The archive fills one day less
than the forecast length for short-range models, because a run issued a full N×24 h
before every hour must still reach that hour:

| Model | D+1 | D+2 | D+3 | D+4 | D+5 |
|---|---|---|---|---|---|
| ALADIN CZ 1 km, ALADIN CE 2.3 km | 100 % | 100 % | 0 | 0 | 0 |
| ICON-D2, GeoSphere AROME, KNMI, DMI | 100 % | 0 | 0 | 0 | 0 |
| ICON-EU | 100 % | 100 % | 100 % | 100 % | 0 |
| ARPEGE Europe | 100 % | 100 % | 100 % | 0 | 0 |
| IFS HRES, IFS 0.25°, AIFS, GFS, UKMO global | 100 % | 100 % | 100 % | 100 % | 100 % |

So the high-resolution models can only be compared at D+1, and ALADIN at D+1 and D+2.

**Archive start and gaps** were measured with `scripts/probe_archive.py` (one request
per model: D+1 forecasts of the three variables at Praha-Libuš, 2021-01-01 to
2026-10-09). `archive_from` is the first day all three variables have D+1 data;
`variable_from` records variables that start later. Re-run the script to refresh.

| Model | First day (D+1) | Hours filled since | Gaps and notes |
|---|---|---|---|
| ALADIN CZ 1 km / CE 2.3 km | 2026-06-24 | 100 % | |
| ICON-D2, ICON-EU | 2024-01-19 | 100 % | |
| ECMWF IFS HRES | 2025-10-01 | 96–100 % | T2m 69–81 % in 2026-03/04, wind 81–83 % in 2026-04/05; a few stray wind values in 2025-01 |
| ECMWF IFS 0.25° | 2024-02-04 | 100 % | |
| ECMWF AIFS | **2025-02-18** | 100 % | not 2024 as the docs suggest |
| NOAA GFS | 2024-01-19 | 100 % | 2 m temperature alone from 2021-03-24 |
| UK Met Office global | 2024-08-08 | **75–84 %** | many months between 14 % and 80 % |
| ARPEGE Europe | 2024-01-19 | 100 % | **10 m wind only from 2026-08-07** |
| GeoSphere AROME | 2026-03-26 | 84–100 % | T2m and precipitation 44–80 % in 2026-03 to 2026-05 |
| KNMI HARMONIE | 2024-06-29 | 99–100 % | precipitation only from 2024-10-10 |
| DMI HARMONIE | 2024-06-29 | 100 % | |

Consequences:

- **ALADIN, the model this project most wants to evaluate, has Previous Runs history
  only from 2026-06-24**, not the ~2 years assumed in the roadmap. Long-window rankings
  must compare models over their common period (or label windows per model).
- Model code landing in Open-Meteo is not a reliable bound: UKMO, KNMI and DMI data
  start a few days before their integration commits, AIFS a year after.
- Gaps are real (UKMO especially), so scores must count only hours where both the
  observation and the forecast exist, and report the sample size.

Also note: AIFS has 6-hourly output and IFS 0.25° 3-hourly, so hourly scores for them
use fewer hours; ICON-EU, IFS HRES and UKMO become 3-hourly later in the forecast
(78 h, 90 h and 54 h).
