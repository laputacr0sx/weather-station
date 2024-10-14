import logging
from datetime import datetime, timedelta

import requests
from numpy import resize
from PIL import Image, ImageDraw, ImageFont

from current_weather import parse_current_weather, CurrentWeather
from rainfall import render_rainfall_chart
from weather_forecast import parse_weather_forecast, WeatherForecast

logging.basicConfig(
    filename="./error.log",  # Log file name
    level=logging.DEBUG,  # Log level
    format="%(asctime)s\t----[%(levelname)s]----\t%(message)s",  # Log format
    datefmt="%Y-%m-%d %H:%M:%S",  # Date format
)

LAB_DIR = "./lib/"
PIC_DIR = "./pic/"
LINE_DIR = "./out/"
CUBIC_FONT_PATH = PIC_DIR + "Cubic_11.ttf"
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
    render_rainfall_chart()

    chart_path = "./rainfall.bmp"
    image.paste(Image.open(chart_path), (250, 230))


def render_forecast_section():
    return


def render_minor_dashboard(draw: ImageDraw.ImageDraw):
    ROW = 2
    COL = 5
    top_left_x = 2
    top_left_y = 210
    cell_width = 140
    cell_height = 54

    for i in range(ROW):
        for j in range(COL):
            x1 = top_left_x + i * cell_width
            y1 = top_left_y + j * cell_height

            draw.text((x1, y1), f"Cell {i}{j}", font=font32, fill=0)


def render_major_section(
    image: Image.Image, draw: ImageDraw.ImageDraw, weather: CurrentWeather
):
    # Render weather icon
    icon = Image.open(f"{LINE_DIR}/{weather.icon[0]}.png")
    resized_icon = icon.resize((256, 256))
    image.paste(resized_icon, (2, 2))

    # Render temperature
    draw.text((278, 20), f"{weather.temperature.data[0].value} C", font=font64, fill=0)
    draw.text((358, 20), "o", font=font24, fill=0)
    # Render humidity
    draw.text((408, 20), f"{weather.humidity.data[0].value}%", font=font64, fill=0)


def render_header_section(
    location: str, now_str: str, draw: ImageDraw.ImageDraw, image: Image.Image
):
    location_length = len(location)

    now_str = get_now_str(now)
    total_str_length = len(now_str)
    now_str_digit_length = sum(c.isdigit() for c in now_str) + 2
    now_str_length = total_str_length - now_str_digit_length

    estimate_location_length = 800 - (
        location_length * 48 + (location_length - 1) * 4 + 2
    )
    estimate_date_length = 800 - (
        now_str_length * 32 + now_str_digit_length * 16 + (total_str_length - 1) * 2 + 2
    )

    draw.text((estimate_location_length, 2), location, font=font48, fill=0)
    draw.text((estimate_date_length, 54), now_str, font=font32, fill=0)


def render_footer_section(draw: ImageDraw.ImageDraw, time_diff: float, now: datetime):
    draw.text((390, 464), f"更新於: {time_diff:.0f} 分鐘前", font=font12, fill=0)
    draw.text(
        (620, 464), f'擷取於:{now.strftime("%Y-%m-%d %H:%M:%S")}', font=font12, fill=0
    )
    return


try:
    now: datetime = datetime.now()

    logging.info("Reading from BME280")
    temperature, humidity, pressure = 25.0, 60.5, 1009.12

    font64 = ImageFont.truetype(CUBIC_FONT_PATH, 64)
    font48 = ImageFont.truetype(CUBIC_FONT_PATH, 48)
    font40 = ImageFont.truetype(CUBIC_FONT_PATH, 40)
    font32 = ImageFont.truetype(CUBIC_FONT_PATH, 32)
    font24 = ImageFont.truetype(CUBIC_FONT_PATH, 24)
    font18 = ImageFont.truetype(CUBIC_FONT_PATH, 18)
    font12 = ImageFont.truetype(CUBIC_FONT_PATH, 12)

    # Fetching HKO Weather
    logging.info("Fetching Weather Information")

    weather = get_current_weather()

    time_diff = get_record_time_diff(now, weather.temperature.record_time)

    logging.info("Drawing Image")
    Himage = Image.new("1", (EPD_WIDTH, EPD_HEIGHT), 255)  # 255: clear the frame
    draw = ImageDraw.Draw(Himage)

    # # Dynamic render pixle
    location = "沙田馬鞍山"
    now_str = get_now_str(now)

    render_header_section(location, now_str, draw, Himage)
    # draw.text((10, 200), f"室內溫度: {temperature:.1f} C", font=font24, fill=0)
    # draw.text((10, 240), f"室內濕度: {humidity:.0f} %", font=font24, fill=0)
    # draw.text((10, 280), f"室內氣壓: {pressure:.2f} hPa", font=font24, fill=0)

    logging.info("Fetching Weather Forecast Information")
    forecast = get_weather_forecast()
    # Drawing boundaries of forecast

    for i in range(5):
        curr_cast = forecast.weather_forecast[i]
        x1 = 248 + i * 110
        y1 = 96
        x2 = x1 + 110
        y2 = 220

        date_str = curr_cast.forecast_date
        forecast_icon_number = curr_cast.forecast_icon
        week_date = curr_cast.week[2]
        htemp = curr_cast.forecast_maxtemp.value
        ltemp = curr_cast.forecast_mintemp.value

        bmp = Image.open(f"{LINE_DIR}/{forecast_icon_number}.png")
        resize_bmp = bmp.resize((72, 72))
        Himage.paste(resize_bmp, (x1 + 4, y1 + 20))

        draw.rectangle((x1, y1, x2, y2), outline=0, width=1)
        draw.text((x1 + 44, y1 + 2), f"{week_date}", font=font24, fill=0)
        draw.text((x1 + 70, y1 + 28), f"{htemp:.0f}", font=font24, fill=0)
        draw.text((x1 + 70, y1 + 54), f"{ltemp:.0f}", font=font24, fill=0)

    render_major_section(Himage, draw, weather)
    render_rainfall_section(Himage)
    render_minor_dashboard(draw)
    render_footer_section(draw, time_diff, now)

    logging.info("Display Image")
    Himage.show()

except IOError as e:
    logging.info(e)

except Exception:
    # Log the exception with traceback
    logging.error("An error occurred", exc_info=True)
