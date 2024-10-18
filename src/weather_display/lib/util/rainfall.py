import io

import matplotlib.pyplot as plt
import pandas as pd
import requests

personal_path = '/Users/veilics/Library/Fonts/'
font_path = personal_path + 'Cubic_11.ttf'


def addlabels(x, y):
    for i in range(len(x)):
        if y[i] == 0:
            break
        mid_point = (0 + y[i]) / 2
        plt.text(i, mid_point, y[i], ha='center', c='white', va='center')


def render_rainfall_chart():
    # Step 1: Download the CSV file
    url = 'https://data.weather.gov.hk/weatherAPI/hko_data/F3/Gridded_rainfall_nowcast.csv'
    response = requests.get(url)

    # Step 2: Read the CSV file into a DataFrame
    df = pd.read_csv(io.StringIO(response.text))

    df = df.rename(
        columns={
            'Updated Date and Time (in Hong Kong Time)': 'updatedAt',
            'Ending Date and Time (in Hong Kong Time)': 'endedAt',
            'Half-hourly Nowcast Accumulated Rainfall (mm)': 'rainfall',
        }
    )

    df['updatedAt'] = pd.to_datetime(df['updatedAt'], format='%Y%m%d%H%M')
    df['endedAt'] = pd.to_datetime(df['endedAt'], format='%Y%m%d%H%M')

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
    filtered_data['group'] = filtered_data.index // 4

    # Calculate the average rainfall for each group
    average_rainfall = filtered_data.groupby('group')['rainfall'].mean()
    # average_rainfall = [0.4, 1, 1.2, 0.2]

    # Display the filtered data and average rainfall
    # print(filtered_data)
    # print(average_rainfall)

    # Time intervals
    ended_at_formatted = (
        filtered_data['endedAt'].dt.strftime('%I:%M').unique()
    )  # hour = "小時"

    # Create a figure with a white background
    # plt.figure(figsize=(0.9, 0.31), facecolor="white")
    plt.figure(figsize=(1.8, 0.65), facecolor='white', dpi=300)

    font = {'family': 'Cubic 11', 'size': 4}
    plt.rc('font', **font)

    plt.bar(
        ended_at_formatted,
        average_rainfall,
        color='black',
        edgecolor='black',
    )

    addlabels(ended_at_formatted, average_rainfall)

    # Remove axis labels and title
    plt.xlabel('')
    plt.ylabel('')
    plt.title('')

    # plt.xticks(visible=False)

    # Set y-axis to start from 0
    # plt.ylim(0, max(average_rainfall) + 0.5)
    ylimit = max(average_rainfall) * 1.1 if max(average_rainfall) > 0 else 0.3
    # Add a little space above the max value for better visualization
    plt.ylim(0, ylimit)

    # Add grid for scale reference
    # plt.grid(True, color="gray", linestyle="--", linewidth=0.5)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    # plt.show()
    plt.close()
    buf.seek(0)

    # Display the plot

    return buf.getvalue()
