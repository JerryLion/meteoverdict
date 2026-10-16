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
- 19 models, every one Open-Meteo has for all of Czechia with an archive: ČHMÚ ALADIN
  (1 km and 2.3 km), DWD ICON-D2, ICON-EU and ICON global, ECMWF IFS HRES, IFS 0.25° and
  AIFS, NOAA GFS and AIGFS, UK Met Office global, Météo-France ARPEGE Europe and World,
  GeoSphere Austria AROME, KNMI and DMI HARMONIE-AROME, ECCC GEM Global, JMA GSM and CMA
  GRAPES (the last eight added in October 2026). Each is used for the lead days its
  archive fills, measured live (the high-resolution models only reach D+1 or D+2).
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

## Run-based verification by lead hour

The D+N scores answer "how good is the forecast made about N days earlier", using
Open-Meteo's `_previous_dayN` (for each hour, the run at least 24·N hours older). That
is fair across all models but blurs the first hours of a forecast: D+1 for a
temperature at 12 UTC is a run from 24 to 30 hours earlier, never a run from this
morning. Meteorologists verify run by run instead, and so do we:

- **Every model**, from Open-Meteo's **Single Runs API** (free, non-commercial tier):
  each 00, 06, 12 and 18 UTC run since 2026-06-23 (the first run with ALADIN), up to
  120 hours ahead, at about **100 stations** (at least one in every okres, plus the
  mountain stations; [the rule](data-sources.md#the-station-subset)), at the station's
  elevation like the D+N scores. Collected four times a day; older runs are filled in
  as the call budget allows ([budget](data-sources.md#open-meteo-budget)).
- Each lead hour is compared with the ČHMÚ observation at its valid time (run start +
  lead): H+6 of the 06 UTC run is the forecast for 12 UTC. Temperature and wind are
  instant values; precipitation is the hourly amount (mm in the hour ending at the
  valid time).
- Only a model's **own output hours** count: AIFS every 6 hours, IFS 0.25° every 3, and
  ICON-EU, IFS HRES and UK Met Office every 3 hours late in their runs (hourly
  precipitation only where the output is hourly), for the same reason as at the D+N
  scores: the hours in between are Open-Meteo's interpolation.
- **Fair set:** at each lead hour, only the models that reach it are compared, and only
  on the runs and stations that every one of them has. The set of models therefore
  **shrinks with the lead hour**: ICON-D2 ends at 48 h, AROME at 60 h, ALADIN at 72 h,
  ARPEGE at 102 h, UK Met Office's 06 and 18 UTC runs at 60 h. Pooled over the four run
  hours a model must reach the lead in each of them; per run hour (00 or 12 UTC) the
  longer runs show. Models whose single-run archive starts later (ALADIN) or that miss a
  run limit the common sample for everyone at the leads they reach.
- MAE, bias and RMSE (and hits, misses and false alarms for ≥ 0.1 mm in an hour) by
  lead hour H+1 … H+120, for Czechia (all runs and each run hour). The page draws all
  models, the three best over the hours bold (by their mean rank among the models
  compared at each hour, which is fair to the short models), ALADIN dashed.

**ALADIN from our own archive** is still verified the same way (H+1 … H+72, both
domains on the same runs and stations, ~290 stations, values at the nearest grid point
**without** elevation correction) and published as `leads-aladin.json`, but no longer
drawn: the all-model chart takes ALADIN from Open-Meteo, so all models are processed
alike. The archive remains our check of Open-Meteo's ALADIN and records when ČHMÚ
published each run.

What it is not:

- **H+1 is not what anyone gets.** ČHMÚ publishes an ALADIN run only about 3 to 4.5 hours
  after its start (measured: 00 UTC → ~03:30, 06 UTC → ~10:25, 12 UTC → ~15:15, 18 UTC →
  ~22:25). By then H+1 to H+3 (or H+4) are in the past. With a run every 6 hours, the
  freshest ALADIN forecast a user can actually hold is between about 3 and 10.5 hours
  old, so "the next hour" really means H+4 to H+11 of some run. The chart shades the
  unpublished hours (measured for ALADIN only; the other models have similar delays,
  which we do not measure). A score of what a user could actually see (always the
  newest run published before the time of use) needs the publication time, which our
  ALADIN archive records from 2026-10-13 on; it is not computed yet.
- **Short history.** The ongoing collection starts in October 2026, and older runs fill
  in at about one a day until the backfill has finished and its budget moves here. For
  weeks the numbers rest on few runs and few weather regimes; long leads rest on fewer
  runs than short ones (a run's H+120 is verified five days later), and pooled run
  hours mix the time of day into the lead hour (H+6 is 06, 12, 18 or 00 UTC).
- **100 stations**, not all ~500: enough for Czechia as a whole, too few for kraje.
- The newest days use ČHMÚ's unchecked `now/` observations, like the D+N scores.

## Event skill for farmers

Farmers decide on yes/no questions: cover the crops tonight, postpone spraying, secure
the polytunnel. So the same single runs are also verified as **events** (`mvd farm`,
`farm.json`, the section "For farmers" on the comparison page):

- **Frost**, per station and **night** (18:00 to 09:00 Prague time, 16 hourly values; 15
  or 17 when the clocks change): the night's lowest hourly 2 m temperature ≤ 0 °C and
  ≤ −2 °C. The model's minimum is taken over its own output hours in the night (3- and
  6-hourly models see fewer hours, as their users do). A night belongs to the lead bin of
  its end (09:00): the 12 UTC run's coming night ends at H+19, so H+13–24 is "tonight,
  from today's midday run". This is air frost at 2 m; ground frost is often colder.
- **Gusts**, per station and **3-hour block** (00–03, 03–06, … UTC): the strongest gust
  ≥ 10, 15 and 20 m/s. Observed: ČHMÚ's `Fmax` (maximum gust in each 10 minutes), the
  largest of the 18 values; forecast: Open-Meteo's hourly gust (maximum of the preceding
  hour) at the model's own output hours in the block. Blocks rather than single hours,
  so a gust ten minutes early does not count as both a miss and a false alarm.
- **3-hour rain**, the same blocks: ≥ 0.5, 2 and 5 mm.
- **Lead bins** H+1–6, 7–12, 13–24, 25–48, 49–72 and 73–120 (by the end of the night or
  block). **Fair set** as above: in each bin only the models whose runs cover the whole
  bin (and, for blocks, have at most 3-hourly output there) are compared, on the nights
  and blocks that all of them have. AIFS has no gusts; 6-hourly output is not scored in
  3-hour blocks.
- Hits, misses, false alarms and correct negatives give the **POD** ("caught 8 of 10
  frosts"), the **FAR** ("3 of 10 warnings were false"), the CSI, the **ETS** (the CSI
  corrected for chance hits; the page colours it) and the frequency bias (warnings per
  event). With fewer than **20 observed events** in a bin the page warns that the numbers
  are mostly chance, which for −2 °C, 15 and 20 m/s and 5 mm will be the case for months.

Limits: one season of runs at most, about 100 stations, observed gusts only from
15 October 2026 (when `Fmax` was added) and forecast gusts only in runs fetched since
then; events cluster in a few weather situations, so neighbouring stations and blocks
are not independent.

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
- **Models added later** (eight in October 2026) are fetched for the newest days first.
  Until their history is filled in, the windows that reach further back (all time,
  seasons) are limited to the days they have, like ALADIN's late start, and gaps of
  one model (AIGFS before July 2026, CMA GRAPES in autumn 2025, UKMO) drop those days
  for every model of the region. The single-run comparison likewise uses only runs that
  every model reaching a lead hour has.
- A region is ranked only with at least **3 stations**. An okres with fewer of its own
  borrows the nearest stations of its neighbours (at most 30 km beyond its border) up to
  3, and the map says how many. So every okres has a ranking, but for a third of them it
  partly describes the surrounding area.
- Windows: the last 90 days, the current season, all time, and each season over all
  years (all winters, springs, summers, autumns). "All time" starts with the oldest day
  scored so far and grows as the backfill fills in history back to January 2024 (ALADIN
  only from June 2026); until then it can cover the same days as the last 90 days. The
  web pages show every window's real dates and number of days, and mark windows that
  are still the same as the 90-day one.

## Ranking and uncertainty

- Models are ordered by MAE. To tell real differences from luck, whole **days** are
  resampled 1,000 times (all stations of a day together, because errors on one day are
  correlated across the country) and the MAE difference to the best model gets a 95 %
  interval.
- A model whose interval includes zero is **tied with the best** ("≈" on the comparison page);
  the best model is a **clear winner** only if nobody is tied.

## Baseline: the mean of all models

The plain average of all models (at least 3 per hour) is scored like a model, but not
ranked. It is compared with the best single model instead: if the average often wins,
picking any single model is worse than averaging them.

## Our own forecast (roadmap 6.2, 6.3, 6.4)

The forecast page combines, for one okres, the current forecasts of all models from the
Open-Meteo Forecast API at a point inside the okres. Each model is weighted by how well
it did there over the last 90 days (inverse of its error variance), and temperature and
wind are corrected by its mean error there; precipitation is weighted but not
corrected. The weights are shrunk towards a plain mean while there are few scored days
(half-way after 30 days), the bias correction much less (half-way after 5 days: a
model's mean error is stable, and leaving half of it in cost 7–10 % of wind MAE). Hours in the next 24 h use the D+1 weights, later hours those
of their lead day (up to D+5), and models that do not reach an hour are left out with
the other weights rescaled; a model that ends early fades out over its last 3 hours, so
the curve does not jump. The page draws, next to the combination, the model ranked
best in the okres for each day of the forecast (it can be a different model on D+1 and
D+3), and lists the largest weights of every lead day. Precipitation weights come from daily totals but are
applied to hourly values. Details: [data-sources.md](data-sources.md#combination-weights-roadmap-62).

### Temperature and wind: regression blend

For temperature and wind the inverse-error weights and the all-hours bias are replaced
by a small model output statistics step (`meteoverdict.mos`), refitted every day on
the forecast–observation pairs of the last 90 days at 00, 06, 12 and 18 UTC (the hours
every model has natively), per variable and lead day:

1. **Rows**: station × slot × day, only the models with a value in at least 80 % of
   the rows, and only rows where all of those have one. An okres uses the stations of
   its pool (its own, plus borrowed ones where it has fewer than three). *D* = days
   with rows.
2. **Hour-of-day bias** per okres, slot and model, shrunk towards the okres's
   all-hours bias: `B = (D·b_slot + 10·b_all) / (D + 10)`.
3. **Elevation term**: `dz` = (station elevation − mean elevation of the okres's
   stations) / 100 m; the error left after step 2 is regressed on `dz` through the
   origin, nationally per slot and model (β). The models are too slow at stations
   above their okres's average and too fast below it (wind about −0.35 m/s per
   100 m at night, −0.16 at noon); higher stations are warmer at night than the
   models say (inversions) and slightly cooler around midday. The correction is
   `C = B + β·dz`.
4. **Weights**: ridge regression of the observations on the corrected forecasts
   `f − C`, constrained to sum to 1: first for Czechia (towards equal weights,
   penalty 0.1 per row), then per okres towards the Czech weights (penalty 1 per row).
   Weights can be negative (a model that errs like a better one is subtracted).
5. **Forecast**: `Σ w · (f − D/(D+5)·C)`, wind not below 0. At the okres's forecast
   point `dz` is the point's elevation (Open-Meteo's, committed in
   `okres-elevations.csv`) minus the station mean, limited to the range of the
   okres's stations; between the four slots the correction is interpolated linearly.

Fallbacks: an hour where one of the regression's models has no value (or fades out)
uses the inverse-error weights with the corrections of steps 2–3, rescaled over the
models present; with fewer than 14 days of pairs (or no pairs in an okres) everything
is as before. The weights without a sum-to-one constraint did better for wind at
stations (−13.8 % instead of −10.9 %) but pull the forecast towards 0 without an
intercept, so they are not used.

Out of sample (rolling origin, training only on days up to *d − N*, 11–30 September
2026, against the previous method on the same rows) this cut the MAE by 6.9 % for
temperature (D+1 −13.5 % … D+5 −3.7 %) and 10.8 % for wind (−9 … −12 % at every lead
day), in line with the research run it was chosen from (−7.0 %, −10.9 %; 95 %
block-bootstrap intervals −9.9…−3.3 and −11.9…−9.8; the last week, held out when
choosing it, gained as much). The gains are largest where the old all-hours bias did
worst: by night for wind, by day for temperature. Tried and not used: a bias per
station (larger gains at stations, but the forecast is for one point per okres), the
previous run as extra members, exponentially decaying training weights, a
multiplicative wind correction, only the best 3 or 5 models, and an elevation slope
per okres (it mostly learns the okres's few stations). Caveats: the data cover late
summer and autumn only, so the slopes are refitted daily rather than fixed (the winter
inversions will change them); where an okres's stations span very different heights
(Chomutov with Klínovec, Trutnov with Sněžka) the linear elevation term is a rough
guess for the lowland stations, and a few such okresy got worse in the test below.

How this compares with operational practice (Bureau of Meteorology OCF, NOAA's
National Blend of Models, MeteoSwiss) and what still has to be tested:
[forecast-research.md](forecast-research.md).

The forecast map (`tv.html`) shows the same combination for every okres, made twice a
day by `mvd outlook`: by part of day, with the probability of precipitation (the
share of models forecasting at least 0.2 mm, each counting the same) and a symbol; cloud cover there is
a plain mean of the models and not verified.

### Does it beat the best single model? (roadmap 6.4)

`mvd blend-test` (run daily, shown at the top of the comparison page) replays the
combination on past days **out of sample**:

- For day *d* at lead day *N*, the weights, bias corrections and the okres's best
  model come only from the okres scores of the 90 days ending on *d − N*: what the
  daily run had published when that D+N forecast was made. Same code and shrinkage
  as the live forecast; the temperature and wind regression is fitted on the station
  pairs of the same window, and its corrections are taken at each station's own
  elevation.
- The combination is applied to the models' stored D+N forecasts at the okres's
  stations (borrowed ones included) and scored like the mean of all models:
  temperature and wind at 00, 06, 12 and 18 UTC, precipitation as UTC-day totals, on
  the station-days every model has.
- It is compared with **the best model at the time** (the okres's rank-1 model in that
  training window, chosen anew every day: what a user following our ranking would have
  used), the **best model in hindsight** (each okres's model with the lowest MAE over
  the whole test: an upper bound nobody could pick in advance), the mean of all models
  and every single model. Czechia sums the 77 okresy.
- 95 % intervals of the MAE difference to the best model at the time come from the
  same day bootstrap as the ranking. **Warm-up:** an okres is tested only after 14
  scored training days.

**Result so far** (24 test days, 7–30 September 2026, after 14 warm-up days; Czechia;
negative = our forecast has the smaller MAE; 95 % interval in brackets):

| | D+1 | D+2 | D+3 | D+4 | D+5 |
|---|---|---|---|---|---|
| Temperature (°C) | **−0.18** (−0.21…−0.14) | **−0.16** (−0.19…−0.12) | **−0.19** (−0.22…−0.15) | **−0.13** (−0.18…−0.08) | **−0.20** (−0.26…−0.14) |
| Wind (m/s) | **−0.17** (−0.19…−0.15) | **−0.17** (−0.20…−0.15) | **−0.20** (−0.23…−0.17) | **−0.21** (−0.25…−0.17) | **−0.35** (−0.39…−0.31) |
| Precipitation (mm/day) | **−0.25** (−0.49…−0.08) | **−0.20** (−0.41…−0.07) | **−0.28** (−0.54…−0.08) | **−0.18** (−0.31…−0.06) | **−0.26** (−0.60…−0.02) |

MAE of the combination with the regression blend against the method before it (same
test): temperature 1.221 → 1.066 °C at D+1 (−12.7 %), −8.5 %, −6.5 %, −4.4 % and
−3.9 % at D+2…D+5; wind 0.949 → 0.822 m/s at D+1 (−13.4 %), −12.3 %, −12.5 %,
−11.5 % and −13.0 %. Of the 385 okres × lead day groups 31 got worse for temperature
(4 by more than 5 %) and 58 for wind (26 by more than 5 %, mostly Chomutov, Liberec
and Nový Jičín, whose stations span very different heights; see above).

Our forecast is now clearly better than the model a user of the ranking would have
picked for every variable and lead day (before the regression blend it was worse for
wind at D+1, by 0.03 m/s against DWD's ICON models, and not significantly different at
several other lead days). For precipitation it is about as good as the plain mean of all
models, and both beat the per-okres "best" model, partly because that choice jumps
between models on a short, noisy history (probably). The best model in hindsight is still better
for precipitation: a fixed, well-chosen model can do better, but nobody knows it in
advance. For temperature and wind the test scores the combination at the stations, with
each station's own elevation in the correction; the published forecast gets the
elevation term only for its one point per okres, so part of the gain (the elevation
term) shows up there only as far as the point differs from the okres's stations. **This rests on 24 autumn days and is not yet a verdict**:
intervals ignore that consecutive days are alike (so they are too narrow), and the
weights themselves had at most 37 days of scores behind them. The test is repeated
every day as history grows. Not yet done: training windows of 30 and 45 days and a
decaying average (roadmap 6.4); with under 45 days of history they would be almost
the same as 90 days.

## Limitations

- **Which stations.** All stations are ČHMÚ's official network (40 main WMO stations,
  about 220 automatic climate, 40 mountain snow and 180 automatic precipitation
  stations, 280 manual rain gauges; no amateur stations). Ranking with only the
  automatic climate stations gives practically the same results (39 of 40 national
  rankings agree within the intervals); with only the 40 main stations, night
  temperatures are about 0.1-0.3 °C easier and the winners for night temperature and
  wind change, because the main network is better exposed and includes summits where
  every model forecasts far too little wind. Stations whose
  errors stand out (summits, frost hollows) are explained by their siting and stay in.
  Manual gauges in a month ČHMÚ has not completed can report a total after missing
  days (probably several days' rain), which makes the models look too dry there.
  Details: [station-check.md](station-check.md) (August-September 2026, 52 days).

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
- **Lead hours.** The run-based scores rest on a short history at 100 stations, ignore
  the hours until a run is published (3–4.5 h for ALADIN), and compare fewer models at
  longer leads (see above).
- **Model changes.** Models are upgraded over time, and long windows mix versions.
- **The mean of all models** has different members by lead day (only the global models
  reach D+5) and over time (archive starts).
- **Statistics.** The bootstrap ignores correlation between consecutive days, so
  intervals are slightly too narrow; and with many regions, variables and lead days
  some "clear winners" will be chance. Small regions and short windows are noisy, and
  the 20 mm and 30 °C scores rest on few events.
- **Wind.** We use ČHMÚ's element `F` at the full hour; how ČHMÚ averages it is not
  documented. Sensor heights are not corrected.
