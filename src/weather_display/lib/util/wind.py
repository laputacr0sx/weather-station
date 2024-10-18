import csv
from dataclasses import dataclass
from datetime import datetime
from io import StringIO

import requests


# Define the dataclass
@dataclass
class WindData:
    datetime: datetime
    station: str
    wind_direction: str
    avg_wind_speed: str
    max_gust_speed: str


def get_wind_data(station_no: int = 15):
    # URL of the CSV file
    url = "https://res.data.gov.hk/api/get-download-file?name=https%3A%2F%2Fdata.weather.gov.hk%2FweatherAPI%2Fhko_data%2Fregional-weather%2Flatest_10min_wind_uc.csv"

    # Fetch the CSV data
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses

    # Use StringIO to simulate a file object
    csv_file = StringIO(response.text)

    # Read the CSV data
    reader = csv.reader(csv_file)
    next(reader)  # Skip the header

    # Parse the CSV data into a list of WindData objects
    wind_data_list = [
        WindData(
            datetime=datetime.strptime(row[0], "%Y%m%d%H%M"),
            station=row[1],
            wind_direction=row[2],
            avg_wind_speed=row[3],
            max_gust_speed=row[4],
        )
        for row in reader
    ]

    return wind_data_list[station_no]
