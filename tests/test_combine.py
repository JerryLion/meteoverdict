import json
import math

import polars as pl
import pytest

from meteoverdict import combine
from meteoverdict.regions import Region, load_regions


def table(rows):
    """rows: (variable, model, days, rmse, bias) for okres CZ0201, window 90d, D+1."""
    return pl.DataFrame(
        [
            {
                "level": "okres",
                "region": "CZ0201",
                "region_name": "Benešov",
                "window": "90d",
                "variable": v,
                "lead_day": 1,
                "model": m,
                "n": 24 * days,
                "days": days,
                "mae": rmse,
                "rmse": rmse,
                "bias": bias,
                "rank": None if m == "blend" else 1,
                "enough_stations": True,
            }
            for v, m, days, rmse, bias in rows
        ]
    )


def weights_of(frame, variable="temperature_2m"):
    part = frame.filter(pl.col("variable") == variable)
    return {m: (w, c) for m, w, c in part.select("model", "weight", "correction").rows()}


def test_temperature_weights_use_the_error_left_after_the_bias_correction():
    # a: RMSE 2 but bias 1.6 → error variance 4 - 2.56 = 1.44; b: RMSE 1.5, no bias → 2.25
    days = 30  # weights shrink 30 / (30 + 30) = 0.5, the correction 30 / (30 + 5) = 6/7
    w = weights_of(
        combine.weights(
            table(
                [("temperature_2m", "a", days, 2.0, 1.6), ("temperature_2m", "b", days, 1.5, 0.0)]
            )
        )
    )
    inv_a, inv_b = 1 / 1.44, 1 / 2.25
    assert w["a"][0] == pytest.approx(0.5 * inv_a / (inv_a + inv_b) + 0.25)
    assert w["b"][0] == pytest.approx(0.5 * inv_b / (inv_a + inv_b) + 0.25)
    assert w["a"][1] == pytest.approx(1.6 * 6 / 7)  # most of the bias
    assert w["b"][1] == 0
    assert w["a"][0] > w["b"][0]  # once corrected, a is the better model


def test_the_bias_correction_is_shrunk_much_less_than_the_weights():
    w = weights_of(
        combine.weights(
            table([("temperature_2m", "a", 5, 1.0, 2.0), ("temperature_2m", "b", 5, 1.0, 0.0)])
        )
    )
    s = 5 / (5 + combine.SHRINK_DAYS)
    assert w["a"][1] == pytest.approx(1.0)  # half of the bias after BIAS_SHRINK_DAYS days
    assert w["a"][1] / 2.0 > 3 * s  # the weights are still mostly the plain mean


def test_precipitation_is_weighted_by_rmse_and_not_corrected():
    w = weights_of(
        combine.weights(
            table(
                [
                    ("precipitation_daily", "a", 90, 1.0, -0.5),
                    ("precipitation_daily", "b", 90, 2.0, 0.0),
                ]
            )
        ),
        "precipitation",
    )
    s = 90 / 120
    assert w["a"][0] == pytest.approx(s * 0.8 + (1 - s) / 2)  # 1/1 vs 1/4
    assert w["a"][1] == 0


def test_few_days_stay_close_to_the_plain_mean():
    w = weights_of(
        combine.weights(
            table([("temperature_2m", "a", 1, 1.0, 0.0), ("temperature_2m", "b", 1, 3.0, 0.0)])
        )
    )
    assert abs(w["a"][0] - 0.5) < 0.05
    assert math.isclose(w["a"][0] + w["b"][0], 1)


def test_a_perfect_model_does_not_take_all_the_weight():
    w = weights_of(
        combine.weights(
            table([("temperature_2m", "a", 900, 0.5, 0.5), ("temperature_2m", "b", 900, 1.0, 0.0)])
        )
    )
    s = 900 / 930
    # error variance 0 is floored at 0.01: inverse 100 against 1
    assert w["a"][0] == pytest.approx(s * 100 / 101 + (1 - s) / 2)
    assert w["a"][0] < 1


def test_only_okres_90d_ranked_variables_and_real_models():
    rows = table(
        [
            ("temperature_2m", "a", 30, 1.0, 0.0),
            ("temperature_2m", "blend", 30, 0.5, 0.0),
            ("temperature_2m_hourly", "a", 30, 1.0, 0.0),
        ]
    )
    other = rows.head(1).with_columns(pl.lit("all").alias("window"), pl.lit("b").alias("model"))
    few = rows.head(1).with_columns(
        pl.lit(False).alias("enough_stations"), pl.lit("c").alias("model")
    )
    w = combine.weights(pl.concat([rows, other, few]))
    assert w.select("variable", "model", "weight").rows() == [("temperature_2m", "a", 1.0)]


def test_every_okres_gets_a_point_inside_it():
    for region in load_regions("okres"):
        assert region.contains(*combine.representative_point(region)), region.code


def test_a_crescent_gets_a_point_inside_not_its_centroid():
    # a C shape: its centroid lies in the empty middle
    ring = [(0, 0), (3, 0), (3, 1), (1, 1), (1, 2), (3, 2), (3, 3), (0, 3), (0, 0)]
    region = Region("X", "C", ((ring,),), (0, 0, 3, 3))
    lon, lat = combine.representative_point(region)
    assert region.contains(lon, lat)
    assert not region.contains(1.5, 1.5)


def test_forecast_files(tmp_path):
    rows = table([("temperature_2m", "a", 30, 1.0, 0.2), ("temperature_2m", "b", 30, 2.0, 0.0)])
    written = combine.write_forecast(rows, tmp_path)
    assert [p.name for p in written] == ["okresy.json", "CZ0201.json"]
    index = json.loads((tmp_path / "forecast" / "okresy.json").read_text("utf-8"))
    assert index["columns"] == ["code", "name", "lat", "lon", "weights"]
    assert len(index["rows"]) == 77
    benesov = next(r for r in index["rows"] if r[0] == "CZ0201")
    assert benesov[1] == "Benešov" and benesov[4] is True
    assert sum(r[4] for r in index["rows"]) == 1
    doc = json.loads((tmp_path / "forecast" / "CZ0201.json").read_text("utf-8"))
    assert doc["columns"] == list(combine.WEIGHT_COLUMNS)
    assert [r[2] for r in doc["rows"]] == ["a", "b"]  # best weight first
