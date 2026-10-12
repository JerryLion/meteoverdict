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
| `now/data/` | current-day 10-minute (`10m-…`) and hourly (`1h-…`) files | regenerated hourly and overwritten; files older than 24 h are deleted |
| `now/metadata/` | `meta1`…`meta4`, named `metaN-YYYYMMDD.json` | daily; deleted after 10 days |
| `recent/data/{10min,1hour,daily,monthly,pentadic,phenomena}/` | current year, month folders `01/`…`12/` | 10 min / 1 h: twice a day, and the previous two months are regenerated on the 3rd of each month; daily: after each day; monthly / pentadic: start of the next month, re-uploaded after two months |
| `historical/data/{10min,1hour,daily,monthly,pentadic,yearly,phenomena}/` | closed years; 10 min and 1 h data from 2018 | once a year, by the end of February |
| `historical/metadata/` | station and element metadata | once a year |
| `historical_csv/data/…` | the same as CSV, one file per element | once a year |

Implications for us:

- **Backfill (2.6)** reads `historical/` for closed years and `recent/` for the current
  year. `historical/` has 10-minute and hourly data from 2018, which covers our 2024+
  window.
- **Daily runs (3.2)** should read `recent/` (checked data, twice a day), not `now/`, and
  re-score the previous two months after the 3rd of each month, when ČHMÚ republishes
  corrected data.

### File names

`{WSI}` is the WIGOS Station Identifier (e.g. `0-20000-0-11520`, Praha-Libuš) and
`{PRVEK}` is the element code.

| Data | Pattern |
|---|---|
| `now/` and `historical/` 10 min / 1 h (JSON) | `10m-{WSI}-{YYYYMMDD}.json`, `1h-{WSI}-{YYYYMMDD}.json` (one file per station and day) |
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
2 Poor, 3 Estimated, 4 Missing, 5 Unknown). `now/` data is unchecked (`5.0`), `recent/`
data is checked (`0.0` for good values). The rows are long-format: one row per
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

**Open for 1.5:** 2 m temperature and 10 m wind are only in the 10-minute files, so 1.5
must decide the hourly sampling (value at the full hour vs. hourly mean) and whether
`F` or `Fprum` matches what Open-Meteo's `wind_speed_10m` represents.

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
