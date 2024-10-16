import matplotlib.pyplot as plt
from PIL import Image
import requests
import io
import pandas as pd
from pyfonts import load_font
from matplotlib.font_manager import fontManager
from matplotlib import font_manager

personal_path = "/Users/veilics/Library/Fonts/"
font_path = personal_path + "Cubic_11.ttf"


def render_rainfall_chart():
    # Step 1: Download the CSV file
    url = "https://data.weather.gov.hk/weatherAPI/hko_data/F3/Gridded_rainfall_nowcast.csv"
    response = requests.get(url)

    # Step 2: Read the CSV file into a DataFrame
    df = pd.read_csv(io.StringIO(response.text))

    df = df.rename(
        columns={
            "Updated Date and Time (in Hong Kong Time)": "updatedAt",
            "Ending Date and Time (in Hong Kong Time)": "endedAt",
            "Half-hourly Nowcast Accumulated Rainfall (mm)": "rainfall",
        }
    )

    df["updatedAt"] = pd.to_datetime(df["updatedAt"], format="%Y%m%d%H%M")
    df["endedAt"] = pd.to_datetime(df["endedAt"], format="%Y%m%d%H%M")

    # Row numbers to extract (zero-based index)
    row_numbers = [
        7204,
        7205,
        7325,
        7326,
        21845,
        21846,
        21966,
        21967,
        36486,
        36487,
        36607,
        36608,
        51127,
        51128,
        51248,
        51249,
    ]

    # Step 3: Filter the rows by their index
    filtered_data = df.iloc[row_numbers]

    filtered_data = filtered_data.reset_index(
        drop=True
    )  # Reset index to ensure sequential grouping
    filtered_data["group"] = filtered_data.index // 4

    # Calculate the average rainfall for each group
    average_rainfall = filtered_data.groupby("group")["rainfall"].mean()

    # Display the filtered data and average rainfall
    # print(filtered_data)
    # print(average_rainfall)

    # Time intervals
    ended_at_formatted = (
        filtered_data["endedAt"].dt.strftime("%I:%M").unique()
    )  # hour = "小時"

    # Create a figure with a white background
    plt.figure(figsize=(1.8, 0.65), facecolor="white")
    # plt.figure(figsize=(5.2, 2.1), facecolor="white")

    font = {"family": "Cubic 11", "size": 4}
    plt.rc("font", **font)

    plt.bar(
        ended_at_formatted,
        average_rainfall,
        color="black",
        edgecolor="black",
    )

    # Remove axis labels and title
    plt.xlabel("")
    plt.ylabel("")
    plt.title("")

    # plt.xticks(visible=False)

    # Set y-axis to start from 0
    plt.ylim(
        0, max(average_rainfall) + 0.5
    )  # Add a little space above the max value for better visualization

    # Add grid for scale reference
    # plt.grid(True, color="gray", linestyle="--", linewidth=0.5)

    # plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # plt.tight_layout()

    # Save the plot as a PNG file
    plt.savefig(
        "rainfall.png",
        format="png",
        bbox_inches="tight",
        dpi=300,
    )

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=300)

    # Convert the PNG file to BMP format with 1-bit color
    with Image.open("rainfall.png") as img:
        img.convert("1").save("rainfall.bmp", format="bmp")

    plt.close()
    buf.seek(0)

    return buf.getvalue()

    # Display the plot
    # plt.show()
