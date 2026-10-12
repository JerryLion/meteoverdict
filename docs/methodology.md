# Methodology

How MeteoVerdict decides which weather model forecasts Czechia best, and what the
results can and cannot tell you. The technical details and the evidence behind each
data claim are in [data-sources.md](data-sources.md); this page explains the method
and its limitations.

## The question

For each place in Czechia (a station, an okres, a kraj, an elevation class, the whole
country) and each weather element: which model's forecast for the next days was
closest to what ČHMÚ measured?

## Observations

- **ČHMÚ climatological open data** (CC BY 4.0), about 470 automatic stations with
  10-minute data: 2 m temperature and 10 m wind at the full hour, hourly precipitation
  as the sum of the six 10-minute values (it equals ČHMÚ's own hourly total).
- **About 280 manual rain gauges** with one daily total each, stamped 06:00 UTC by ČHMÚ
  (the 24 hours after that time).
- Values ČHMÚ marks as suspect, poor or missing are dropped, as are physically
  implausible ones. Estimated values are kept (a scoring option can exclude them).
- The last few days come from ČHMÚ's unchecked `now/` files; once ČHMÚ publishes the
  checked month, it replaces them and the scores are recomputed.

## Forecasts

- From the **Open-Meteo Previous Runs API** (CC BY 4.0): for each model the value it
  predicted for a given hour 1, 2, … 5 days earlier (`_previous_dayN`, "D+N").
- 11 models: ČHMÚ ALADIN (1 km and 2.3 km), DWD ICON-D2 and ICON-EU, ECMWF IFS HRES,
  IFS 0.25° and AIFS, NOAA GFS, UK Met Office global, Météo-France ARPEGE Europe and
  GeoSphere Austria AROME. Each is used for the lead days its archive fills, measured
  live (the high-resolution models only reach D+1 or D+2).
- Requested at each station's coordinates **and elevation**: Open-Meteo picks the grid
  point and corrects temperature for the height difference.

## Pairing forecasts and observations

- **Temperature and wind:** ranked at 00, 06, 12 and 18 UTC, the hours at which every
  model has its own output. Some models write output only every 3 or 6 hours (all
  hours for AIFS and IFS 0.25°, longer lead times for ICON-EU, IFS HRES, GFS and UKMO)
  and Open-Meteo interpolates the hours in between; scoring an interpolated hour would
  judge the interpolation, not the model, and comparing models over different hours of
  the day would favour some of them. Errors at every native hour are kept too, for
  information.
- **Precipitation:** hourly for hourly models, 3- or 6-hour sums otherwise, and two
  daily totals for every model: the **UTC day** (automatic stations) and ČHMÚ's
  **climatological day from 06 to 06 UTC** (automatic stations and the manual gauges).
- **Extremes:** the daily maximum of the hourly temperature (only models with hourly
  output at that lead day) with **heat days** of at least 30 °C, and **heavy
  precipitation** days of at least 20 mm.
- **Time of day:** the temperature at 00, 06, 12 and 18 UTC on its own, where every
  model has native output.

## Metrics

- **MAE** (mean absolute error) ranks the models. **Bias** (forecast minus observed)
  and **RMSE** are reported too.
- Precipitation and heat events (at least 0.1, 5 and 20 mm a day; at least 30 °C) get
  the **probability of detection**, the **false alarm ratio** and the **equitable
  threat score**.
- Scores are kept as daily sums per station and model, so any region and period is
  summed first and the metric computed once.

## Fair comparison

- Within each time window, variable, lead day and region, only the station-days that
  **every model present in that region** has forecasts for are used, so all models of a
  region are compared on the same stations and days. Models whose archive starts later
  (ALADIN: June 2026) or has gaps get the same days as the rest. The price: the "all
  time" window at D+1 and D+2 only starts when ALADIN's does.
- Where a model never reaches some stations (ICON-D2 at six stations in the Beskydy),
  those stations are left out of their regions' comparison for every model; on their own
  they are still compared among the other models.
- A region is ranked only with at least **3 stations**. An okres with fewer of its own
  borrows the nearest stations of its neighbours (at most 30 km beyond its border) up to
  3, and the map says how many. So every okres has a ranking, but for a third of them it
  partly describes the surrounding area.
- Windows: the last 90 days, the current season, all time, and each season over all
  years (all winters, springs, summers, autumns).

## Ranking and uncertainty

- Models are ordered by MAE. To tell real differences from luck, whole **days** are
  resampled 1,000 times (all stations of a day together, because errors on one day are
  correlated across the country) and the MAE difference to the best model gets a 95 %
  interval.
- A model whose interval includes zero is **tied with the best** ("≈" in the README);
  the best model is a **clear winner** only if nobody is tied.

## Baseline: the mean of all models

The plain average of all models (at least 3 per hour) is scored like a model, but not
ranked. It is compared with the best single model instead: if the average often wins,
picking any single model is worse than averaging them.

## Our own forecast (roadmap 6.2, 6.3)

The forecast page combines, for one okres, the current forecasts of all models from the
Open-Meteo Forecast API at a point inside the okres. Each model is weighted by how well
it did there over the last 90 days (inverse of its error variance), and temperature and
wind are corrected by its mean error there; precipitation is weighted but not
corrected. The weights are shrunk towards a plain mean while there are few scored days
(half-way after 30 days). Hours in the next 24 h use the D+1 weights, later hours those
of their lead day (up to D+5), and models that do not reach an hour are left out with
the other weights rescaled; a model that ends early fades out over its last 3 hours, so
the curve does not jump. The page draws, next to the combination, the model ranked
best in the okres for each day of the forecast (it can be a different model on D+1 and
D+3), and lists the largest weights of every lead day. Precipitation weights come from daily totals but are
applied to hourly values. Details: [data-sources.md](data-sources.md#combination-weights-roadmap-62).

How this compares with operational practice (Bureau of Meteorology OCF, NOAA's
National Blend of Models, MeteoSwiss) and what still has to be tested:
[forecast-research.md](forecast-research.md).

The forecast map (`tv.html`) shows the same combination for every okres, made twice a
day by `mvd outlook`: by part of day, with the probability of precipitation (the
weighted share of models forecasting at least 0.2 mm) and a symbol; cloud cover there is
a plain mean of the models and not verified.

This is a forecast built on the ranking, not yet a verified one: whether it beats the
best single model has to be shown out of sample (roadmap 6.4). Until then the page
says so.

## Limitations

- **Borrowed stations.** Where an okres borrows, nearness is the only criterion; a
  borrowed station may sit higher or lower than the okres itself (a hill-top station
  next to a lowland okres), which matters most for temperature.

- **Point versus grid cell.** A station measures one point; a model forecasts a grid
  cell average (1 km to about 25 km). Thunderstorm rain, valley inversions and wind in
  complex terrain differ within a cell, which penalises coarse models most. That is
  what users of point forecasts experience, but it is not a pure measure of model
  quality.
- **Open-Meteo's processing.** Grid-point choice, elevation correction and
  interpolation are Open-Meteo's, not the models' own; mountain stations are most
  affected. Our own ALADIN archive (nearest grid point, no correction) can later serve
  as a check.
- **Which run is "D+N".** `_previous_dayN` takes, for each hour, the run at least
  N days older. A 24-hour total therefore mixes runs (the hours after midnight come
  from a run one day later), and the native output step is inferred from the lead time
  plus a 6-hour margin, not read from the run.
- **Interpolated hours.** Where a model is 3- or 6-hourly we score only native hours,
  but whether Open-Meteo's hourly precipitation adds up exactly to the model's own
  period totals is **unverified**.
- **Manual gauges.** ČHMÚ stamps each total at 06:00 UTC; the actual reading time of a
  gauge is **unverified**. Manual readings arrive about a month late, so the newest
  scores cover automatic stations only. Like all gauges they catch less than falls in
  wind and snow, so models may look too wet in winter.
- **Hourly values, not extremes.** The observed daily maximum is the highest reading
  at the full hour, slightly below ČHMÚ's own daily maximum; both sides use the same
  convention.
- **Model changes.** Models are upgraded over time, and long windows mix versions.
- **The mean of all models** has different members by lead day (only the global models
  reach D+5) and over time (archive starts).
- **Statistics.** The bootstrap ignores correlation between consecutive days, so
  intervals are slightly too narrow; and with many regions, variables and lead days
  some "clear winners" will be chance. Small regions and short windows are noisy, and
  the 20 mm and 30 °C scores rest on few events.
- **Wind.** We use ČHMÚ's element `F` at the full hour; how ČHMÚ averages it is not
  documented. Sensor heights are not corrected.
