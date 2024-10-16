import requests
from enum import Enum
from datetime import datetime
from typing import List
from dataclasses import dataclass


class Unit(Enum):
    MM = "mm"


@dataclass
class RegionalRainfall:
    automatic_weather_station: str
    automatic_weather_station_id: str
    value: int
    unit: Unit


@dataclass
class RainfallHourlyData:
    obs_time: datetime
    hourly_rainfall: List[RegionalRainfall]


def parse_hourly_rainfall(json_data: dict) -> RainfallHourlyData:
    # Parse rainfall data
    rainfall_data = [
        RegionalRainfall(
            unit=Unit(datum["unit"]),
            automatic_weather_station="",
            automatic_weather_station_id="",
            value=datum["value"],
        )
        for datum in json_data["hourlyRainfall"]
    ]

    # Create CurrentWeather instance
    hourly_rainfall = RainfallHourlyData(
        hourly_rainfall=rainfall_data, obs_time=json_data["obsTime"]
    )

    return hourly_rainfall


def get_hourly_rainfall():
    hourly_rainfall_url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/hourlyRainfall.php"
    )
    params = {"lang": "tc"}
    current_json = requests.get(hourly_rainfall_url, params=params).json()

    return parse_hourly_rainfall(current_json)
