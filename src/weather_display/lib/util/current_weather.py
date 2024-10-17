from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

import requests
from weather_display import HKO_URL


class PurpleUnit(Enum):
    C = "C"
    PERCENT = "percent"


@dataclass
class HumidityDatum:
    unit: PurpleUnit
    value: int
    place: str


@dataclass
class Humidity:
    record_time: datetime
    data: List[HumidityDatum]


class Main(Enum):
    EMPTY = ""
    FALSE = "FALSE"


class FluffyUnit(Enum):
    MM = "mm"


@dataclass
class RainfallDatum:
    unit: FluffyUnit
    place: str
    max: int
    main: Main


@dataclass
class Rainfall:
    data: List[RainfallDatum]
    start_time: datetime
    end_time: datetime


@dataclass
class UvindexDatum:
    place: str
    value: int
    desc: str


@dataclass
class Uvindex:
    data: List[UvindexDatum]
    record_desc: str


@dataclass
class CurrentWeather:
    rainfall: Rainfall
    warning_message: str
    icon: List[int]
    icon_update_time: datetime
    uvindex: Uvindex
    update_time: datetime
    temperature: Humidity
    tcmessage: str
    mintemp_from00_to09: str
    rainfall_from00_to12: str
    rainfall_last_month: str
    rainfall_january_to_last_month: str
    humidity: Humidity


# Example usage
# Assuming you have a JSON response parsed into a dictionary named `json_data`
# You would need to convert the JSON data into these classes


# Example function to parse JSON into the CurrentWeather dataclass
def parse_current_weather(json_data: dict) -> CurrentWeather:
    # Parse rainfall data
    rainfall_data = [
        RainfallDatum(
            unit=FluffyUnit(datum["unit"]),
            place=datum["place"],
            max=datum["max"],
            main=Main(datum["main"] if datum["main"] else Main.EMPTY),
        )
        for datum in json_data["rainfall"]["data"]
    ]
    rainfall = Rainfall(
        data=rainfall_data,
        start_time=datetime.fromisoformat(json_data["rainfall"]["startTime"]),
        end_time=datetime.fromisoformat(json_data["rainfall"]["endTime"]),
    )

    if type(json_data["uvindex"] is str):
        uvindex = Uvindex(data=[], record_desc="")
    else:
        uvindex_data = [
            UvindexDatum(place=datum["place"], value=datum["value"], desc=datum["desc"])
            for datum in json_data["uvindex"]["data"]
        ]

        uvindex = Uvindex(
            data=uvindex_data, record_desc=json_data["uvindex"]["recordDesc"]
        )

    # Parse temperature data
    temperature_data = [
        HumidityDatum(
            unit=PurpleUnit(datum["unit"]),
            value=datum["value"] or 0,
            place=datum["place"],
        )
        for datum in json_data["temperature"]["data"]
    ]
    temperature = Humidity(
        record_time=datetime.fromisoformat(
            json_data["temperature"]["recordTime"]
        ).replace(tzinfo=None),
        data=temperature_data,
    )

    # Parse humidity data
    humidity_data = [
        HumidityDatum(
            unit=PurpleUnit(datum["unit"]), value=datum["value"], place=datum["place"]
        )
        for datum in json_data["humidity"]["data"]
    ]
    humidity = Humidity(
        record_time=datetime.fromisoformat(json_data["humidity"]["recordTime"]),
        data=humidity_data,
    )

    # Create CurrentWeather instance
    current_weather = CurrentWeather(
        rainfall=rainfall,
        warning_message=json_data.get("warningMessage", ""),
        icon=json_data.get("icon", []),
        icon_update_time=datetime.fromisoformat(json_data["iconUpdateTime"]),
        uvindex=uvindex,
        update_time=datetime.fromisoformat(json_data["updateTime"]),
        temperature=temperature,
        tcmessage=json_data.get("tcmessage", ""),
        mintemp_from00_to09=json_data.get("mintempFrom00To09", ""),
        rainfall_from00_to12=json_data.get("rainfallFrom00To12", ""),
        rainfall_last_month=json_data.get("rainfallLastMonth", ""),
        rainfall_january_to_last_month=json_data.get("rainfallJanuaryToLastMonth", ""),
        humidity=humidity,
    )

    return current_weather


def get_current_weather():
    params = {"dataType": "rhrread", "lang": "tc"}
    current_json = requests.get(HKO_URL, params=params).json()

    return parse_current_weather(current_json)


# Example JSON data (replace with actual JSON response)
# json_data = {...}
# current_weather = parse_current_weather(json_data)
# print(current_weather)
