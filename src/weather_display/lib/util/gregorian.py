import logging
from dataclasses import dataclass
from datetime import datetime

import requests


@dataclass
class GregorianDate:
    lunar_year: str
    lunar_date: str


def parse_gregorian_json(json: dict) -> GregorianDate:
    return GregorianDate(lunar_year=json["LunarYear"], lunar_date=json["LunarDate"])


def get_gregorian_date(date: datetime = datetime.now()):
    url = "https://data.weather.gov.hk/weatherAPI/opendata/lunardate.php"

    year = date.year
    month = date.month
    day = date.day

    params = {"date": f"{year}-{month}-{day}"}

    res = requests.get(url, params)
    res.raise_for_status()

    return parse_gregorian_json(res.json())


try:
    get_gregorian_date()

except requests.HTTPError:
    logging.error("Something went wrong...")

except ConnectionError as e:
    logging.error("Some error occurred")
