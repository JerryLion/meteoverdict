"""Weights for combining the models into one forecast per okres (roadmap 6.2).

For every okres, variable and lead day, each model gets a weight from how well it did
there over the last 90 days (the okres scores of ``mvd aggregate``, on the same fair
station-days for all models, with borrowed stations where an okres has few):

- **temperature and wind**: the forecast is first corrected by the model's mean error
  (bias) there, so the weight is the inverse of the error variance left after that
  correction, ``1 / (RMSE² - bias²)``;
- **precipitation** (daily totals): no correction (subtracting a mean would give
  negative rain), weight ``1 / RMSE²``.

With few days these numbers are noisy, so both are shrunk towards the plain mean of all
models (weight ``1 / models``, no correction), the correction much less than the weight:
with ``days`` scored days, the weight is ``s * w + (1 - s) / models`` with
``s = days / (days + SHRINK_DAYS)`` and the correction ``c * bias`` with
``c = days / (days + BIAS_SHRINK_DAYS)``. After 30 days half of the weight comes from
the scores, after 90 days three quarters; the correction is 6/7 of the bias after 30
days. A model's mean error is stable enough to be removed almost in full (out of sample
in September 2026, shrinking it like the weights left about half of it in and cost
7-10 % of wind MAE).

The combined forecast is ``sum_m weight_m * (forecast_m - correction_m)`` over the
models available for that hour, with the weights of the missing ones left out and the
rest rescaled (``combine_values``), with at least ``MIN_MODELS`` models; precipitation
and wind are not allowed below 0. Whether this beats the best single model is tested
out of sample by ``meteoverdict.blendtest`` (roadmap 6.4).

Output (``write_forecast``): ``forecast/okresy.json`` with a forecast point per okres
and ``forecast/<okres>.json`` with its weights, both ``{"columns", "rows"}`` like the
score files.
"""

from __future__ import annotations

import json
from itertools import pairwise
from pathlib import Path

import polars as pl

from meteoverdict import blend
from meteoverdict.regions import Region, load_regions

WINDOW = "90d"
#: shrinkage of the weights towards the plain mean, in scored days (half-way after this)
SHRINK_DAYS = 30
#: shrinkage of the bias correction towards none, in scored days
BIAS_SHRINK_DAYS = 5
#: smallest error variance used, so a model that was perfect on a few days does not get
#: all the weight (units of the variable squared)
MIN_ERROR_VARIANCE = 0.01
#: Open-Meteo hourly variable → (score variable the weights come from, bias-corrected)
VARIABLES = {
    "temperature_2m": ("temperature_2m", True),
    "wind_speed_10m": ("wind_speed_10m", True),
    "precipitation": ("precipitation_daily", False),
}
WEIGHT_COLUMNS = ("variable", "lead_day", "model", "weight", "correction", "mae", "rank", "days")
#: a combined value needs at least this many models with a value at that hour
MIN_MODELS = 2
#: combined variables that cannot be negative (clipped at 0 after the bias correction)
NON_NEGATIVE = ("precipitation", "wind_speed_10m")


def weights(table: pl.DataFrame, window: str = WINDOW) -> pl.DataFrame:
    """One row per okres, variable (Open-Meteo name), lead day and model.

    ``table`` holds aggregated scores (``meteoverdict.aggregate``); ``rank`` (from
    ``meteoverdict.ranking``) is passed through where present, null otherwise.
    """
    if "rank" not in table.columns:
        table = table.with_columns(pl.lit(None, pl.Int16).alias("rank"))
    by_score = {score: (name, corrected) for name, (score, corrected) in VARIABLES.items()}
    rows = table.filter(
        pl.col("level") == "okres",
        pl.col("window") == window,
        pl.col("variable").is_in(list(by_score)),
        pl.col("model") != blend.ID,
        pl.col("enough_stations"),
        pl.col("n") > 0,
        pl.col("rmse").is_not_null(),
    )
    corrected = pl.col("variable").replace_strict(
        {s: c for s, (_, c) in by_score.items()}, return_dtype=pl.Boolean
    )
    group = ["region", "variable", "lead_day"]
    variance = (
        pl.when(corrected)
        .then(pl.col("rmse") ** 2 - pl.col("bias") ** 2)
        .otherwise(pl.col("rmse") ** 2)
    )
    shrink = pl.col("days") / (pl.col("days") + SHRINK_DAYS)
    shrink_bias = pl.col("days") / (pl.col("days") + BIAS_SHRINK_DAYS)
    return (
        rows.with_columns(
            (1 / pl.max_horizontal(variance, pl.lit(MIN_ERROR_VARIANCE))).alias("inverse"),
            shrink.alias("shrink"),
        )
        .with_columns(
            (
                pl.col("shrink") * pl.col("inverse") / pl.col("inverse").sum().over(group)
                + (1 - pl.col("shrink")) / pl.len().over(group)
            ).alias("weight"),
            pl.when(corrected)
            .then(shrink_bias * pl.col("bias"))
            .otherwise(0.0)
            .alias("correction"),
            pl.col("variable").replace_strict({s: n for s, (n, _) in by_score.items()}),
        )
        .select("region", "region_name", *WEIGHT_COLUMNS)
        .sort("region", "variable", "lead_day", "weight", descending=[False, False, False, True])
    )


def combine_values(
    frame: pl.LazyFrame | pl.DataFrame, variable: str, by: list[str], weight: str = "weight"
) -> pl.LazyFrame | pl.DataFrame:
    """The combined forecast of ``variable``, one row per group ``by``.

    ``frame`` has one row per group and model with the model's forecast in
    ``variable``, its ``weight`` (column named by ``weight``) and its ``correction``.
    ``sum(weight * (forecast - correction)) / sum(weight)`` over the models with a value,
    so the weights of missing models are left out and the rest rescaled; null with fewer
    than ``MIN_MODELS`` models; not below 0 for ``NON_NEGATIVE`` variables.
    """
    w = pl.col(weight)
    combined = (
        frame.drop_nulls(variable)
        .group_by(by)
        .agg(
            ((w * (pl.col(variable) - pl.col("correction"))).sum() / w.sum()).alias(variable),
            pl.len().alias("_models"),
        )
        .with_columns(
            pl.when(pl.col("_models") >= MIN_MODELS).then(pl.col(variable)).alias(variable)
        )
        .drop("_models")
    )
    if variable in NON_NEGATIVE:
        combined = combined.with_columns(pl.col(variable).clip(lower_bound=0))
    return combined


def representative_point(region: Region) -> tuple[float, float]:
    """A point inside the okres: the centroid of its largest polygon, or, where that
    falls outside (a crescent-shaped okres), the inside grid point nearest to it."""
    ring = max((p[0] for p in region.polygons), key=lambda r: abs(_area(r)))
    area = _area(ring)
    lon = sum((x1 + x2) * (x1 * y2 - x2 * y1) for (x1, y1), (x2, y2) in pairwise(ring))
    lat = sum((y1 + y2) * (x1 * y2 - x2 * y1) for (x1, y1), (x2, y2) in pairwise(ring))
    lon, lat = lon / (6 * area), lat / (6 * area)
    if region.contains(lon, lat):
        return lon, lat
    lon_min, lat_min, lon_max, lat_max = region.bbox
    steps = 60
    inside = [
        (lon_min + (lon_max - lon_min) * i / steps, lat_min + (lat_max - lat_min) * j / steps)
        for i in range(steps + 1)
        for j in range(steps + 1)
    ]
    inside = [(x, y) for x, y in inside if region.contains(x, y)]
    return min(inside, key=lambda p: (p[0] - lon) ** 2 + (p[1] - lat) ** 2)


def _area(ring: list[tuple[float, float]]) -> float:
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in pairwise(ring)) / 2


def _write(path: Path, frame: pl.DataFrame) -> Path:
    rows = frame.select(
        pl.col(c).round(4) if frame.schema[c].is_float() else pl.col(c) for c in frame.columns
    ).rows()
    doc = {"columns": frame.columns, "rows": rows}
    path.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), "utf-8")
    return path


def okres_points() -> pl.DataFrame:
    """``code``, ``name``, ``lat``, ``lon`` of the forecast point of every okres."""
    points = []
    for region in load_regions("okres"):
        lon, lat = representative_point(region)
        points.append((region.code, region.name, round(lat, 4), round(lon, 4)))
    return pl.DataFrame(points, schema=["code", "name", "lat", "lon"], orient="row")


def write_forecast(table: pl.DataFrame, out_dir: Path) -> list[Path]:
    """``out_dir/forecast/okresy.json`` and one ``out_dir/forecast/<okres>.json`` each."""
    folder = out_dir / "forecast"
    folder.mkdir(parents=True, exist_ok=True)
    w = weights(table)
    index = okres_points().with_columns(
        pl.col("code").is_in(w["region"].unique().to_list()).alias("weights")
    )
    written = [_write(folder / "okresy.json", index.sort("code"))]
    for (code,), part in sorted(w.partition_by("region", as_dict=True).items()):
        written.append(_write(folder / f"{code}.json", part.select(WEIGHT_COLUMNS)))
    return written
