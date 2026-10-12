import json
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
import polars as pl
import pytest

from meteoverdict import combine, outlook

FIXTURES = Path(__file__).parent / "fixtures"
CODES = ["CZ0100", "CZ0201"]
# the saved answer was fetched at 08:25 UTC on 12 October 2026
NOW = datetime(2026, 10, 12, 8, 25, tzinfo=UTC)


def weights_of(code):
    doc = json.loads((FIXTURES / "weights" / f"{code}.json").read_text("utf-8"))
    return pl.DataFrame(doc["rows"], schema=doc["columns"], orient="row").with_columns(
        pl.lit(code).alias("region"), pl.col("lead_day").cast(pl.Int8)
    )


WEIGHTS = pl.concat([weights_of(c) for c in CODES])
MODELS = sorted(WEIGHTS["model"].unique().to_list())
PAYLOAD = json.loads((FIXTURES / "open-meteo" / "forecast-2-okresy.json").read_text("utf-8"))
FC = outlook.parse(PAYLOAD, CODES, MODELS)


def test_request_and_cost():
    points = pl.DataFrame({"code": CODES, "lat": [50.0668, 49.717], "lon": [14.466, 14.7767]})
    params = outlook.request_params(points, ["a", "b"])
    assert params["latitude"] == "50.0668,49.717"
    assert params["hourly"] == "temperature_2m,precipitation,wind_speed_10m,cloud_cover"
    assert params["models"] == "a,b" and params["timezone"] == "GMT"
    # 77 okresy, 4 variables x 11 models: 4.4 calls each
    assert outlook.cost(77, 11) == pytest.approx(338.8)


def test_parse_the_saved_answer():
    assert FC["okres"].unique().sort().to_list() == CODES
    assert FC["model"].n_unique() == 11
    d2 = FC.filter(pl.col("okres") == "CZ0201", pl.col("model") == "dwd_icon_d2")
    assert d2["time"].max() < FC["time"].max()  # ICON-D2 ends after about two days
    assert FC.filter(pl.col("temperature_2m").is_null()).is_empty()


def test_combined_hour_matches_the_formula():
    hourly = outlook.combine_hourly(FC, WEIGHTS, NOW)
    when = datetime(2026, 10, 12, 12, tzinfo=UTC)
    got = hourly.filter(pl.col("okres") == "CZ0201", pl.col("time") == when)
    rows = FC.filter(pl.col("okres") == "CZ0201", pl.col("time") == when)
    w = WEIGHTS.filter(
        pl.col("region") == "CZ0201",
        pl.col("variable") == "temperature_2m",
        pl.col("lead_day") == 1,
    )
    joined = rows.join(w, on="model")  # no model ends at 12 UTC today: no fading
    expected = (
        joined["weight"] * (joined["temperature_2m"] - joined["correction"])
    ).sum() / joined["weight"].sum()
    assert got["temperature_2m"].item() == pytest.approx(expected)
    assert got["models"].item() == 11
    assert got["cloud_cover"].item() == pytest.approx(rows["cloud_cover"].mean())
    assert hourly.filter(pl.col("precipitation") < 0).is_empty()


def test_models_fade_out_at_their_end():
    fc = outlook.with_lead_and_fade(FC, NOW).filter(pl.col("okres") == "CZ0201")
    d2 = fc.filter(pl.col("model") == "dwd_icon_d2").sort("time")
    assert d2["fade"].tail(4).to_list() == [1.0, 0.75, 0.5, 0.25]
    assert d2["fade"].head(-4).unique().to_list() == [1.0]
    ifs = fc.filter(pl.col("model") == "ecmwf_ifs")  # reaches the end: never fades
    assert ifs["fade"].unique().to_list() == [1.0]
    assert fc.filter(pl.col("time") == NOW.replace(minute=0))["lead_day"].unique().to_list() == [1]
    assert fc["lead_day"].max() == 5


def test_lead_days_fall_back_to_the_nearest_shorter_one():
    w = pl.DataFrame(
        {
            "region": ["X", "X"],
            "variable": ["temperature_2m"] * 2,
            "lead_day": pl.Series([1, 3], dtype=pl.Int8),
            "model": ["a", "a"],
            "weight": [1.0, 1.0],
            "correction": [0.1, 0.3],
        }
    )
    lead = outlook._lead_weights(w).sort("lead_day")
    assert lead["lead_day"].to_list() == [1, 2, 3, 4, 5]
    assert lead["correction"].to_list() == [0.1, 0.1, 0.3, 0.3, 0.3]


def test_probability_is_the_weighted_share_of_wet_models():
    times = [datetime(2026, 10, 13, h, tzinfo=UTC) for h in range(4, 10)]  # 06-12 Prague
    fc = pl.DataFrame(
        {
            "okres": "X",
            "time": times * 3,
            "model": ["a"] * 6 + ["b"] * 6 + ["c"] * 6,
            "temperature_2m": 10.0,
            "precipitation": [0.1] * 6 + [0.0] * 6 + [0.01] * 6,  # a: 0.6 mm, wet
            "wind_speed_10m": 1.0,
            "cloud_cover": 50.0,
        }
    ).with_columns(pl.col("time").cast(pl.Datetime("us", "UTC")))
    w = pl.DataFrame(
        {
            "region": "X",
            "variable": "precipitation",
            "lead_day": pl.Series([1, 1, 1], dtype=pl.Int8),
            "model": ["a", "b", "c"],
            "weight": [0.5, 0.25, 0.25],
            "correction": 0.0,
        }
    )
    p = outlook.probability(fc, w, datetime(2026, 10, 13, tzinfo=UTC))
    morning = p.filter(pl.col("part") == "morning")
    assert morning["day"].item() == date(2026, 10, 13)
    assert morning["rain_probability"].item() == pytest.approx(0.5)


@pytest.mark.parametrize(
    ("cloud", "rain", "chance", "temp", "expected"),
    [
        (10, 0, 0, 10, "clear"),
        (50, 0, 0, 10, "partly"),
        (90, 0, 0.1, 10, "cloudy"),
        (90, 0.1, 0.4, 10, "showers"),
        (90, 2.0, 0.8, 10, "rain"),
        (90, 2.0, 0.8, 1.5, "sleet"),
        (90, 2.0, 0.8, -3, "snow"),
        (90, 0.05, 0.8, 10, "showers"),  # likely but too little to call it rain
        (None, None, None, None, None),
    ],
)
def test_symbols(cloud, rain, chance, temp, expected):
    assert outlook.symbol(cloud, rain, chance, temp) == expected


def test_parts_and_days_in_prague_time(tmp_path):
    hourly = outlook.combine_hourly(FC, WEIGHTS, NOW)
    table = outlook.summarise(hourly, outlook.probability(FC, WEIGHTS, NOW))
    benesov = table.filter(pl.col("okres") == "CZ0201")
    # the answer starts at 00 UTC = 02:00 in Prague: today's night has 4 hours, still kept
    assert benesov["day"].min() == date(2026, 10, 12)
    assert benesov.filter(pl.col("day") == date(2026, 10, 12))["part"].to_list() == [
        "night",
        "morning",
        "afternoon",
        "evening",
        "day",
    ]
    assert benesov["day"].n_unique() == 6
    day = benesov.filter(pl.col("part") == "day")
    assert (day["tmin"] <= day["tmax"]).all()
    assert day["rain_probability"].is_between(0, 1).all()
    assert (
        day["symbol"].is_in(["clear", "partly", "cloudy", "showers", "rain", "sleet", "snow"]).all()
    )
    points = pl.DataFrame(
        {"code": CODES, "name": ["Praha", "Benešov"], "lat": [50.0, 49.7], "lon": [14.4, 14.7]}
    )
    path = outlook.write(table, points, tmp_path / "outlook.json", NOW)
    doc = json.loads(path.read_text("utf-8"))
    assert doc["parts"] == ["night", "morning", "afternoon", "evening"]
    assert doc["days"][0] == "2026-10-12" and len(doc["days"]) == 6
    assert doc["columns"] == list(outlook.COLUMNS)
    assert doc["okresy"][1]["name"] == "Benešov"
    assert {r[0] for r in doc["rows"]} == set(CODES)


def test_outlook_end_to_end_with_a_mocked_api():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.open-meteo.com"
        assert request.url.params["models"] == ",".join(MODELS)
        return httpx.Response(200, json=PAYLOAD)

    points = combine.okres_points().filter(pl.col("code").is_in(CODES)).sort("code")
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        table, hourly = outlook.outlook(client, WEIGHTS, points, now=NOW)
    assert table["okres"].unique().sort().to_list() == CODES
    assert hourly["okres"].unique().sort().to_list() == CODES


def test_hourly_file(tmp_path):
    hourly = outlook.combine_hourly(FC, WEIGHTS, NOW)
    path = outlook.write_hourly(hourly, tmp_path / "outlook-hourly.json", NOW)
    doc = json.loads(path.read_text("utf-8"))
    assert len(doc["time"]) == 144
    assert doc["time"][0] == "2026-10-12T00:00Z"
    assert set(doc["okresy"]) == set(CODES)
    benesov = doc["okresy"]["CZ0201"]
    assert set(benesov) == set(outlook.HOURLY)
    assert all(len(v) == 144 for v in benesov.values())
    noon = hourly.filter(
        pl.col("okres") == "CZ0201", pl.col("time") == datetime(2026, 10, 12, 12, tzinfo=UTC)
    )
    assert benesov["temperature_2m"][12] == round(noon["temperature_2m"].item(), 1)


def test_too_expensive_requests_are_refused():
    points = pl.DataFrame({"code": ["x"] * 200, "lat": [50.0] * 200, "lon": [14.0] * 200})
    transport = httpx.MockTransport(lambda r: httpx.Response(500))
    with httpx.Client(transport=transport) as client, pytest.raises(ValueError, match="MAX_CALLS"):
        outlook.fetch(client, points, MODELS, lambda _: None)
