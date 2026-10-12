"""TV-style forecast for every okres (roadmap 6.6).

Twice a day, ask the Open-Meteo Forecast API for the next ``DAYS`` days of all models at
the forecast point of every okres (one request, 77 locations), combine them with the
okres weights of ``meteoverdict.combine`` (the same rules as the forecast page: bias
correction, weights per lead day, the next 24 h with D+1, models fading out over their
last ``TAPER_HOURS`` hours) and summarise each day by part of day in Prague time:
night 0-6, morning 6-12, afternoon 12-18, evening 18-24.

Per part of day and per whole day: minimum and maximum of the combined temperature,
combined precipitation total, **probability of precipitation** (the weighted share of
models whose own total for that period is at least ``WET_MM``; averaging rain smooths it,
see docs/forecast-research.md), the highest combined hourly wind, mean cloud cover and a
weather symbol. Cloud cover is the plain mean of the models: we do not verify it.

Cost: 77 locations x 4 variables x 11 models / 10 = about 340 weighted calls a run.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import httpx
import polars as pl

from meteoverdict.forecasts import call_weight

URL = "https://api.open-meteo.com/v1/forecast"
VARIABLES = ("temperature_2m", "precipitation", "wind_speed_10m", "cloud_cover")
COMBINED = ("temperature_2m", "precipitation", "wind_speed_10m")
NON_NEGATIVE = ("precipitation", "wind_speed_10m")
DAYS = 6
MAX_LEAD_DAY = 5
TAPER_HOURS = 3
MIN_MODELS = 2
TIME_ZONE = "Europe/Prague"
#: part of day → first and last local hour + 1
PARTS = {"night": (0, 6), "morning": (6, 12), "afternoon": (12, 18), "evening": (18, 24)}
#: a part of day (6 h) or day (24 h) needs at least this many hours of combined
#: temperature; the forecast starts at 00 UTC, 02:00 in Prague in summer time, so today's
#: night and the day as a whole are a few hours short
MIN_PART_HOURS = 4
MIN_DAY_HOURS = 18
#: a model "forecasts precipitation" for a period with at least this total (mm)
WET_MM = 0.2
#: symbols: precipitation when likely, otherwise by cloud cover
RAIN_PROBABILITY = 0.5
SHOWER_PROBABILITY = 0.3
CLEAR_BELOW = 25.0
PARTLY_BELOW = 70.0
SNOW_AT_OR_BELOW = 0.5
SLEET_AT_OR_BELOW = 2.0
MAX_CALLS = 500


def request_params(points: pl.DataFrame, models: list[str]) -> dict:
    return {
        "latitude": ",".join(str(v) for v in points["lat"]),
        "longitude": ",".join(str(v) for v in points["lon"]),
        "hourly": ",".join(VARIABLES),
        "wind_speed_unit": "ms",
        "timezone": "GMT",
        "forecast_days": DAYS,
        "models": ",".join(models),
    }


def cost(points: int, models: int) -> float:
    return call_weight(points, len(VARIABLES) * models, DAYS)


def fetch(
    client: httpx.Client,
    points: pl.DataFrame,
    models: list[str],
    sleep: Callable[[float], None],
) -> list | dict:
    """One request for all points; waits and retries on the per-minute limit."""
    weight = cost(points.height, len(models))
    if weight > MAX_CALLS:
        raise ValueError(f"{weight:.0f} weighted calls is more than MAX_CALLS = {MAX_CALLS}")
    for wait in (30, 60, 120, None):
        response = client.get(URL, params=request_params(points, models))
        if response.status_code != 429 or wait is None or "daily" in response.text.lower():
            break
        sleep(wait)
    if response.status_code >= 400:
        reason = response.json().get("reason", response.text)
        raise RuntimeError(f"Open-Meteo forecast: HTTP {response.status_code}: {reason}")
    return response.json()


def parse(payload: list | dict, codes: list[str], models: list[str]) -> pl.DataFrame:
    """The API answer → one row per okres, hour and model with the four variables."""
    results = payload if isinstance(payload, list) else [payload]
    if len(results) != len(codes):
        raise ValueError(f"asked for {len(codes)} locations, got {len(results)}")
    frames = []
    for position, result in enumerate(results):
        hourly = result["hourly"]
        times = pl.Series(hourly["time"]).str.to_datetime("%Y-%m-%dT%H:%M", time_zone="UTC")
        for model in models:
            columns = {v: hourly.get(f"{v}_{model}") for v in VARIABLES}
            if all(c is None for c in columns.values()):
                continue
            frames.append(
                pl.DataFrame(
                    {
                        "okres": codes[result.get("location_id", position)],
                        "time": times,
                        "model": model,
                        **{v: columns[v] for v in VARIABLES},
                    },
                    schema={
                        "okres": pl.String,
                        "time": pl.Datetime("us", "UTC"),
                        "model": pl.String,
                        **{v: pl.Float64 for v in VARIABLES},
                    },
                    strict=False,
                )
            )
    out = pl.concat(frames)
    return out.filter(~pl.all_horizontal(pl.col(v).is_null() for v in VARIABLES))


def _lead_weights(weights: pl.DataFrame) -> pl.DataFrame:
    """Weights for every lead day 1..MAX_LEAD_DAY, taking the nearest shorter lead day
    that has weights where one is missing (as the forecast page does)."""
    have = weights.select("region", "variable", "lead_day").unique()
    wanted = (
        have.select("region", "variable")
        .unique()
        .join(
            pl.DataFrame({"lead": list(range(1, MAX_LEAD_DAY + 1))}, schema={"lead": pl.Int8}),
            how="cross",
        )
    )
    source = (
        wanted.join(have, on=["region", "variable"])
        .filter(pl.col("lead_day") <= pl.col("lead"))
        .group_by("region", "variable", "lead")
        .agg(pl.col("lead_day").max())
    )
    return (
        source.join(weights, on=["region", "variable", "lead_day"])
        .drop("lead_day")
        .rename({"lead": "lead_day", "region": "okres"})
    )


def combine_hourly(fc: pl.DataFrame, weights: pl.DataFrame, now: datetime) -> pl.DataFrame:
    """One row per okres and hour: the combined temperature, precipitation and wind,
    the plain mean of cloud cover, and the number of models."""
    hours = (pl.col("time") - pl.lit(now)).dt.total_hours()
    last = (
        pl.col("time").filter(pl.col("temperature_2m").is_not_null()).max().over("okres", "model")
    )
    fc = fc.with_columns(
        pl.min_horizontal(pl.lit(MAX_LEAD_DAY), pl.max_horizontal(pl.lit(1), hours // 24))
        .cast(pl.Int8)
        .alias("lead_day"),
        # 1, then ¾, ½, ¼ in a model's last hours, unless it reaches the end of all
        pl.when(last == pl.col("time").max().over("okres"))
        .then(1.0)
        .otherwise(
            pl.min_horizontal(
                pl.lit(1.0),
                ((last - pl.col("time")).dt.total_hours() + 1) / (TAPER_HOURS + 1),
            )
        )
        .alias("fade"),
    )
    lead = _lead_weights(weights)
    out = fc.group_by("okres", "time").agg(
        pl.col("cloud_cover").mean(), pl.col("model").n_unique().alias("models")
    )
    for variable in COMBINED:
        w = lead.filter(pl.col("variable") == variable).select(
            "okres", "lead_day", "model", "weight", "correction"
        )
        part = (
            fc.select("okres", "time", "model", "lead_day", "fade", variable)
            .drop_nulls(variable)
            .join(w, on=["okres", "lead_day", "model"])
            .with_columns((pl.col("weight") * pl.col("fade")).alias("w"))
            .group_by("okres", "time")
            .agg(
                (
                    (pl.col("w") * (pl.col(variable) - pl.col("correction"))).sum()
                    / pl.col("w").sum()
                ).alias(variable),
                pl.len().alias("n"),
            )
            .with_columns(pl.when(pl.col("n") >= MIN_MODELS).then(pl.col(variable)).alias(variable))
            .drop("n")
        )
        if variable in NON_NEGATIVE:
            part = part.with_columns(pl.col(variable).clip(lower_bound=0))
        out = out.join(part, on=["okres", "time"], how="left")
    return out.sort("okres", "time")


def _local(frame: pl.DataFrame) -> pl.DataFrame:
    local = pl.col("time").dt.convert_time_zone(TIME_ZONE)
    part = pl.lit(None, pl.String)
    for name, (first, end) in PARTS.items():
        part = (
            pl.when(local.dt.hour().is_between(first, end - 1)).then(pl.lit(name)).otherwise(part)
        )
    return frame.with_columns(local.dt.date().alias("day"), part.alias("part"))


def probability(fc: pl.DataFrame, weights: pl.DataFrame, now: datetime) -> pl.DataFrame:
    """Per okres, day and part (and ``part`` = "day" for whole days): the weighted share
    of models whose own precipitation total is at least ``WET_MM``. Only models that
    cover as many hours of the period as the longest one count."""
    hours = (pl.col("time") - pl.lit(now)).dt.total_hours()
    lead = _lead_weights(weights).filter(pl.col("variable") == "precipitation")
    rows = _local(
        fc.drop_nulls("precipitation").with_columns(
            pl.min_horizontal(pl.lit(MAX_LEAD_DAY), pl.max_horizontal(pl.lit(1), hours // 24))
            .cast(pl.Int8)
            .alias("lead_day")
        )
    )
    frames = []
    for period in ("part", "day"):
        keys = ["okres", "day"] if period == "day" else ["okres", "day", "part"]
        totals = (
            rows.group_by(*keys, "model")
            .agg(
                pl.col("precipitation").sum(),
                pl.len().alias("hours"),
                pl.col("lead_day").min(),
            )
            # a model ending inside the period would undercount its rain
            .filter(pl.col("hours") == pl.col("hours").max().over(keys))
            .join(lead, on=["okres", "lead_day", "model"])
            .group_by(keys)
            .agg(
                (
                    (pl.col("weight") * (pl.col("precipitation") >= WET_MM)).sum()
                    / pl.col("weight").sum()
                ).alias("rain_probability")
            )
        )
        if period == "day":
            totals = totals.with_columns(pl.lit("day").alias("part"))
        frames.append(totals.select("okres", "day", "part", "rain_probability"))
    return pl.concat(frames)


def symbol(
    cloud: float | None,
    precipitation: float | None,
    chance: float | None,
    temperature: float | None,
) -> str | None:
    """Weather symbol: precipitation when likely, else sky by cloud cover."""
    if cloud is None and chance is None:
        return None
    wet = (chance or 0) >= RAIN_PROBABILITY and (precipitation or 0) >= WET_MM
    if wet:
        if temperature is not None and temperature <= SNOW_AT_OR_BELOW:
            return "snow"
        if temperature is not None and temperature <= SLEET_AT_OR_BELOW:
            return "sleet"
        return "rain"
    if (chance or 0) >= SHOWER_PROBABILITY:
        return "showers"
    if cloud is None:
        return None
    if cloud < CLEAR_BELOW:
        return "clear"
    return "partly" if cloud < PARTLY_BELOW else "cloudy"


def summarise(hourly: pl.DataFrame, chances: pl.DataFrame) -> pl.DataFrame:
    """Rows per okres, day and part of day, plus ``part`` = "day" for whole days (its
    symbol from the daytime hours 6-18). Periods with fewer than ``MIN_PART_HOURS`` or
    ``MIN_DAY_HOURS`` hours of combined temperature (the ends of the forecast) are left
    out."""
    rows = _local(hourly)
    stats = [
        pl.col("temperature_2m").min().alias("tmin"),
        pl.col("temperature_2m").max().alias("tmax"),
        pl.col("temperature_2m").mean().alias("tmean"),
        pl.col("precipitation").sum().alias("precipitation"),
        pl.col("wind_speed_10m").max().alias("wind"),
        pl.col("temperature_2m").count().alias("hours"),
    ]
    parts = (
        rows.group_by("okres", "day", "part")
        .agg(*stats, pl.col("cloud_cover").mean().alias("cloud"))
        .filter(pl.col("hours") >= MIN_PART_HOURS)
    )
    daytime = pl.col("part").is_in(["morning", "afternoon"])
    days = (
        rows.group_by("okres", "day")
        .agg(
            *stats,
            pl.col("cloud_cover").filter(daytime).mean().alias("cloud"),
        )
        .filter(pl.col("hours") >= MIN_DAY_HOURS)
        .with_columns(pl.lit("day").alias("part"))
    )
    table = pl.concat([parts, days], how="diagonal_relaxed")
    table = table.join(chances, on=["okres", "day", "part"], how="left")
    symbols = [
        symbol(c, p, r, t)
        for c, p, r, t in table.select(
            "cloud", "precipitation", "rain_probability", "tmean"
        ).iter_rows()
    ]
    order = {name: i for i, name in enumerate([*PARTS, "day"])}
    return (
        table.with_columns(pl.Series("symbol", symbols, pl.String))
        .drop("hours", "tmean")
        .with_columns(pl.col("part").replace_strict(order, return_dtype=pl.Int8).alias("order"))
        .sort("okres", "day", "order")
        .drop("order")
    )


COLUMNS = (
    "okres",
    "day",
    "part",
    "tmin",
    "tmax",
    "precipitation",
    "rain_probability",
    "wind",
    "cloud",
    "symbol",
)


def write(table: pl.DataFrame, points: pl.DataFrame, path: Path, generated: datetime) -> Path:
    """``outlook.json``: ``{"generated", "time_zone", "parts", "days", "okresy",
    "columns", "rows"}``, numbers rounded to one decimal (probability to two)."""
    rounded = table.select(
        pl.col("okres"),
        pl.col("day").cast(pl.String),
        pl.col("part"),
        *[pl.col(c).round(1) for c in ("tmin", "tmax", "precipitation", "wind")],
        pl.col("rain_probability").round(2),
        pl.col("cloud").round(0).cast(pl.Int16, strict=False),
        pl.col("symbol"),
    ).select(COLUMNS)
    doc = {
        "generated": generated.isoformat(timespec="minutes"),
        "time_zone": TIME_ZONE,
        "parts": list(PARTS),
        "days": sorted(rounded["day"].unique().to_list()),
        "okresy": points.select("code", "name", "lat", "lon").rows(named=True),
        "columns": list(COLUMNS),
        "rows": rounded.rows(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), "utf-8")
    return path


def outlook(
    client: httpx.Client,
    weights: pl.DataFrame,
    points: pl.DataFrame,
    now: datetime | None = None,
    sleep: Callable[[float], None] = lambda _: None,
) -> pl.DataFrame:
    """Fetch, combine and summarise for all ``points`` (code, name, lat, lon) that have
    weights."""
    now = now or datetime.now(UTC)
    points = points.filter(pl.col("code").is_in(weights["region"].unique().to_list()))
    models = sorted(weights["model"].unique().to_list())
    payload = fetch(client, points, models, sleep)
    fc = parse(payload, points["code"].to_list(), models)
    return summarise(combine_hourly(fc, weights, now), probability(fc, weights, now))
