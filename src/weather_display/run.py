import io
import logging
import os
from datetime import datetime, timedelta

import requests
from PIL import Image, ImageDraw

from weather_display import ASSEST_DIR
from weather_display.assest.font.cubic_font import (
    font12,
    font24,
    font32,
)
from weather_display.lib.render.footer import render_footer_section
from weather_display.lib.render.forecast import render_forecast_section
from weather_display.lib.render.header import render_header_section
from weather_display.lib.util.current_weather import (
    CurrentWeather,
    parse_current_weather,
)
from weather_display.lib.util.rainfall import render_rainfall_chart
from weather_display.lib.util.weather_forecast import (
    parse_weather_forecast,
)

logging.basicConfig(
    filename="./error.log",  # Log file name
    level=logging.DEBUG,  # Log level
    format="%(asctime)s\t----[%(levelname)s]----\t%(message)s",  # Log format
    datefmt="%Y-%m-%d %H:%M:%S",  # Date format
)


HKO_URL = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php"

EPD_WIDTH = 800
EPD_HEIGHT = 480


def get_current_weather():
    params = {"dataType": "rhrread", "lang": "tc"}
    current_json = requests.get(HKO_URL, params=params).json()

    return parse_current_weather(current_json)


def get_weather_forecast():
    params = {"dataType": "fnd", "lang": "tc"}
    forecast_json = requests.get(HKO_URL, params=params).json()

    return parse_weather_forecast(forecast_json)


def get_record_time_diff(curr: datetime, record_time: datetime):
    time_difference: timedelta = curr - record_time
    total_minutes: float = time_difference.total_seconds() // 60

    return total_minutes


def get_now_str(now: datetime):
    chinese_months = [
        "一月",
        "二月",
        "三月",
        "四月",
        "五月",
        "六月",
        "七月",
        "八月",
        "九月",
        "十月",
        "十一月",
        "十二月",
    ]

    chinese_weekdays = ["一", "二", "三", "四", "五", "六", "日"]

    month = chinese_months[now.month - 1]
    day = now.day
    weekday = chinese_weekdays[now.weekday()]

    return f"{month}{day}日({weekday})"


"""
Methods below are rendering related
"""


def render_rainfall_section(image: Image.Image):
    chart_byte = render_rainfall_chart()

    chart = Image.open(io.BytesIO(chart_byte))

    # chart_path = "./rainfall.bmp"
    # image.paste(Image.open(chart_path), (270, 250))
    image.paste(chart, (270, 220))


def render_minor_dashboard(
    weather: CurrentWeather, draw: ImageDraw.ImageDraw, image: Image.Image
):
    valid_data = [
        [
            {
                "icon_uri": "sunrise.png",
                "name": "日出時間",
                "data": "05:59",
                "unit": None,
            },
            {"icon_uri": "80.png", "name": "風速", "data": "3", "unit": None},
            {
                "icon_uri": "uv.png",
                "name": "紫外線指數",
                "data": weather.uvindex.data[0].value,
                "unit": None,
            },
            {
                "icon_uri": "thermo.png",
                "name": "室內氣溫",
                "data": 25.9,
                "unit": "C",
            },
        ],
        [
            {
                "icon_uri": "sunset.png",
                "name": "日落時間",
                "data": "18:02",
                "unit": None,
            },
            {
                "icon_uri": "outdoor_humidity.png",
                "name": f"{weather.rainfall.data[6].place}降雨量",
                "data": weather.rainfall.data[6].max,
                "unit": "mm",
            },
            {
                "icon_uri": "barometer.png",
                "name": "室內氣壓",
                "data": 1015,
                "unit": "in",
            },
            {
                "icon_uri": "humidity.png",
                "name": "室內濕度",
                "data": 61.2,
                "unit": "%",
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

            draw.text((x1 + 48, y1), f"{name}", font=font12, fill=0)
            draw.text((x1 + 48, y1 + 16), f"{data}", font=font32, fill=0)
            draw.text((x1 + 150 - 30, y1 + 20), unit, font=font24, fill=0)

            icon = Image.open(os.path.join(ASSEST_DIR, "img", "pic", img))
            resized_icon = icon.resize((48, 48))
            image.paste(resized_icon, (x1, y1))


def main():
    try:
        # logging.info("Reading from BME280")

        logging.info("Gathering System Information")
        now: datetime = datetime.now()
        logging.info("Current Datetime GOT! ")

        weather = get_current_weather()
        logging.info("Current Weather GOT! ")

        forecast = get_weather_forecast()
        logging.info("Weatherforecast GOT! ")

        time_diff = get_record_time_diff(now, weather.temperature.record_time)

        logging.info("Generating Image")
        main_image = Image.new("1", (EPD_WIDTH, EPD_HEIGHT), 255)

        logging.info("Drawing Image")
        draw = ImageDraw.Draw(main_image)

        location = "沙田馬鞍山"
        now_str = get_now_str(now)

        logging.info("Rendering different sections...")
        render_header_section(weather, location, now_str, draw, main_image)
        render_forecast_section(forecast, draw, main_image)
        render_rainfall_section(main_image)
        render_minor_dashboard(weather, draw, main_image)
        render_footer_section(draw, time_diff, now)

        logging.info("Rendering Process Finished")

        logging.info("Display Image")
        main_image.show()
        logging.info("Displaying Image Success")

    except IOError as e:
        logging.info(e)

    except Exception:
        # Log the exception with traceback
        logging.error("An error occurred", exc_info=True)


if __name__ == "__main__":
    main()
