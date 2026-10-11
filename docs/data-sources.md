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

Covered in roadmap 1.3 (model coverage) and 1.6 (client). Licence: CC BY 4.0, free tier
non-commercial and under 10,000 calls a day. See ROADMAP.md, section "Data & licensing".
