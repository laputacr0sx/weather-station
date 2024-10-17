import pandas as pd

# File paths for the local CSV files
file_paths = {
    "humidity": "latest_1min_humidity_uc.csv",
    "temperature": "latest_1min_temperature_uc.csv",
    "pressure": "latest_1min_pressure_uc.csv",
    "wind": "latest_10min_wind_uc.csv",
    "visibility": "latest_10min_visibility_uc.csv",
}

# Load each CSV file into a DataFrame
humidity_df = pd.read_csv(file_paths["humidity"])
temperature_df = pd.read_csv(file_paths["temperature"])
pressure_df = pd.read_csv(file_paths["pressure"])
wind_df = pd.read_csv(file_paths["wind"])
visibility_df = pd.read_csv(file_paths["visibility"])

for df in [humidity_df, temperature_df, pressure_df, wind_df, visibility_df]:
    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], format="%Y%m%d%H%M")

# Merge all DataFrames on '自動氣象站'
merged_df = (
    wind_df.merge(
        temperature_df, on="自動氣象站", how="outer", suffixes=("_wind", "_temp")
    )
    .merge(humidity_df, on="自動氣象站", how="outer", suffixes=("", "_humidity"))
    .merge(pressure_df, on="自動氣象站", how="outer", suffixes=("", "_pressure"))
    .merge(visibility_df, on="自動氣象站", how="outer", suffixes=("", "_visi"))
)

print(merged_df)

# Drop duplicate '日期時間' columns if they exist
# if "日期時間_temp" in merged_df.columns:
#     merged_df = merged_df.drop(
#         columns=["日期時間_temp", "日期時間_humidity", "日期時間_pressure"]
#     )

# Save the merged DataFrame to a new CSV file
merged_df.to_csv("summarized_weather_data.csv", index=False)

# Created/Modified files during execution:
print("summarized_weather_data.csv")
