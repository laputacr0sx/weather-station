from dataclasses import dataclass
from datetime import datetime

import requests


@dataclass
class SunStatus:
    date: str
    rise: str
    transit: str
    set: str


def parse_sun_json(json: dict) -> SunStatus:
    return SunStatus(
        date=json["data"][0][0],
        rise=json["data"][0][1],
        transit=json["data"][0][2],
        set=json["data"][0][3],
    )


def get_sun_status(date: datetime = datetime.now()):
    url = "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
    params = {
        "dataType": "SRS",
        "rformat": "json",
        "year": f"{date.year}",
        "month": f"{date.month}",
        "day": f"{date.day}",
    }

    res = requests.get(url, params)

    res.raise_for_status()

    return parse_sun_json(res.json())
