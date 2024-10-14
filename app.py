import requests
import numpy
import pandas as pd

lastest_one_minute_mean_temperature = "https://data.weather.gov.hk/weatherAPI/hko_data/csdi/dataset/latest_1min_temperature_csdi_16.csv"
lastest_10min_wind = "https://data.weather.gov.hk/weatherAPI/hko_data/csdi/dataset/latest_10min_wind_csdi_15.csv"
lastest_one_minute_mean_rh = "https://data.weather.gov.hk/weatherAPI/hko_data/csdi/dataset/latest_1min_humidity_csdi_13.csv"
lastest_15min_uvindex = "https://data.weather.gov.hk/weatherAPI/hko_data/csdi/dataset/latest_15min_uvindex_csdi_0.csv"
sun_position = "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php?dataType=SRS&year=2024&rformat=csv"


def get_weather_data():
    return ""


# Define the file paths (assuming they are named file1.csv, file2.csv, file3.csv)
file1 = "~/Downloads/latest_1min_humidity_csdi_13.csv"
file2 = "~/Downloads/latest_1min_temperature_csdi_16.csv"
file3 = "~/Downloads/latest_10min_wind_csdi_15.csv"

# Read the CSV files
df1 = pd.read_csv(file1, usecols=range(9))
df2 = pd.read_csv(file2, usecols=range(9))
df3 = pd.read_csv(file3, usecols=range(9))


def combine_datetime(df):
    df.rename(
        columns={
            "Date time (Year)": "year",
            "Date time (Month)": "month",
            "Date time (Day)": "day",
            "Date time (Hour)": "hour",
            "Date time (Minute)": "minute",
            "Date time (Second)": "second",
            "Date time (Time Zone)": "tz",
        },
        inplace=True,
    )
    df["second"] = "0"

    df["Datetime"] = pd.to_datetime(
        df["year"].astype(str)
        + "-"
        + df["month"].astype(str)
        + "-"
        + df["day"].astype(str)
        + " "
        + df["hour"].astype(str)
        + ":"
        + df["minute"].astype(str)
        + ":"
        + df["second"].astype(str)
    )

    return df
