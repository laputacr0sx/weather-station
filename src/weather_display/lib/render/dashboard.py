import os

from PIL import Image, ImageDraw
from weather_display import PIC_DIR
from weather_display.assest.font.cubic_font import font12, font18, font32
from weather_display.lib.util.current_weather import CurrentWeather
from weather_display.lib.util.env_sensor import EnvironmentData
from weather_display.lib.util.hourly_rainfall import get_hourly_rainfall
from weather_display.lib.util.uv_index import UVIndex
from weather_display.lib.util.wind import WindData


def render_minor_dashboard(
    env: EnvironmentData,
    wind: WindData,
    uv: UVIndex,
    weather: CurrentWeather,
    draw: ImageDraw.ImageDraw,
    image: Image.Image,
):
    valid_data = [
        [
            {
                "icon_uri": "sunrise.png",
                "name": "日出時間",
                "data": "05:59",
                "unit": None,
            },
            {
                "icon_uri": "80.png",
                "name": f"{wind.station}風速",
                "data": f"{wind.avg_wind_speed}",
                "unit": f"{wind.wind_direction}",
            },
            {
                "icon_uri": "uv.png",
                "name": "紫外線指數",
                # "data": weather.uvindex.data[0].value,
                "data": uv.uv_index,
                "unit": f"@{uv.datetime.strftime("%H:%M")}",
            },
            {
                "icon_uri": "thermo.png",
                "name": "室內氣溫",
                "data": env.temperature,
                "unit": None,
            },
        ],
        [
            {
                "icon_uri": "sunset.png",
                "name": "日落時間",
                "data": "18:02",
                "unit": None,
            },
            # {
            #     "icon_uri": "outdoor_humidity.png",
            #     "name": f"{weather.rainfall.data[6].place}降雨量",
            #     "data": weather.rainfall.data[6].max,
            #     "unit": "mm",
            # },
            {
                "icon_uri": "outdoor_humidity.png",
                "name": f"{weather.rainfall.data[6].place}降雨量",
                "data": get_hourly_rainfall().hourly_rainfall[21].value,
                "unit": "mm",
            },
            {
                "icon_uri": "barometer.png",
                "name": "室內氣壓",
                "data": env.pressure,
                "unit": "in",
            },
            {
                "icon_uri": "humidity.png",
                "name": "室內濕度",
                "data": env.humidity,
                "unit": None,
            },
        ],
    ]

    ROW = 2
    COL = 4
    top_left_x = 2
    top_left_y = 230
    cell_width = 150
    cell_height = 64

    for i in range(ROW):
        for j in range(COL):
            x1 = top_left_x + i * cell_width
            y1 = top_left_y + j * cell_height

            cell = valid_data[i][j]
            name = cell["name"]
            data = cell["data"]
            img = cell["icon_uri"] or "na.png"
            unit = cell["unit"] or ""

            data_length = len(data) if type(data) is str else len(str(abs(data)))

            draw.text((x1 + 48, y1), f"{name}", font=font12, fill=0)
            draw.text((x1 + 48, y1 + 16), f"{data}", font=font32, fill=0)
            draw.text(
                (x1 + 48 + data_length * 18 + 2, y1 + cell_height - 34),
                unit,
                font=font18,
                fill=0,
            )

            icon = Image.open(os.path.join(PIC_DIR, img))
            resized_icon = icon.resize((48, 48))
            image.paste(resized_icon, (x1, y1))
