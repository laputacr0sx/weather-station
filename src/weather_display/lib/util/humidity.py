import requests
from datetime import datetime
import csv
from io import StringIO
from dataclasses import dataclass


# Define the dataclass
@dataclass
class HumidityData:
    datetime: datetime
    station: str
    humidity: str


def get_humidity_data(station_no: int = 15):
    # URL of the CSV file
    humidity_url = "https://res.data.gov.hk/api/get-download-file?name=https%3A%2F%2Fdata.weather.gov.hk%2FweatherAPI%2Fhko_data%2Fregional-weather%2Flatest_1min_humidity_uc.csv"

    temperature_url = "https://res.data.gov.hk/api/get-download-file?name=https%3A%2F%2Fdata.weather.gov.hk%2FweatherAPI%2Fhko_data%2Fregional-weather%2Flatest_1min_temperature_uc.csv"

    # Fetch the CSV data
    response = requests.get(humidity_url)
    response.raise_for_status()  # Raise an error for bad responses

    # Use StringIO to simulate a file object
    csv_file = StringIO(response.text)

    # Read the CSV data
    reader = csv.reader(csv_file)
    next(reader)  # Skip the header

    # Parse the CSV data into a list of WindData objects
    humidity_data_list = [
        HumidityData(
            datetime=datetime.strptime(row[0], "%Y%m%d%H%M"),
            station=row[1],
            humidity=row[2],
        )
        for row in reader
    ]

    return humidity_data_list[station_no]
