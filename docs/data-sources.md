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
only, see below), plus inactive stations (not in today's `meta2`). One day for all
stations from `now/` took about a minute (468 stations returned data on 2026-10-10).
A monthly `recent/` or `historical/` file is about 5 MB per station, so a month of
history for all stations is about 2.5 GB to download; `historical_csv/` (one file per
element) may be cheaper for the backfill (2.6).

### Manual rain gauges (`mvd fetch-gauges`)

About 280 active stations have no 10-minute data: they are manual rain gauges that
report one daily precipitation total (`SRA`, mm), stamped by ČHMÚ at 06:00 UTC. When
an observer actually reads a gauge is not in the PDF (**unverified**: presumably the
morning climatological term, around 06 UTC). They roughly double the station count
for precipitation.

| Path | Content |
|---|---|
| `recent/data/daily/MM/dly-{WSI}-{YYYYMM}.json` | daily elements (`SRA`, `SNO`, …) of one month, last 12 months; header `STATION,ELEMENT,VTYPE,DT,VAL,FLAG,QUALITY` |
| `historical_csv/data/daily/precipitation/dly-{WSI}-SRA.csv` | all `SRA` values of one station up to the last closed year (about 2.5 MB); header `STATION,ELEMENT,TIMEFUNC,DT,VALUE,FLAG,QUALITY` with a trailing comma on every line |

- **Window:** `DT` is the **start** of the 24-hour window: the value stamped
  `2026-09-04T06:00Z` fell from 4 Sept 06:00 to 5 Sept 06:00 UTC. Checked against the
  hourly totals of Praha-Libuš, which has both: all 30 days of September 2026
  matched. `mvd fetch-gauges` stores it as `precipitation_24h` stamped with the
  window's **end**, like every other value.
- **Delay:** manual readings are published late. In October 2026 July and August were
  complete, while most September rows were still `""` with `QUALITY` 4 (missing).
- **Scoring:** the window is 06–06 UTC, not the calendar UTC day used for automatic
  stations, so the forecasts are summed over the same 24 hours (`precipitation_24h`,
  see "Daily scores").
- **Storage:** `data/gauges/YYYY-MM.parquet` (same columns as `data/obs`), a separate
  kind in the raw data store, so gauge months never overwrite hourly ones.
- **Cost of history:** the historical CSV is about 2.5 MB per station, about 770 MB
  for all gauges, and it holds every closed year. So the history is imported once with
  `mvd fetch-gauges --start 2024-01-01 --end …` (then `mvd store upload`); the
  scheduled runs read only the small monthly files in `recent/`.

A live run for August 2026 (`--start 2026-08-01 --end 2026-08-31`) returned 8,370
daily values from 273 of 307 stations selected as gauges (manual or closed).

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
| POD | a / (a + c) | daily precipitation ≥ 0.1 mm, ≥ 5 mm and ≥ 20 mm (heavy precipitation, the ETCCDI index R20mm) |
| FAR | b / (a + b) | same |
| ETS | (a − a_r) / (a + b + c − a_r), a_r = (a + b)(a + c) / n | same |
| POD, FAR, ETS | as above | daily maximum temperature ≥ 30 °C (a "tropický den", tropical day) |

a = hits, b = false alarms, c = misses, d = correct negatives; an event is "at least the
threshold". Scores are stored as additive sums (`n`, `sum_err`, `sum_abs_err`,
`sum_sq_err`, `a_*`, `b_*`, `c_*`, `d_*`), so they can be summed over days, stations and
regions before the metrics are computed; a metric whose denominator is zero is null.
Stored compactly (one row is one station-day): `n` as uint16, the sums as float32
(about 7 significant digits), the counts as uint8; every aggregation sums them in
64 bits (`metrics.total`).
Checked against Finley's (1884) tornado forecasts (a = 28, b = 72, c = 23, d = 2680:
POD 0.549, FAR 0.72, ETS 0.216).

## Daily scores (`mvd score`)

`mvd score --start D --end D` reads `data/obs` and `data/fc` (the months of the range
plus the next day, for the last day's precipitation) and writes
`data/scores/YYYY-MM.parquet`: one row per `date`, `station_id`, `model`, `lead_day`
and `variable` with `period_h` and the additive sums (`n`, `sum_err`, `sum_abs_err`,
`sum_sq_err`; for `precipitation_daily` and `precipitation_24h` also `a_*`, `b_*`,
`c_*`, `d_*` for 0.1, 5 and 20 mm; for `temperature_max` for 30 °C).

| `variable` | `period_h` | Day of a pair |
|---|---|---|
| `temperature_2m`, `wind_speed_10m` | 0 | UTC date of the hour; only 00, 06, 12 and 18 UTC (ranked) |
| `temperature_2m_hourly`, `wind_speed_10m_hourly` | 0 | UTC date of the hour; every native hour of the model (not ranked) |
| `precipitation` | 1, 3 or 6 (the model's native period) | UTC date the period ends in (01:00 … 24:00) |
| `precipitation_daily` | 24 | the UTC day |
| `precipitation_24h` | 24 | the day ČHMÚ's climatological day starts (06:00 to 06:00 UTC) |
| `temperature_max` | 24 | the UTC day (highest of the 24 hourly values, 00:00 … 23:00) |
| `temperature_2m_00utc`, `_06utc`, `_12utc`, `_18utc` | 0 | UTC date of that hour |

Hourly precipitation MAEs of different periods are not comparable, so models are
ranked on `precipitation_daily` and `precipitation_24h`.

`precipitation_24h` is the window of the manual rain gauges (see "Manual rain gauges"),
so it is the one precipitation score that covers all ~750 stations. A gauge's own
value is used where there is one; at automatic stations the 24 hourly sums ending
07:00 … 06:00 (all must exist). The forecast is the sum of the same 24 hourly values;
like the UTC-day total, each hour comes from its own lead day (the hours after midnight
from the run one day later). Every native period of 3 or 6 hours fits into the window,
so this works for every model. The maps rank precipitation by this score by default;
`precipitation_daily` is also in the map data.

The temperature at the four **synoptic hours** 00, 06, 12 and 18 UTC (roadmap 5.1b)
is also scored on its own (`temperature_2m_00utc` …). Every model, the 6-hourly ones
included, has native output at these hours, so all can be compared by time of day:
06 UTC (07:00 CET, 08:00 CEST) is around the end of the night, when valley inversions
are strongest; 12 UTC is early afternoon. These variables are aggregated (MAE, bias,
RMSE per region, window and season) but not ranked with the bootstrap, which keeps
the daily run short; they add about 40 % to the score rows.

**Same hours for every model.** The ranked `temperature_2m` and `wind_speed_10m`
use only 00, 06, 12 and 18 UTC, where every model (also AIFS, IFS 0.25° and the blend,
which are 6- or 3-hourly) has native output. Scoring each model at all its native hours
compared hourly models over 24 hours with 6-hourly ones over 4, and errors depend on
the time of day: on the first real data (21–29 Sept 2026, D+1, about 470 stations)
a model's MAE over its native hours and over the four synoptic hours differed by
0.02–0.05 °C, as much as the gap between several models. The all-hours scores are kept
as `temperature_2m_hourly` and `wind_speed_10m_hourly`, for information only.

`temperature_max` (roadmap 5.2b) compares the highest hourly temperature of each UTC
day, forecast and observed, and counts heat days (at least 30 °C). It is scored only
for models with hourly output at that lead day (not AIFS, IFS 0.25°, nor the
3-hourly lead days of ICON-EU, IFS HRES, GFS and UKMO, nor the blend): the highest
interpolated hour would cut off the afternoon peak. Both sides use values at the full
hour, so the observed maximum is a little below ČHMÚ's own daily maximum (`TMA`).

A day can only be scored once its observations are
published: on 2026-10-12 the latest complete checked month was September 2026 (see
"File names" above). A run over 20 stations and 14 days took 0.2 s.

## Aggregates (`mvd aggregate`)

`mvd aggregate` sums the daily scores per **level** (`station`, `okres`, `kraj`,
`elevation` class, `cz`) and **window** ending at the last scored day (`90d`, `season`
= meteorological season so far, `all`), then derives the metrics. The **seasonal
windows** `djf`, `mam`, `jja` and `son` (roadmap 5.1) take every day of that season
in the whole history, e.g. all summers, so models can be compared by season (their
`from` is the first scored day of all).

- **Cost:** with the seasonal windows, aggregating and ranking one variable and lead
  day for 750 stations, 13 models and a year of days takes about 35 s on a laptop
  (bootstrap included; 19 s with only the first three windows).

- **Fair comparison:** within a window, variable, lead day and region only the
  station-days that every model present in that region has scores for are used, so all
  models of a region are compared on the same stations and days. Models with a shorter
  archive or gaps get the same days as the rest. Where a model never reaches some
  stations (ICON-D2 at six stations in the Beskydy), those stations drop out of that
  region's comparison (Moravskoslezský kraj, Czechia, their okres and elevation class)
  for every model, and are compared among the other models at the station level.
  (Consequences: the `all` window for D+1 and D+2 starts when the newest model's archive
  starts, ALADIN in June 2026; while the backfill has fetched a model for only part of
  the stations, regions are compared on that part.) A window's `from` is its start or
  the first scored day, whichever is later.
- A region needs at least 3 stations (`enough_stations`); stations are always
  rankable on their own.
- **Borrowed stations (roadmap 6.1):** an okres with fewer than 3 stations of its own
  for a variable adds the nearest stations of other okresy, closest to its border first,
  up to 3 and at most 30 km beyond its border (`meteoverdict.neighbours`). A station
  only counts if it survives the fair comparison at D+1; one that some of the okres's
  models never reach is replaced by the next nearest. `borrowed` (in the okres rows)
  counts them; a borrowed station still counts in its own okres. On the 2026-09 scores
  (90 days, D+1) this borrows for 25 okresy for temperature, 39 for wind and 5 for the
  06–06 precipitation, and all 77 okresy are ranked for all three (before: 52, 38 and
  72). Only the okres level borrows.
- Output: `data/aggregates.parquet` (all columns, including the sums) and
  `site/data/meta.json` plus `site/data/<window>/<level>/<variable>.json` as
  `{"columns": […], "rows": […]}` with floats rounded to 3 decimals.
- For the web map also `site/data/stations.json` (position, okres, kraj) and
  `site/data/series/<station>.json`: each model's daily MAE at that station over the
  last 90 days, for the ranked variables at D+1 and D+2 (about 65 kB per station, so
  only in the release `data-latest`).

## Combination weights (roadmap 6.2)

`mvd aggregate` also writes, for the web map's own forecast, how to combine the models
in each okres (`meteoverdict.combine`), from the okres scores of the last 90 days
(window `90d`, same fair station-days, borrowed stations included):

| Open-Meteo variable | Weights from | Bias correction |
|---|---|---|
| `temperature_2m` | `temperature_2m` (synoptic hours, where every model is native) | yes |
| `wind_speed_10m` | `wind_speed_10m` | yes |
| `precipitation` | `precipitation_daily` (daily totals) | no |

- Weight of a model ∝ `1 / (RMSE² − bias²)` (the error left after removing its mean
  error) where it is bias-corrected, `1 / RMSE²` for precipitation; error variances
  below 0.01 count as 0.01.
- Shrinkage towards the plain mean, by the number of scored days:
  `s = days / (days + 30)`, weight `s · w + (1 − s) / models`, correction `s · bias`.
- Combined forecast: `Σ weight · (forecast − correction)` over the models available
  for the hour, weights rescaled to sum to 1; a model ending before the others gets ¾,
  ½ and ¼ of its weight in its last three hours.
- Files: `site/data/forecast/okresy.json` (`code`, `name`, `lat`, `lon` of a point
  inside each okres: the centroid of its largest part, or the nearest inside point;
  `weights` false where the okres has no scores yet) and
  `site/data/forecast/<okres>.json` (`variable`, `lead_day`, `model`, `weight`,
  `correction`, `mae`, `rank`, `days`; about 8 kB each). Only in the release
  `data-latest`, like the okres scores.
- Not yet verified: whether the combination beats the best single model is roadmap 6.4.

## Outlook (`mvd outlook`, roadmap 6.6)

The TV-style forecast for every okres (`meteoverdict.outlook`):

- **Request:** one Open-Meteo **Forecast API** request (`api.open-meteo.com/v1/forecast`)
  for the forecast points of all 77 okresy, all models with weights,
  `hourly=temperature_2m,precipitation,wind_speed_10m,cloud_cover,sunshine_duration`,
  `forecast_days=6`, UTC; 77 × 5 × 11 / 10 ≈ 420 weighted calls (refused above 500). Checked live on
  2026-10-12: a JSON list of 77 results, columns `<variable>_<model>`, 2.7 MB, under a
  second.
- **Combination:** as on the forecast page (bias correction, weights of the hour's lead
  day, models fading out over their last 3 hours, at least 2 models). Cloud cover and
  sunshine are the plain mean of the models (not verified; all 13 models report
  sunshine, checked 2026-10-12).
- **Periods** in Prague time: night 0–6, morning 6–12, afternoon 12–18, evening 18–24,
  and the whole day; a part needs at least 4 hours and a day 18 (the answer starts at
  00 UTC, 02:00 in Prague in summer time).
- **Per period:** `tmin`, `tmax`, `precipitation` (sum of the combined hourly values),
  `rain_probability` (weighted share of the models whose own total is ≥ 0.2 mm, among
  those covering the whole period), `wind` (highest combined hourly mean, m/s), `cloud`
  (%), `sunshine` (hours, sum of the hourly mean), `symbol`: `rain` / `sleet` / `snow` (≤ 2 / ≤ 0.5 °C mean temperature) when the
  probability is ≥ 50 % and the total ≥ 0.2 mm, `showers` at ≥ 30 %, otherwise `clear`
  (< 25 % cloud), `partly` (< 70 %) or `cloudy`. The whole day's symbol uses the cloud
  of 6–18.
- **Sunrise and sunset** (`sunrise`, `sunset`, Prague time "HH:MM") at the okres point,
  computed with the NOAA solar equations (`meteoverdict.sun`, no request; within half a
  minute of almanacs), the same on every row of a day.
- **Output:** `site/data/outlook.json` `{"generated", "time_zone", "parts", "days",
  "okresy": [{code, name, lat, lon}], "columns", "rows"}` (about 110 kB);
  `.github/workflows/outlook.yml` runs it at 05:52 and 17:52 UTC and uploads it to the
  release `data-latest`, after which the Pages workflow rebuilds the map.
- **Budget:** two runs a day ≈ 850 calls; see the [budget split](#open-meteo-budget)
  with the backfill and the single runs.

## Ranking with confidence intervals (roadmap 2.5)

`meteoverdict.ranking` (run by `mvd aggregate`) ranks the models of every level,
region, window, variable and lead day by MAE, on the same fair station-days as the
aggregates. Ranked variables: `temperature_2m`, `wind_speed_10m`,
`precipitation_daily`, `precipitation_24h` (hourly precipitation periods differ between
models).

- **Bootstrap:** 1,000 resamples of whole **days** with replacement. All stations and
  models of a day stay together, because forecast errors on one day are correlated
  across stations; resampling hours or stations would make the intervals too narrow
  (a test checks that copying the same errors to more stations does not narrow them).
- `diff_to_best`, `diff_ci_low`, `diff_ci_high`: the MAE difference to the best model
  and its 95 % interval. `tied_with_best` when that interval contains 0;
  `clear_winner` for the best model when no other model is tied with it (never with a
  single model).
- Each group draws from its own seed (a fixed base seed and the group's key), so results
  are reproducible and do not depend on which other groups are computed.
- **Not handled:** autocorrelation between consecutive days (a moving-block bootstrap
  would widen intervals slightly).
- Cost: about 10 s per window for 100 stations × 90 days × all models (measured); the
  full network takes a few minutes, mostly at station level.

### Blend baseline (roadmap 5.3)

Does a plain mean of all models beat every single one? `mvd score` (and the backfill
and daily runs) also score `blend`, the mean of the models' forecasts per station,
hour and lead day and variable, wherever at least 3 models have a value.

- **Members** change with the lead day (D+1 has all models, D+5 only the global ones)
  and with the archive starts; no weighting, no bias correction.
- **Time resolution:** some members are 3- or 6-hourly (Open-Meteo interpolates the
  hours in between), so the blend is scored like a 6-hourly model: temperature and wind
  at 00, 06, 12 and 18 UTC, precipitation over 6-hour periods, the UTC day and the
  06–06 day.
- **Fair comparison:** the blend counts as one more model covering a station, so a day
  without a blend (fewer than 3 members) is dropped for every model there.
- **Ranking:** the blend is not ranked (`rank` null) and never takes the win from a
  model. Its `diff_to_best` and interval are relative to the best single model, so
  `diff_ci_high` below 0 means the mean beats every model in that region; the model
  comparison page shows it next to the ranked models.

## Backfill (`mvd backfill`)

`mvd backfill --from 2024-01-01 [--to D] [--max-calls N] [--github-release]` fills
history newest first in 14-day windows counted from `--from` (a window costs the same
Open-Meteo quota as one day, so windows run across month boundaries). Only **complete**
windows are processed; the newest one is picked up once its 14th day has passed, so
fresh forecasts reach the scores within two weeks. Progress keys include the window's
start and end. For each window:
the observations of its months (once per month), the forecasts of every enabled model
from its archive start, then the window's daily scores.

- **Progress:** in GitHub Actions each run adds a job summary (windows and calls of the
  run, windows scored so far out of all complete windows since `--from`, final months).
- **Resumable:** `data/backfill-state.json` records published observation months,
  finished `model|window` pairs and scored windows. A run stops at `--max-calls` or at
  Open-Meteo's daily limit, keeps what it fetched, and the next run continues. The
  same holds when Open-Meteo keeps failing: server errors, network errors and answers
  that are not JSON (once an empty answer to a request mid-run, 12 Oct 2026) are retried
  after 30, 60 and 120 s, and if they persist the run stops cleanly with the reason in
  its summary instead of failing and losing the window's forecasts fetched so far.
- A month whose observations came from `now/` only (not yet published) is not final:
  its windows are fetched but scored only once ČHMÚ publishes the month.
- With `--github-release` the month files and the state are pulled from and pushed to
  GitHub Releases (`data-YYYY-MM`, state in `data-state`) after every window, so the
  scheduled workflow `.github/workflows/backfill.yml` (daily, 6,800 calls, leaving room
  for the outlook and the single runs, see the [budget split](#open-meteo-budget)) can continue
  from any machine.
- Budget: about 6,900 calls per window for all ~500 stations and 11 models, plus about
  1,550 for the rain gauges (measured on the first real runs, 12 Oct 2026: 5,913 + 3,785
  calls for the newest window), so about one window a day with 8,500 calls (since
  2026-10-13 the daily budget is 6,800, so a little less than one); 2024-01-01
  to now is about 70 windows, fewer models in older ones (archive starts), i.e. about
  two months. The free tier counts calls per IP address and GitHub's runners share
  addresses, so a run can meet the daily limit early; it then stops cleanly. ČHMÚ
  downloads are about 2.5 GB per month of history. Checked live on 3 stations × one
  window (41 calls, 6,270 score rows; a second run did nothing).
- **Rain gauges** (the ~280 manual gauges; closed stations are already verified
  hourly): precipitation forecasts only, for 28-day windows counted from `--from`
  (two 14-day windows; progress key `gauges|model|start|end`). With at most 5 lead
  days that is at most 5 variables, so 28 days still cost one call per location: about
  3,100 calls per 28 days for 11 models, roughly +22 % on the station forecasts. The
  newer 14-day window fetches its 28-day gauge window and re-scores both halves, so
  windows scored before the gauges were added get them too. Gauge observations come
  from `recent/` per month into `data/gauges`; a month is final once it ended 62 days
  before `--to` (manual readings arrive about a month late), newer ones are refreshed
  by the daily run.

## Daily pipeline (`mvd daily`)

Run every morning by `.github/workflows/daily.yml` (05:17 UTC, after the backfill, same
concurrency group because both write release assets). No Open-Meteo calls.

1. Pull the months of the last 100 days from the releases.
2. Capture the last 3 days of observations from `now/` (the current month reaches
   `recent/` only after it ends), and read the rain gauges' months of the last 62 days
   again from `recent/` (about 280 small files a month), as the manual readings arrive.
3. Re-score the last 100 days, so captured observations, forecast windows completed by
   the backfill, and checked data replacing unchecked data all reach the scores.
4. Push changed months, pull all score months, aggregate and rank, write `site/data`
   and `site/data/badge.json`, and replace `aggregates.parquet` and `site-data.zip` in
   the release `data-latest`.
5. The workflow commits `site/data/badge.json` and `site/data/meta.json` (the README
   no longer has a generated leaderboard; roadmap 6.14).
   The score JSON is only in `data-latest` and on GitHub Pages: even the summary levels
   are about 3 MB a day (first real data, October 2026), too much for the git history.

Freshness: forecasts up to 2 weeks behind (complete backfill windows); observations
daily (unchecked first, replaced by checked data once ČHMÚ publishes the month).

## Data quality (`mvd check`)

Run by the daily workflow after `mvd daily` and before the commit. An **error** fails
the run, so GitHub notifies the owner and nothing is committed; the report
also appears on the run page (job summary).

| Check | Error | Warning |
|---|---|---|
| newest observation | older than 30 h | |
| newest forecast, newest score | older than 21 days (complete backfill windows lag up to 15) | |
| stations reporting in the last 3 days, of those that reported in the last 30 | under 80 % | the stations missing |
| temperature MAE per station over 90 days (all models) | | above 3 x the network median and above 3 °C: sensor or metadata problem |

Before that, observations outside physically plausible limits are dropped when they are
read: temperature −50…50 °C (Czech records −42.2 and 40.4 °C), wind 0…75 m/s, hourly
precipitation 0…120 mm.

## Raw data store

`mvd store upload` and `mvd store download --from YYYY-MM [--to YYYY-MM]` keep
`data/{obs,gauges,fc,scores}/YYYY-MM.parquet` as the assets
`{obs,gauges,fc,scores}-YYYY-MM.parquet`
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
| `published` | when ČHMÚ published the run (UTC): the latest HTTP `Last-Modified` of the four files read; null in files archived before 2026-10-13 and if the server sends no header |

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

**Publication time.** opendata.chmi.cz (nginx) sends `Last-Modified` with every file,
and the directory listing shows the same time to the minute (checked 2026-10-13: the
listing's `12-Oct-2026 10:24` for `…2026101206_CLSTEMPERATURE.grb.bz2`, header
`Mon, 12 Oct 2026 10:24:09 GMT`). Over the runs of 2026-10-11 to 2026-10-13 the four
fields we read appeared on the 1 km domain, after the run's start: 00 UTC run 3 h 30–3 h 34, 06 UTC
4 h 24–4 h 25, 12 UTC 3 h 13–3 h 14, 18 UTC 4 h 22–4 h 25 (the Lambert domain's
temperature a few minutes earlier than its precipitation). Since 2026-10-13 the archive
stores this as `published`; readers of older files get null (polars
`concat(how="diagonal_relaxed")`). It is not used in any score yet; it is there for a
later "what could a user actually see" score (the newest run published before the
time of use).

ČHMÚ's checked station observations stay online (`recent/` the last 12 months,
`historical/` all closed years), but the unchecked 10-minute and hourly data of `now/`
are kept for only about three days; the [ČHMÚ archive](#chmi-archive) keeps them, and
everything else ČHMÚ publishes for the stations.

<a id="chmi-archive"></a>

## ČHMÚ archive

`mvd chmi-archive` (module `meteoverdict.chmi_archive`) keeps **every element of every
station in every resolution** that ČHMÚ publishes under `meteorology/climate/`, also
what the scores do not use. What exists and how big it is: [chmi-data.md](chmi-data.md).
Licence CC BY 4.0, ČHMÚ; the values are unchanged, only converted from JSON to Parquet.

### Format

Every file has the same long table, one row per station, time and element (and, for
the statistics, time function and statistic), sorted by `station`, `resolution`,
`time`, `element`, `vtype`, `func`; zstd-compressed Parquet with column statistics, so
a reader can filter by station or time without reading everything:

| Column | Type | From ČHMÚ |
|---|---|---|
| `station` | string | `STATION` (WIGOS id) |
| `resolution` | string | `10min`, `1hour`, `daily`, `pentadic`, `monthly`, `yearly`, `phenomena` |
| `time` | timestamp (ms, UTC) | `DT` (end of a 10-minute or hourly interval, ČHMÚ's daily stamp); for statistics the start of the period: pentade *p* of a month starts on day 5(*p*−1)+1, a month on the 1st, a year on 1 January; phenomena the day at 00:00 |
| `element` | string | `ELEMENT`, or `PHENOMENON` (e.g. `BO`) |
| `vtype` | string | daily `VTYPE` (`AVG`, `SUM`, `06:00`, …) or `TIMEFUNCTION` of the statistics |
| `func` | string | `MDFUNCTION` of the statistics (`AVG`, `MAX`, `MIN`, `SUM`, `GE(30)` = number of days ≥ 30, …) |
| `value` | float32 | `VAL` / `VALUE`; null where ČHMÚ sends `""` (missing, quality 4); null for phenomena |
| `flag` | string | `FLAG` (meanings in `meta3`), or `FLAG_REPEAT` of the statistics |
| `flag2` | string | `FLAG_INTERRUPTED` of the statistics |
| `quality` | uint8 | `QUALITY` (`meta4`: 0 good, 1 suspect, 2 poor, 3 estimated, 4 missing, 5 unknown = not checked yet) |

Recent monthly and pentadic files have no `YEAR`/`MONTH` columns; they come from the
file name. ČHMÚ's missing rows (`""`, quality 4) are kept: they say a value was
expected.

### Files and releases

Each file is an asset of a GitHub release of this repository (labels hold the SHA-256);
`mvd chmi-archive --out-dir DIR` writes the same layout to a disk,
`DIR/<release>/<file>`:

| Release | Files | What | Size |
|---|---|---|---|
| `chmi-now-YYYY` | `chmi-now-YYYY-MM-DD.parquet` | one UTC day, 10-minute and hourly rows of all stations as first published (from `now/`, mostly not checked; from `recent/`'s day files if the day already left `now/`) | ~0.8 MB a day |
| | `chmi-meta-YYYY-MM-DD.zip` | `meta1`…`meta4` of that day as published (JSON) | ~55 kB |
| `chmi-YYYY` | `chmi-10min-YYYY-MM.parquet`, `chmi-1hour-YYYY-MM.parquet` | one month of all stations, checked (`historical/` for closed years, else `recent/`) | 10 min ~21 MB, 1 h ~1.2 MB |
| | `chmi-{daily,monthly,pentadic,phenomena}-YYYY-MM.parquet` | one month of all stations from `recent/`, for months not in the station histories yet (the current year; the current month grows daily) | < 2 MB |
| `chmi-history-D` (D = last digit of the WSI) | `chmi-history-<WSI>.parquet` | all closed years of one station: daily, monthly, pentadic, yearly and phenomena (`historical/`), back to 1775 | 0.1–5 MB, ~1 GB for 1,550 stations |
| `chmi-state` | `chmi-archive-state.json` | progress: for each month and station, a fingerprint of the ČHMÚ files it was built from | small |

Per-station history files (not per year) because that is how ČHMÚ publishes the
closed years (one file of up to 100 MB per station), which makes the backfill
resumable station by station and gives the station pages one file per station.
Ten releases keep each under GitHub's 1,000 files. A year in both a station history
and `chmi-…-YYYY-MM` month files (after ČHMÚ's yearly update) is the same data; the
history is the reference.

Reading it (after `mvd chmi-mirror DIR`):

```python
import polars as pl

libus = pl.read_parquet("DIR/chmi-history-0/chmi-history-0-20000-0-11520.parquet")
t = (
    pl.scan_parquet("DIR/chmi-2025/chmi-10min-2025-*.parquet")
    .filter(pl.col("station") == "0-20000-0-11520", pl.col("element") == "T")
    .collect()
)
```

### Units of work and schedule

Work is split into units, one file each, done in this order (newest first) until the
time budget (`--max-minutes`) is used up; the state remembers each unit's fingerprint
(names, sizes and dates in ČHMÚ's directory listing), so a unit is done again only
when ČHMÚ changes its files, and a stopped run resumes with the next unit:

| `--part` | Unit | When |
|---|---|---|
| `days` | a complete UTC day not archived yet | `chmi-archive.yml`, 01:41 and 13:41 UTC (two chances per day; `now/` keeps ~3) |
| `recent` | a month of one resolution in `recent/` whose files changed | same runs; daily data change every day, 10 min and 1 h after ČHMÚ's checks (the 3rd of the month) |
| `history` | one station's closed years | `chmi-backfill.yml`, 02:07 UTC, 5 hours a run |
| `months` | a closed month of 10-minute or hourly data (2018 on, hourly first) | same |

Both workflows share the concurrency group `chmi-archive`, so they never write the
state at the same time; neither calls Open-Meteo. Downloads use 4 parallel
connections and the retries of `mvd fetch-obs` (2, 5 and 15 s on network or server
errors and unreadable bodies). A listed file that still cannot be read (ČHMÚ
sometimes serves an empty body) is left out and counted in the run's summary
("unreadable files left out"), like a missing station-day in `mvd fetch-obs`.

**Backfill estimate** ([details](chmi-data.md#what-the-archive-costs)): about 157 GB of
JSON to download, about 3.1 GB of Parquet stored; at the measured 2–8 MB/s about 6–9
hours, i.e. two or three daily runs. Then about 0.6 GB a year.

```bash
uv run mvd chmi-archive --part days --out-dir data/chmi           # the last days
uv run mvd chmi-archive --part history --station 0-20000-0-11520 \
    --out-dir data/chmi                                         # one station's history (a trial)
uv run mvd chmi-mirror /Volumes/disk/chmi                         # copy the archive (needs GITHUB_TOKEN)
```

`--station` limits `recent`, `history` and `months` to some stations, for trials; the
files are then partial, so the state is not saved.

<a id="station-pages"></a>

### Station pages

`mvd station-pages` (module `meteoverdict.station_pages`) writes one JSON per station
for `web/station.html`, from the archive (`--github-release` first downloads the files it
needs into `--archive`, default `data/chmi`; `--publish` uploads the folder as
`station-data.zip` to `data-latest`, which the Pages workflow unpacks into
`data/scores/station/`):

- `station/index.json`: `{"generated", "stations": [{id, name, okres, elevation,
  active, views}]}` for the search;
- `station/<WSI>.json`: `station` (from `mvd stations`), `elements` (from ČHMÚ's
  `meta2`: Czech name, unit, sensor height, kinds `10M`/`1H`/`DLY`/`PHENO`, first and
  last day, and the `views` that have it), `series` and `source`.

Each series is `{"start", "step", "values": {element: [...]}, "how": {element: label}}`;
value *i* is at `start + i × step`, null where there is none, rounded to 0.1:

| View | Step | Covers | From |
|---|---|---|---|
| `10min` | 10 min | the last 3 days up to the newest value | month files, else the captured days |
| `1hour` | 1 h | the last 30 days | hourly elements, and 10-minute elements at the full hour (not `SRA10M`, `SSV10M`, whose hourly totals are `SRA1H`, `SSV1H`) |
| `daily` | 1 day | the last 3 years and this one | station history, then the recent month files after it; one series per element: the daily mean (`AVG`) where there is one, else the sum, else the only observation time |
| `monthly` | 1 month | the whole history | ČHMÚ's monthly statistics: the mean (`AVG AVG`) where there is one, else the total, maximum or minimum; `how` says which |

Sizes (measured 2026-10-15): Praha-Libuš 469 kB (10 min 37, hourly 196 with 35
ceilometer elements, daily 149, monthly 69), Brno-Tuřany 380 kB, Lysá hora 507 kB
(118, 100 and 106 kB gzipped as GitHub Pages serves them); the 10-minute and hourly
part of all 476 automatic stations 28 MB. Estimated for all ~780 stations: about
120 MB (≈ 40 stations with hourly synoptic elements at ~0.5 MB, ~440 automatic stations
at ~0.2 MB, ~300 rain gauges at ~0.05 MB); at most 0.4 GB even if every station were
as big as Lysá hora, well under GitHub Pages' 1 GB. Building all of them took 16 s
and 2 GB of memory.

## Single runs (`mvd fetch-runs`)

Open-Meteo's **Single Runs API** returns one model run as it was issued, which the
Previous Runs API (D+N, above) cannot: there each hour mixes runs. Checked live on
2026-10-13 without an API key (free tier):

- Endpoint `https://single-runs-api.open-meteo.com/v1/forecast`, the Forecast API's
  parameters plus `run=YYYY-MM-DDTHH:MM` (the run's **start**, UTC). Several models per
  request (`models=a,b,c`, columns `<variable>_<model>`) and several locations
  (comma-separated `latitude`, `longitude`, `elevation`; a JSON list, `location_id` on
  all but the first) work as in the other APIs, and `elevation` is used for the
  elevation correction as there.
- The answer starts at the run's start (lead 0); `forecast_hours=121` gives leads 0 to
  120 (`forecast_days=N` gives N × 24 hours from the run's start). Lead 0 is not stored.
- If **any** requested model does not have that run, the whole request fails: HTTP 400
  `{"error":true,"reason":"The requested model run is not available. Model: X, run: …"}`.
  X is Open-Meteo's internal name, which can differ from the id we ask for:
  `dwd_icon_d2_native`, `dwd_icon_eu_native`, `ncep_gfs013` (for `ncep_gfs_global`); the
  others report their own id. `mvd fetch-runs` drops X and asks again for the rest.
- A model without data at one location (ICON-D2 in the far east) is **left out of that
  location's answer** instead of failing the request; if only one model is left, the
  columns lose their model suffix (`temperature_2m`). A one-model request fails there
  with "No data is available for this location", as in the Previous Runs API.
- Every model has every 00, 06, 12 and 18 UTC run. Horizons seen (temperature, lead
  hours with a value, runs of 2026-10-12): ALADIN (both) 72; ICON-D2 48; GeoSphere
  AROME 60; ARPEGE Europe 102; ICON-EU, IFS HRES, IFS 0.25°, AIFS and GFS 120 (asked
  for); UK Met Office 120 from 00 and 12 UTC, 60 from 06 and 18 UTC. AIFS (6-hourly)
  and IFS 0.25° (3-hourly) come with every hour filled, so the hours in between are
  interpolated, as in the Previous Runs API.
- **Archive start:** the 2026-04-02 00 UTC runs are there for every model except ALADIN,
  the 2026-04-01 12 UTC runs only for IFS HRES (the docs say IFS HRES from 2024-03-14).
  ALADIN (both domains) from the **2026-06-23 00 UTC** run (2026-06-22 18 UTC is missing;
  `runs_from` in models.yaml). Gaps after that are possible (KNMI, not used, misses
  2026-09-01 12 UTC).
- **Delivery:** at 14:25 UTC on 2026-10-13 the 06 UTC run (8.4 h old) was complete for
  all 11 models, the 12 UTC run only for ICON-D2. So a run is fetched once it is
  **10 hours** old.

### The station subset

Asking every run at all ~500 stations would cost about 1,650 calls a run, 6,600 a day.
We use about 100 stations instead (`src/meteoverdict/data/run-stations.csv`, committed,
so the set does not change from run to run). The rule (`runs.select_stations`,
regenerated with `uv run scripts/build_run_stations.py`):

1. **One per okres** (all 77): among the okres's active stations, those with the most of
   our three elements at 10 minutes in ČHMÚ's `meta2` (`T`, `F`, `SRA10M`), and of
   these the one closest to the okres's forecast point (the same point as the outlook).
   Blansko has only precipitation stations, so its station verifies precipitation only.
2. **Mountains:** every other station with all three elements above 800 m (13).
3. **Spread** up to 100: repeatedly the full station farthest from all chosen ones,
   counting 100 m of height difference as 10 km (10 stations).

Ties go to the lower WIGOS id. Result on 2026-10-13: 100 stations in all 77 okresy,
47 lowland, 39 upland and 14 mountain, 99 with all three elements. The CSV records why
each station is in (`reason`: `okres`, `mountain`, `spread`).

### Fetching and storage

`mvd fetch-runs [--mode recent|history|all] [--run YYYY-MM-DDTHH …] [--max-calls N]
[--extra-calls-if-backfill-idle N [--backfill-from 2024-01-01]] [--history-from D]
[--github-release] [--dry-run]`:

- **One request per run** for all 100 stations and all enabled models (11),
  `hourly=temperature_2m,precipitation,wind_speed_10m`, `forecast_hours=121`,
  `wind_speed_unit=ms`, with each station's elevation. Retries, the daily limit and
  persistent failures behave as in `mvd fetch-fc` (`forecasts.request`); a run stopped by
  the budget or by Open-Meteo is not kept and is asked again next time.
- **Cost** (Open-Meteo's formula: locations × max(1, variables × models / 10 ×
  max(1, days / 14))): 121 hours count as 6 days, under 14, so the whole 5 days cost the
  same as one day: **3 × 11 / 10 = 3.3 calls per station, 330 a run** (270 for the runs
  before 2026-06-23 without ALADIN). Measured on the first real runs (2026-10-13, our
  budget counter): 330 for each of 2026-10-10 00 and 12 UTC, 2026-07-15 00 UTC and
  2026-10-13 00 UTC, 270 for 2026-04-15 12 UTC. A model that has to be asked again on
  its own costs at least 1 per station (100). Requests that fail count too (we do not
  know whether Open-Meteo counts them).
- **Order:** "recent" runs first (all runs between 10 and 48 hours old not done yet:
  ongoing collection, missed schedules catch up), then "history" newest first back to
  **2026-06-23 00 UTC** (`runs.HISTORY_FROM`, `--history-from` to change it). `--run`
  fetches only the given runs.
- **Why the history stops at 2026-06-23:** it is the first run with ALADIN (both
  domains) in the archive. The runs from 2026-04-02 to 2026-06-22 have only 9 of the 11
  models, so on the fair common set (every model verified on the same runs, stations
  and hours) they add nothing for ALADIN and little for the others, yet they are about
  330 more runs (~89,000 calls, at 270 a run). They can still be fetched with
  `--history-from 2026-04-02` or `--run`.
- **Gaps:** a model Open-Meteo does not have for a run older than 24 hours is recorded as
  missing for good; for a younger run it is asked again later (models arrive at
  different times).
- **Rows:** `data/runs/YYYY-MM.parquet` by the month of the run's start, one row per
  `run`, `model`, `station_id`, `lead_h` (1–120) with `valid_time` (= run + lead),
  `temperature_2m` (°C), `precipitation` (mm in the hour ending at `valid_time`) and
  `wind_speed_10m` (m/s), sorted by run. About 107,000 rows and 0.31 MB a run, so about
  38 MB a month.
- **State:** `data/runs-state.json`: per run (`YYYYMMDDHH`) the models fetched and the
  models missing.
- **Release storage** (`--github-release`): the month files as `runs-YYYY-MM.parquet` in
  the releases `runs-YYYY-MM` (a family of their own, CC BY-SA 4.0 like the other data
  files), the state as `runs-state.json` in the release `runs-state`; labels hold the
  SHA-256 so unchanged files are skipped. The month file is pulled before a run is
  added to it and pushed after each run. Only `runs.yml` writes these releases, so it
  has its own concurrency group; `mvd leads` in the daily workflow only reads them.
- **Schedule** (`.github/workflows/runs.yml`): at 04:20, 10:20, 16:20 and 22:20 UTC,
  10 h 20 min after each run. Each scheduled run normally fetches the newest run; the
  10:20 run has a larger budget and also fills about one older run. When the backfill
  is idle, 10:20 and an extra run at 13:20 take its share for the history (below).

### Open-Meteo budget

All workflows share the free tier's 10,000 weighted calls a day, 5,000 an hour and
300,000 a month (per IP address; GitHub's runners share addresses, so a run can still
meet the daily limit early and then stops cleanly). Each workflow has its own call
budget (`--max-calls`); `forecasts.Budget` also paces one run below 4,800 an hour.

**While the D+N backfill has work** (until about early January 2027):

| Workflow | Calls a day | In 31 days |
|---|---|---|
| Backfill (`backfill.yml`, once a day) | 6,800 | 210,800 |
| Outlook (`outlook.yml`, 2 × ~420) | ~850 | ~26,400 |
| Single runs (`runs.yml`, 3 × 350 + 750) | 1,800 | 55,800 |
| **Total** | **~9,450** | **~293,000** |

The monthly limit is the tighter one: 10,000 a day would be 310,000 in a 31-day month.

**Handover.** Once the backfill has caught up, it needs one new 14-day window every 14
days (~6,900 calls, plus ~3,100 for the rain gauges' 28-day window with every other
window), i.e. two days of its 6,800 and nothing on the other twelve. On those days its share goes to
the single-runs history: `mvd fetch-runs --extra-calls-if-backfill-idle N` adds N to
`--max-calls` only when `backfill.handover` says the backfill is idle, from the
backfill's own state (`backfill-state.json` in the release `data-state`, read-only):

- no complete 14-day window since `--backfill-from` (2024-01-01, as in `backfill.yml`)
  up to yesterday still needs Open-Meteo forecasts (`backfill.pending_windows`, the
  same rule as `mvd backfill`: station forecasts of every enabled model from its
  archive start, and the rain-gauge forecasts of the 28-day window). A window fetched
  but waiting for ČHMÚ to publish the month's observations needs no Open-Meteo calls,
  so it does not block the handover. A newly enabled model makes every window pending
  again, which stops the handover by itself;
- no window becomes due tomorrow (one ending today): the day before the backfill's
  big day stays normal, so the extra calls and the backfill's 6,800 are always more
  than 24 hours apart (also safe if Open-Meteo counts a rolling 24 hours);
- the backfill did not call Open-Meteo today (UTC; `calls_on` in its state, written
  whenever it asks for forecasts), so a day on which it finished a window this
  morning stays normal;
- if the state cannot be downloaded or read, the normal budget is used.

The job summary of every single-runs run states the budget used and why (for example
"3750 calls (750 normal + 3000 extra: backfill idle (all 72 complete windows since
2024-01-01 fetched))" or "750 calls (normal; extra 3000 not used: 70 backfill windows
pending (newest 2024-…))").

In `runs.yml` the 10:20 run (after the backfill at 02:41 and the daily run at 05:17)
gets +3,000 and a run at 13:20 gets 3,000 (nothing when the backfill is not idle): two
runs of at most 3,750 and 3,000 in different hours, under the 5,000 an hour.

| Day | Backfill | Outlook | Single runs | Total |
|---|---|---|---|---|
| Backfill has work | 6,800 | ~850 | 1,800 | ~9,450 |
| Backfill idle (handover) | 0 | ~850 | 1,800 + 6,000 | ~8,650 |
| New window due tomorrow | 0 | ~850 | 1,800 | ~2,650 |
| Backfill finishes a window | ≤ 3,200 | ~850 | 1,800 | ≤ ~5,850 |

No day exceeds ~9,450, so no month exceeds 9,450 × 31 = ~293,000, in either regime; the
idle day leaves ~1,350 a day for the outlook (user-facing) and for requests that are
retried. A typical 28-day cycle after the backfill (two windows, one with the gauges):
per window 1 day before it (2,650), 1 day of the window (9,450) and 1 day finishing it
(2,750 without the gauges, 5,850 with them), plus 22 idle days (22 × 8,650 = 190,300):
about 223,000 in 28 days, ~8,000 a day, ~247,000 in 31 days. Once the run history is
complete the extra budget is simply not spent (~2,700 a day in all).

**How long the history takes.** From 2026-06-23 00 UTC to now (2026-10-14) there are
about 450 runs older than the recent ones (446 at 10:20 UTC), at 330 calls ≈ 147,000
calls (not counting the four new runs a day, which the normal budget covers: 4 × 330 =
1,320 of its 1,800).

- **Normal budget only:** the 480 left a day are usable only at 10:20 (750 − 330 = 420,
  one run; the 350-call runs have 20 left), so about **one history run a day**: ~450
  days, i.e. not before early 2028 (back to 2026-04-02 it would be ~770 runs, over two
  years).
- **Until the backfill finishes** (70 of 72 windows pending on 2026-10-14; at most
  ~8,450 calls a window on average with the gauges, fewer for the older windows with
  fewer models; 6,800 a day: ~75–90 days, i.e. early January 2027): ~85 history runs,
  ~360 left.
- **After the handover:** on an idle day 10:20 fetches the newest run and 10 older ones
  (3,750 / 330), 13:20 another 9 (3,000 / 330): ~19 history runs a day; with 11 idle
  days out of 14 that is 11 × 19 + 3 × 1 = ~212 runs in 14 days, ~15 a day. The ~360
  runs left take **about 24 days**, so the history back to 2026-06-23 is complete
  around **early February 2027** (instead of early 2028).

## Error by lead hour (`mvd leads`)

Run-based verification (see [methodology](methodology.md#run-based-verification-by-lead-hour)
for what it means). `meteoverdict.leads` has two parts.

### Every model, from the single runs (`leads.json`)

1. Reads the single runs started in the last `--runs-days` days (default 90) from
   `data/runs/` (with `--github-release` it first downloads changed months from the
   releases `runs-YYYY-MM`, and the observation months from `data-YYYY-MM`).
2. Per model, run, station and lead hour 1–120: temperature and wind as given (instant
   values at `valid_time`), precipitation as given (Open-Meteo's hourly value, mm in
   the hour ending at `valid_time`, no differencing). Only **native output hours** are
   scored: AIFS every 6 h, IFS 0.25° every 3 h, ICON-EU after 78 h, IFS HRES after 90 h
   and UK Met Office after 54 h every 3 h (`step_hours`, `coarser_after_h` in
   models.yaml); hourly precipitation only where the output is hourly.
3. **Fair set.** A model's horizon per run hour is the median over its runs of the last
   lead hour with a temperature. For each run hour (00, 06, 12, 18 UTC), lead hour and
   variable, the *required* models are those whose horizon reaches the lead with a
   native output hour; only the (run, station) pairs where every required model has a
   value (and the observation exists) are scored. For "all" run hours a model must reach
   the lead in every run hour (UK Met Office therefore ends at 60 h there, ARPEGE at
   102 h). So the set of models shrinks with the lead hour, and a model missing from a
   run takes that run out of the comparison at the leads it would reach (like the D+N
   rule: models whose archive starts later — ALADIN, 2026-06-23 — limit the common
   sample).
4. Sums errors per run hour stratum (`all`, `00`, `06`, `12`, `18`), model, variable
   and lead hour, 24 runs at a time (the sums are additive, so months of runs fit in
   memory), plus the 2×2 counts for ≥ 0.1 mm in the hour.

`site/data/leads.json` (with `--publish` also in the release `data-latest`, from where
the Pages build takes it):

| Key | Meaning |
|---|---|
| `generated`, `first_run`, `last_run` | UTC, `YYYY-MM-DDTHH:MMZ` |
| `source`, `about`, `fair_set` | where the data come from and the comparison rule |
| `stations` | stations with at least one pair |
| `models` | per model: `name`, `runs` and `pairs` used (run hour "all"), `horizon_h` per run hour, `publication_delay_h` (ALADIN only, from our archive; null for the others) |
| `variables`, `region`, `regions` | units; Czechia only (`cz`) |
| `columns`, `rows` | one row per `run_hour`, `model`, `variable`, `lead_h`: `runs`, `stations`, `n`, `mae`, `bias`, `rmse` (3 decimals), `a_0p1`, `b_0p1`, `c_0p1`, `d_0p1` (precipitation only) |

About 0.6 MB with two run hours (6,586 rows: "all", 00 and 12 UTC), about 1 MB with all
four (≈ 11,000 rows); no kraj file
(100 stations are only about 7 per kraj).

First real numbers, 2026-10-13: 5 runs (2026-04-15 12, 2026-07-15 00, 2026-10-10 00 and
12, 2026-10-13 00 UTC), observations of 99 stations from `recent/` (April, July) and
`now/` (2026-10-11 00 to 2026-10-13 13 UTC; `now/` no longer had 2026-10-10). Temperature
MAE in °C, all run hours (runs, pairs per model):

| Model | H+1 | H+6 | H+12 | H+24 | H+48 | H+72 |
|---|---|---|---|---|---|---|
| ALADIN CZ 1 km | 1.33 | 1.58 | 1.13 | 1.23 | 1.12 | 1.67 |
| ALADIN CE 2.3 km | 1.35 | 1.57 | 1.13 | 1.23 | 1.12 | 1.70 |
| ICON-D2 | 1.06 | 1.20 | 1.07 | 1.17 | 1.12 | – |
| GeoSphere AROME | 1.43 | 1.73 | 1.22 | 1.12 | 1.36 | – |
| ICON-EU | 1.41 | 1.54 | 1.20 | 1.18 | 1.20 | 1.59 |
| ECMWF IFS HRES | 1.48 | 1.57 | 1.10 | 1.18 | 1.22 | 1.40 |
| ECMWF IFS 0.25° | – | 1.73 | 1.14 | 1.21 | 1.23 | 1.45 |
| ECMWF AIFS | – | 1.51 | 1.15 | 1.17 | 1.25 | 1.37 |
| NOAA GFS | 2.28 | 2.47 | 1.26 | 1.49 | 1.31 | 1.79 |
| UK Met Office | 1.61 | 1.59 | 1.27 | 1.17 | 1.29 | 1.70 |
| ARPEGE Europe | 1.53 | 1.50 | 1.01 | 1.35 | 1.24 | 2.01 |
| runs (pairs per model) | 2 (194) | 2 (193) | 3 (288) | 3 (289) | 3 (291) | 3 (292) |

(– : no native output at that hour, or the model has ended.) The April run has no
ALADIN, so it counts only beyond H+72. Five runs of three weather situations: a check
that the pipeline works, not a result.

### ALADIN from our own archive (`leads-aladin.json`)

1. Reads the archived runs of the last `--days` days (default 30) from
   `<archive-dir>/aladin-YYYY-MM/*.parquet` (with `--github-release` it first downloads
   the missing ones from the releases `aladin-YYYY-MM`; files already there are kept).
2. Per model, run, station and lead hour 1–72 (lead 0, the analysis, is left out):
   temperature and wind as stored (instant values at `valid_time = run + lead_h`);
   precipitation as `precipitation_accum(h) − precipitation_accum(h − 1)`, i.e. mm in
   the hour ending at the valid time (lead 1 = its accumulation, as there is none at
   lead 0; small negative differences from GRIB packing → 0; missing previous lead →
   no value).
3. Joins the observations (`data/obs`, same conventions as the D+N scores: T and F at
   the full hour, precipitation summed over the hour ending there) on station, valid
   time and variable, and keeps only the run, station, lead hour and variable that
   **both** domains have, so they are compared on the same sample.
4. Sums errors (`metrics.error_sums`) and, for precipitation, the 2×2 counts for
   ≥ 0.1 mm in the hour, per lead hour: for Czechia over all runs and per run hour
   (00, 06, 12, 18 UTC), and per kraj over all runs.

`site/data/leads-aladin.json` (Czechia) and `site/data/leads-aladin-kraj.json` (kraje),
with `--publish` also in the release `data-latest` (until 2026-10-13 these were
`leads.json` and `leads-kraj.json`). Same keys as `leads.json` plus a `region` column
(`cz` or a kraj NUTS 3 code) and `regions`. The web page shows the all-model file; this
one stays as a check of Open-Meteo's ALADIN (nearest grid point, no elevation
correction, all ~290 stations) and it is where the **publication time** comes from:
the median delay from run start to `published` per ALADIN domain goes into
`leads.json` (`publication_delay_h`) and shades the hours not yet published on the
chart. About 230 KB for Czechia (2,160 rows), 650 KB for the kraje.

First real run, 2026-10-13 (runs 2026-10-09 00 UTC to 2026-10-13 06 UTC, 18 per
domain; observations from `now/` for 2026-10-10 00 UTC to 2026-10-13 12 UTC, as
`now/` no longer had 2026-10-09; 291 stations with temperature): temperature MAE in °C

| | H+1 | H+6 | H+12 | H+24 | H+48 | H+72 |
|---|---|---|---|---|---|---|
| ALADIN CZ 1 km | 0.93 | 1.11 | 1.11 | 1.10 | 1.27 | 1.61 |
| ALADIN Central Europe 2.3 km | 0.99 | 1.17 | 1.17 | 1.15 | 1.31 | 1.62 |
| runs (pairs per domain) | 14 (4,041) | 15 (4,327) | 15 (4,327) | 15 (4,327) | 11 (3,174) | 7 (2,023) |

Four days of one October spell: an illustration that the pipeline works, not a result.

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
  429 with "Daily API request limit exceeded"; the minute and hour limits, HTTP 5xx,
  network errors and answers that are not JSON are retried. Days before a model's archive start
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
| `dwd_icon_d2` | lat 43.18–58.08, lon −3.94–20.34 | **not the far east**: no data for 6 stations east of about 18.6° E (live check, see below) |
| `dwd_icon_eu` | lat 29.5–70.5, lon −23.5–62.5 | covered |
| `meteofrance_arpege_europe` | lat 20–72, lon −32–42 | covered |
| `geosphere_arome_austria` | lat 42.98–51.82, lon 5.50–22.10 | covered |
| `knmi_harmonie_arome_europe` | rotated grid, 676 × 564 × 0.05° | covered |
| `dmi_harmonie_arome_europe` | Lambert conformal, 1906 × 1606 × 2 km | covered |
| `meteofrance_arome_france` | lat 37.5–55.4, lon −12.0–16.0 | **partly** (not east of 16° E): excluded |
| `italia_meteo_arpae_icon_2i` | lat 33.7–48.9, lon 3–22 | **only the far south**: excluded |

**Live check (2026-10-12):** all ~500 verified stations were requested from each
regional model (ALADIN CZ 1 km and CE 2.3 km, ICON-D2, GeoSphere AROME, ARPEGE Europe).
Only ICON-D2 answered "No data is available for this location", for 6 stations in the
Beskydy (`0-203-0-11792`, `0-203-0-20303008001`, `0-203-0-20303018003`,
`0-203-0-20303019001`, `0-203-0-20303032003`, `0-203-0-42106052001`; lon 18.63–18.83).
The grid rectangle in Open-Meteo's code is wider than the area with data, so the
5-point grid check above was not enough. `mvd fetch-fc` splits a request that fails this
way until it finds such stations and skips them (`uncovered`, kept in the backfill
state); scoring compares models per station among the models covering it.

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
