import logging
import requests
import pandas as pd
from io import StringIO

# List of URLs to download CSV files from
urls = [
    "https://res.data.gov.hk/api/get-download-file?name=https%3A%2F%2Fdata.weather.gov.hk%2FweatherAPI%2Fhko_data%2Fregional-weather%2Flatest_1min_humidity_uc.csv",
    "https://res.data.gov.hk/api/get-download-file?name=https%3A%2F%2Fdata.weather.gov.hk%2FweatherAPI%2Fhko_data%2Fregional-weather%2Flatest_1min_temperature_uc.csv",
    "https://res.data.gov.hk/api/get-download-file?name=https%3A%2F%2Fdata.weather.gov.hk%2FweatherAPI%2Fhko_data%2Fregional-weather%2Flatest_1min_pressure_uc.csv",
    "https://res.data.gov.hk/api/get-download-file?name=https%3A%2F%2Fdata.weather.gov.hk%2FweatherAPI%2Fhko_data%2Fregional-weather%2Flatest_10min_wind_uc.csv",
    "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php?dataType=LTMV&lang=tc&rformat=csv",
]


measures = ["humidity", "temperature", "pressure", "wind", "visibility"]


# Function to fetch and load CSV data into a DataFrame
def fetch_csv(url):
    response = requests.get(url)
    if response.status_code == 200:
        csv_data = StringIO(response.text)
        return pd.read_csv(csv_data)
    else:
        print(f"Failed to download data from {url}")
        return None


try:
    # Fetch and load all CSVs into DataFrames
    dataframes = [fetch_csv(url) for url in urls]

    # Filter out any None values in case of failed downloads
    dataframes = [df for df in dataframes if df is not None]

    # Convert '日期時間' to datetime using .iloc
    for df in dataframes:
        df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], format="%Y%m%d%H%M")

    # Merge all DataFrames on '自動氣象站'
    merged_df = dataframes[0]
    # for df, m in dataframes[1:], measures:
    #     merged_df = merged_df.merge(
    #         df, on="自動氣象站", how="outer", suffixes=("", f"_{m}")
    #     )
    for i, df in enumerate(dataframes[1:], start=1):
        suffix = f"_{measures[i]}"
        merged_df = merged_df.merge(
            df, on="自動氣象站", how="outer", suffixes=("", suffix)
        )

    print(merged_df.columns)

    # for column in merged_df.columns:
    #     if (
    #         column.startswith("日期時間")
    #         and merged_df[column].duplicated(keep="first").any()
    #     ):
    #         merged_df.drop(columns=column, inplace=True)

    # Drop duplicate '日期時間' columns if they exist
    merged_df = merged_df.loc[:, ~merged_df.columns.duplicated()]

    # Save the merged DataFrame to a new CSV file
    merged_df.to_csv("summarized_weather_data.csv", index=False)

    # Created/Modified files during execution:
    print("summarized_weather_data.csv")

except Exception:
    logging.error("Something went wrong", Exception)
