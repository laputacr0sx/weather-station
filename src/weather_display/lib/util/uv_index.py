import requests
from datetime import datetime
import csv
from io import StringIO
from dataclasses import dataclass


@dataclass
class UVIndex:
    datetime: datetime
    uv_index: str


def get_uv_data():
    # URL of the CSV file
    url = "https://res.data.gov.hk/api/get-download-file?name=https%3A%2F%2Fdata.weather.gov.hk%2FweatherAPI%2Fhko_data%2Fregional-weather%2Flatest_15min_uvindex.csv"

    # Fetch the CSV data
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses

    # Use StringIO to simulate a file object
    csv_file = StringIO(response.text)

    # Read the CSV data
    reader = csv.reader(csv_file)
    next(reader)  # Skip the header

    # Parse the CSV data into a list of WindData objects
    uv_data = [
        UVIndex(datetime=datetime.strptime(row[0], "%Y%m%d%H%M"), uv_index=row[1])
        for row in reader
    ]

    return uv_data
