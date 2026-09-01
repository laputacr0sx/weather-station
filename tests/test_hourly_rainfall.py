"""Parser tests for HKO past-hour station rainfall."""
from datetime import datetime

from weather_display.lib.util.hourly_rainfall import parse_hourly_rainfall


def _payload(value, station_id="RF020", name="沙田"):
    return {
        "obsTime": "2026-09-01T10:45:00+08:00",
        "hourlyRainfall": [
            {
                "automaticWeatherStation": "西貢",
                "automaticWeatherStationID": "N15",
                "value": "9",
                "unit": "mm",
            },
            {
                "automaticWeatherStation": name,
                "automaticWeatherStationID": station_id,
                "value": value,
                "unit": "mm",
            },
        ],
    }


def test_parse_sha_tin_integer_mm():
    rain = parse_hourly_rainfall(_payload("2"))
    assert rain.station == "沙田"
    assert rain.station_id == "RF020"
    assert rain.mm == 2.0
    assert rain.is_wet
    assert rain.obs_time == datetime(2026, 9, 1, 10, 45)


def test_parse_zero_is_dry_not_missing():
    rain = parse_hourly_rainfall(_payload("0"))
    assert rain.mm == 0.0
    assert rain.available
    assert not rain.is_wet


def test_parse_na_is_unavailable():
    rain = parse_hourly_rainfall(_payload("N/A"))
    assert rain.mm is None
    assert not rain.available
    assert not rain.is_wet


def test_missing_station_is_unavailable():
    payload = {
        "obsTime": "2026-09-01T10:45:00+08:00",
        "hourlyRainfall": [
            {
                "automaticWeatherStation": "西貢",
                "automaticWeatherStationID": "N15",
                "value": "1",
                "unit": "mm",
            }
        ],
    }
    rain = parse_hourly_rainfall(payload)
    assert rain.mm is None
    assert rain.station_id == "RF020"
