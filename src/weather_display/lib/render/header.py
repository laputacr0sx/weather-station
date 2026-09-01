import os

from PIL import Image, ImageDraw
from weather_display import EPD_WIDTH, PIC_DIR
from weather_display.assest.font.cubic_font import (
    font12,
    font14,
    font18,
    font24,
    font32,
    font40,
    font48,
    font80,
)
from weather_display.lib.render.text import draw_celsius, draw_run
from weather_display.lib.util.current_weather import CurrentWeather
from weather_display.lib.util.env_sensor import EnvironmentData
from weather_display.lib.util.gregorian import GregorianDate
from weather_display.lib.util.humidity import HumidityData


def render_header_section(
    gregorian: GregorianDate,
    weather: CurrentWeather,
    humidity: HumidityData,
    location: str,
    now: str,
    draw: ImageDraw.ImageDraw,
    image: Image.Image,
    env: EnvironmentData,
):
    major_weather(weather, humidity, image, draw)
    dates(location, now, gregorian, draw)
    inhouse_weather(env, draw)


def dates(location: str, now: str, gregorian: GregorianDate, draw: ImageDraw.ImageDraw):
    draw.text((798, 46), location, font=font48, fill=0, anchor="rs")
    draw.text((798, 90), now, font=font40, fill=0, anchor="rs")
    gregorian_date = (
        f'{gregorian.lunar_year[:3]}{gregorian.lunar_date}[{gregorian.lunar_year[4:5]}]'
    )
    draw.text((798, 116), gregorian_date, font=font18, fill=0, anchor="rs")


def major_weather(weather, humidity, image, draw: ImageDraw.ImageDraw):
    # 156px leaves the column to the right for a 9-day forecast row.
    # 220px ate that band and capped the forecast at five days.
    icon = Image.open(os.path.join(PIC_DIR, f'{weather.icon[0]}.png'))
    image.paste(icon.resize((156, 156)), (8, 0))

    temp_text = f'{weather.temperature.data[0].value:.0f}'
    draw_celsius(draw, 172, 78, temp_text, font80, font24, font48)
    draw_run(draw, 172, 126, [(f'{humidity.humidity}', font40), ('%', font32)])


def inhouse_weather(env: EnvironmentData, draw: ImageDraw.ImageDraw):
    top_left = (EPD_WIDTH - 372, 4)
    bottom_right = (EPD_WIDTH - 252, 130)

    house_tip = (top_left[0] + (bottom_right[0] - top_left[0]) // 2, 10)
    left_wall = (top_left[0] + 8, top_left[1] + 50)
    left_ground = (left_wall[0], bottom_right[1] - 6)
    right_ground = (bottom_right[0] - 8, bottom_right[1] - 6)
    right_wall = (right_ground[0], left_wall[1])

    draw.polygon(
        ([house_tip, left_wall, left_ground, right_ground, right_wall]),
        255,
        0,
        4,
    )
    draw.line((left_wall, right_wall), 0, 4)
    draw.rectangle(
        (
            (house_tip[0] - 10, house_tip[1] + 20),
            (house_tip[0] + 10, house_tip[1] + 40),
        ),
        255,
        0,
        3,
    )
    draw.line(
        ((house_tip[0], house_tip[1] + 20), (house_tip[0], house_tip[1] + 40)), 0, 2
    )
    draw.line(
        (
            (house_tip[0] - 10, house_tip[1] + 30),
            (house_tip[0] + 10, house_tip[1] + 30),
        ),
        0,
        2,
    )

    chimney_bottom_left = (house_tip[0] + 27, house_tip[1] + 21)
    chimney_top_right = (chimney_bottom_left[0] + 14, chimney_bottom_left[1] - 19)
    draw.line(
        (chimney_bottom_left, (chimney_bottom_left[0], chimney_bottom_left[1] - 19)),
        0,
        3,
    )
    draw.line(
        (
            (
                (chimney_bottom_left[0], chimney_bottom_left[1] - 19),
                chimney_top_right,
            )
        ),
        0,
        3,
    )
    draw.line(
        (
            chimney_top_right,
            (chimney_top_right[0], chimney_bottom_left[1] + 12),
        ),
        0,
        3,
    )
    draw.arc(
        (
            (chimney_top_right[0] - 8, chimney_top_right[1] - 10),
            (chimney_top_right[0] + 28, chimney_top_right[1] - 2),
        ),
        150,
        30,
        0,
        2,
    )
    draw.arc(
        (
            (chimney_top_right[0] + 4, chimney_top_right[1] - 4),
            (chimney_top_right[0] + 20, chimney_top_right[1] + 2),
        ),
        start=150,
        end=30,
        fill=0,
        width=2,
    )

    draw_celsius(
        draw,
        left_wall[0] + 4,
        left_ground[1] - 32,
        f'{env.temperature:.01f}',
        font40,
        font12,
        font14,
    )
    draw_run(
        draw,
        left_ground[0] + 4,
        left_ground[1] - 8,
        [(f'{env.humidity:0.1f}', font24), ('%', font12)],
    )
