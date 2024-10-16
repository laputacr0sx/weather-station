import aiohttp
import asyncio
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

# Mapping of URLs to measurement types
measurement_types = ["humidity", "temperature", "pressure", "wind"]


async def fetch_csv(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            csv_data = await response.text()
            return pd.read_csv(StringIO(csv_data))
        else:
            print(f"Failed to download data from {url}")
            return None


async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_csv(session, url) for url in urls]
        dataframes = await asyncio.gather(*tasks)

        # Filter out any None values in case of failed downloads
        dataframes = [df for df in dataframes if df is not None]

        # Add a column to each DataFrame to identify the measurement type
        for df, measurement in zip(dataframes, measurement_types):
            df["Measurement"] = measurement

        # Concatenate all DataFrames
        combined_df = pd.concat(dataframes, ignore_index=True)

        # Restructure the DataFrame
        restructured_df = combined_df.pivot_table(
            index="自動氣象站",
            columns="Measurement",
            values="數值",  # Assuming '數值' is the column with the measurement values
            aggfunc="first",
        )

        # Save the restructured DataFrame to a new CSV file
        restructured_df.to_csv("restructured_weather_data.csv")


# Run the asynchronous main function
# Use asyncio.run(main()) if not in an interactive environment like Jupyter
asyncio.run(main())

# Created/Modified files during execution:
print("restructured_weather_data.csv")
