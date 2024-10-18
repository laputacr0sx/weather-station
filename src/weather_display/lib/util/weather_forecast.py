from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

import requests
from weather_display import HKO_URL


class Unit(Enum):
    C = "C"
    METRE = "metre"
    PERCENT = "percent"


@dataclass
class Depth:
    unit: Unit
    value: float


@dataclass
class Temp:
    place: str
    value: float
    unit: Unit
    record_time: datetime
    depth: Optional[Depth] = None


@dataclass
class WeatherForecast:
    forecast_date: int
    week: str
    forecast_wind: str
    forecast_weather: str
    forecast_maxtemp: Depth
    forecast_mintemp: Depth
    forecast_maxrh: Depth
    forecast_minrh: Depth
    forecast_icon: int
    psr: str


@dataclass
class WeatherForecastData:
    general_situation: str
    weather_forecast: List[WeatherForecast]
    update_time: datetime
    sea_temp: Temp
    soil_temp: List[Temp]


# Example function to parse JSON into the WeatherForecastData dataclass
def parse_weather_forecast(json_data: dict) -> WeatherForecastData:
    # Parse weather forecast data
    weather_forecast = [
        WeatherForecast(
            forecast_date=int(item["forecastDate"]),
            week=item["week"],
            forecast_wind=item["forecastWind"],
            forecast_weather=item["forecastWeather"],
            forecast_maxtemp=Depth(Unit.C, item["forecastMaxtemp"]["value"]),
            forecast_mintemp=Depth(Unit.C, item["forecastMintemp"]["value"]),
            forecast_maxrh=Depth(Unit.PERCENT, item["forecastMaxrh"]["value"]),
            forecast_minrh=Depth(Unit.PERCENT, item["forecastMinrh"]["value"]),
            forecast_icon=item["ForecastIcon"],
            psr=item["PSR"],
        )
        for item in json_data["weatherForecast"]
    ]

    # Parse sea temperature
    sea_temp = Temp(
        place=json_data["seaTemp"]["place"],
        value=json_data["seaTemp"]["value"],
        unit=Unit.C,
        record_time=datetime.fromisoformat(json_data["seaTemp"]["recordTime"]),
    )

    # Parse soil temperature
    soil_temp = [
        Temp(
            place=item["place"],
            value=item["value"],
            unit=Unit.C,
            record_time=datetime.fromisoformat(item["recordTime"]),
            depth=Depth(Unit.METRE, item["depth"]["value"]),
        )
        for item in json_data["soilTemp"]
    ]

    # Create WeatherForecastData instance
    weather_forecast_data = WeatherForecastData(
        general_situation=json_data["generalSituation"],
        weather_forecast=weather_forecast,
        update_time=datetime.fromisoformat(json_data["updateTime"]),
        sea_temp=sea_temp,
        soil_temp=soil_temp,
    )

    return weather_forecast_data


def get_weather_forecast():
    params = {"dataType": "fnd", "lang": "tc"}
    forecast_json = requests.get(HKO_URL, params=params).json()

    return parse_weather_forecast(forecast_json)


# Example JSON data (replace with actual JSON response)
# json_data = {...}
# weather_forecast_data = parse_weather_forecast(json_data)
# print(weather_forecast_data)
