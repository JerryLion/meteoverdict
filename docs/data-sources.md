# Data sources

This page records what we verified about the external data, where it lives and under
which terms. Everything here was read on **2026-10-11**. Claims we could not verify are
marked **unverified**; do not build on them without checking.

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
| `recent/` 10 min / 1 h | "created the same way as `now/`" per the PDF; exact names **unverified** |
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
(string, often empty), `QUALITY` (number; we saw `4.0` and `5.0`, and their meaning is
listed in `meta4`). The rows are long-format: one row per station × element × time.

Which elements go where (from `meta2`'s `OBS_TYPE` column and real files):

- **Hourly (`1H`) elements** include `SRA1H` (precipitation, 1 h, mm), `P`, `E`, `Td`,
  `N`, `ww`, `VV`, `SSV1H` and the ceilometer `C-…` elements. **`T` and the wind
  elements are not listed as hourly elements for the station we checked (Cheb).**
- **10-minute (`10M`) elements** include `D`, `Dmax`, `Dprum`, `F`, `Fmax`, `Casmax`
  (all seen in `10m-0-20000-0-11520-20261011.json`). The PDF lists `T`, `SRA10M` and
  `SSV10M` as 10-minute elements, but we could not read that far into a file.
- Element names and units come from `meta2` (`NAME`, `UN_DESCRIPTION`). The PDF lists
  codes without definitions.

**Unverified / open for 1.5:** which exact element (and sampling) to use for hourly 2 m
temperature (`T` at the full hour from the 10-minute data?) and 10 m wind speed (`F` vs
`Fprum`, 10-minute mean at the full hour?). Settle this from `meta2` and real files,
ideally in CI, which has open internet.

### Metadata files

| File | Header (as seen in real files) | Notes |
|---|---|---|
| `meta1` (`now/`) | `WSI,GH_ID,FULL_NAME,GEOGR1,GEOGR2,ELEVATION,BEGIN_DATE` | stations operating today (about 530 rows on 2026-10-11). **`GEOGR1` is longitude, `GEOGR2` is latitude** (e.g. Cheb 12.39, 50.07). Elevation in m. The PDF omits `BEGIN_DATE`. It includes at least one non-Czech station (Reykjavik), so filter to Czechia. |
| `meta1` (`historical/metadata/meta1.json`) | `WSI,GH_ID,BEGIN_DATE,END_DATE,FULL_NAME,GEOGR1,GEOGR2,ELEVATION` | **one row per validity period**: a station's position and elevation can change between periods (Cheb has six). An open period ends at `3999-12-31T23:59:00Z`. Also lists closed stations. Note the different column order. The copy we read was created 2026-02-12, so it lags behind closures during the current year. |
| `meta2` | `OBS_TYPE,WSI,EG_EL_ABBREVIATION,NAME,UN_DESCRIPTION,HEIGHT,SCHEDULE` | elements measured per station, with sensor height in m. The PDF omits `OBS_TYPE` and `SCHEDULE`. |
| `meta3` | per the PDF: `EL_ABBREVIATION,FLAG,DESCRIPTION` | **unverified** |
| `meta4` | per the PDF: `FLAG2,DESCRIPTION` (quality codes) | **unverified** |

Neither `meta1` has an "active" flag. `mvd stations` (roadmap 1.2) treats a station
as active when it is in the current `now/metadata/meta1`, and takes its position from
there. Stations only in the historical file are kept as inactive at the position of
their last period, if that period ended on or after 2024-01-01. The historical file
is not reliable as the only source of "active": it is regenerated once a year.

Foreign stations also show up in the historical file, and not always with sensible
coordinates: Marambio (Antarctica) is listed at `GEOGR1` 56.62, `GEOGR2` 64.23, so
latitude and longitude look swapped and unsigned. A Czech bounding box filters them
out.

Small real excerpts are in `tests/fixtures/chmi/` (see the README there).

### Access notes

- Directory listings below `meteorology/climate/{now,recent,historical}/` often failed
  to load through our web reader (server errors or timeouts). Single files loaded
  fine. The fetcher should build URLs from the patterns above rather than scrape
  listings, and should retry.
- No authentication is needed.

### Licence and attribution

- The PDF and the server do not state a licence. The PDF only says these data replace
  data published under Act No. 123/1998 Coll. (on the right to environmental
  information).
- The ČHMÚ page ["Mohu získat vaše data pro svůj projekt?"](https://www.chmi.cz/-/mohu-z%C3%ADskat-va%C5%A1e-data-pro-sv%C5%AFj-projekt-)
  sends open-data users to opendata.chmi.cz and carries a **CC BY 4.0** badge in its
  footer. This suggests CC BY 4.0, but it is not an explicit statement for the dataset.
- **Status: likely CC BY 4.0, not confirmed.** Until confirmed, credit "Czech
  Hydrometeorological Institute (ČHMÚ), opendata.chmi.cz" wherever we show derived
  data. To confirm: the dataset's record in the National Open Data Catalogue (NKOD,
  data.gov.cz), or ask klima@chmi.cz.

## Open-Meteo Previous Runs API (forecasts)

Checked on **2026-10-11** against the Open-Meteo documentation and its source code
(open-meteo-website at `1755598c7ac9`, open-meteo server at `f625df2c2b2d`).
api.open-meteo.com is not reachable from the development sandbox, so **no live
request has been made yet**; the client (roadmap 1.6) will record real responses.

- Endpoint: `https://previous-runs-api.open-meteo.com/v1/forecast`, same parameters as
  the Forecast API (`latitude`, `longitude`, `elevation`, `hourly`, `models`,
  `start_date`/`end_date` or `past_days`).
- `<variable>_previous_dayN` is the value predicted 24·N hours before the valid time,
  N = 1…7; `_previous_day0` is the latest run. For models with a short forecast horizon
  only the offsets within the horizon are filled ("a model with a 3-day horizon will
  have at most `_previous_day3` populated").
- Variables with offsets include `temperature_2m`, `precipitation` and
  `wind_speed_10m`, the three we verify.
- Archive: "Most models are archived from **January 2024**. Some models were added to
  the archive later in 2024 or 2025 and have correspondingly shorter coverage." GFS 2 m
  temperature goes back to March 2021.
- Licence: CC BY 4.0. Non-commercial use is free under 10,000 calls a day; commercial
  use of this API needs the Professional subscription.

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
KNMI and DMI 2.5 days). `mvd models` derives the usable lead days from it, capped at D+5.
Lead days close to the horizon (e.g. ICON-D2 at D+2) may be only partly filled,
depending on run times; check this in the first live data.

**`archive_from` is a lower bound, not a verified start.** It is the later of
2024-01-01 and the day the model was added to the Open-Meteo server (first commit of
its domain code):

| Model | Added to Open-Meteo |
|---|---|
| ČHMÚ ALADIN CZ 1 km | 2026-06-10 |
| ČHMÚ ALADIN Central Europe 2.3 km | 2026-06-24 |
| GeoSphere AROME Austria | 2026-03-24 |
| ECMWF IFS HRES 9 km | 2025-09-30 |
| UK Met Office Global 10 km | 2024-08-12 |
| KNMI / DMI HARMONIE-AROME | 2024-07-04 |
| ECMWF AIFS | 2024-02-28 |
| ECMWF IFS 0.25° | 2024-02-04 |

Consequence: **ALADIN, the model this project most wants to evaluate, has at most a
few months of Previous Runs history (from June 2026)**, not the ~2 years assumed in the
roadmap. Long-window rankings must compare models over their common period (or label
windows per model). The real first available day of each model should be probed once
we have network access (roadmap 1.6 / 2.6).

Also note: AIFS has 6-hourly output and IFS 0.25° 3-hourly, so hourly scores for them
use fewer hours; ICON-EU, IFS HRES and UKMO become 3-hourly later in the forecast
(78 h, 90 h and 54 h).
