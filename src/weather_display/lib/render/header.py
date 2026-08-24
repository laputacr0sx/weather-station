import os

from PIL import Image, ImageDraw
from weather_display import EPD_WIDTH, PIC_DIR
from weather_display.assest.font.cubic_font import (
    font12,
    font18,
    font24,
    font32,
    font40,
    font48,
    font64,
)
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
    location_length = len(location)
    current_date_length = len(now)

    number_of_digits = sum(c.isdigit() for c in now) + 2
    number_of_chinese_char = current_date_length - number_of_digits

    location_x_position = 800 - (location_length * 48 + (location_length - 1) * 4 + 2)
    date_x_position = 800 - (
        number_of_chinese_char * 32
        + number_of_digits * 16
        + (current_date_length - 1) * 2
        + 2
    )

    draw.text((location_x_position, 2), location, font=font48, fill=0)
    draw.text((date_x_position, 54), now, font=font32, fill=0)

    gregorian_date = (
        f'{gregorian.lunar_year[:3]}{gregorian.lunar_date}[{gregorian.lunar_year[4:5]}]'
    )
    greg_date_length = len(gregorian_date)
    greg_x_position = 800 - (
        (greg_date_length - 2) * 18 + 2 * 9 + (greg_date_length - 1) * 2 + 2
    )

    draw.text((greg_x_position, 92), gregorian_date, font=font18, fill=0)


def major_weather(weather, humidity, image, draw: ImageDraw.ImageDraw):
    # Render weather icon
    icon = Image.open(os.path.join(PIC_DIR, f'{weather.icon[0]}.png'))
    icon_pos = (20, 0)
    icon_size = (220, 220)
    resized_icon = icon.resize(icon_size)
    # draw.rectangle(
    #     (
    #         icon_pos[0] - 1,
    #         icon_pos[1] - 1,
    #         1 + icon_pos[0] + icon_size[0],
    #         1 + icon_pos[1] + icon_size[1],
    #     ),
    #     fill=0,
    # )
    image.paste(resized_icon, icon_pos)
    temp_text = f'{weather.temperature.data[0].value:.0f}'
    temperature_boundingbox = draw.textbbox((278, 2), temp_text, font=font64)
    humidity_bb = draw.textbbox(
        (278, 68),
        f'{humidity.humidity}',
        font=font48,
        anchor=None,
        spacing=4,
        align='left',
        direction=None,
        features=None,
        language=None,
        stroke_width=0,
        embedded_color=False,
        font_size=None,
    )

    # Render temperature
    draw.text((278, 2), temp_text, font=font64, fill=0)
    draw.text((temperature_boundingbox[2] + 2, 14), 'o', font=font18, fill=0)
    draw.text((temperature_boundingbox[2] + 10, 17), 'C', font=font48, fill=0)
    # Render humidity
    draw.text((278, 68), f'{humidity.humidity}', font=font48, fill=0)
    draw.text((humidity_bb[2], 82), '%', font=font32, fill=0)


def inhouse_weather(env: EnvironmentData, draw: ImageDraw.ImageDraw):
    top_left = (EPD_WIDTH - 388, 4)
    bottom_right = (EPD_WIDTH - 260, 130)
    # draw.rectangle(
    #     (top_left, bottom_right),
    #     255,
    #     0,
    #     2,
    # )

    house_tip = (top_left[0] + (bottom_right[0] - top_left[0]) // 2, 10)
    left_wall = (top_left[0] + 8, top_left[1] + 50)
    left_ground = (left_wall[0], bottom_right[1] - 6)
    right_ground = (bottom_right[0] - 8, bottom_right[1] - 6)
    right_wall = (right_ground[0], left_wall[1])

    # Drawing house
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

    # Drawing chimney
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
    # draw.arc([55, -10, 85, 10], start=30, end=150, fill=0, width=2)
    # draw.arc([50, -20, 90, 0], start=30, end=150, fill=0, width=2)

    # Drawing Temperature & Humidity Text
    degree_pos = (left_wall[0] + 2, left_ground[1] - 70)
    draw.text(degree_pos, f'{env.temperature:.01f}', font=font40, fill=0)
    draw.text((degree_pos[0] + 84, degree_pos[1] + 14), 'o', font=font12, fill=0)
    draw.text((degree_pos[0] + 90, degree_pos[1] + 15), 'C', font=font24, fill=0)

    humidity_pos = (left_ground[0] + 4, left_ground[1] - 26)
    inhouse_humidity_bb = draw.textbbox(
        humidity_pos,
        f'{env.humidity:0.1f}',
        font=font24,
        anchor=None,
        spacing=4,
        align='left',
        direction=None,
        features=None,
        language=None,
        stroke_width=0,
        embedded_color=False,
        font_size=None,
    )

    draw.text(humidity_pos, f'{env.humidity:0.1f}', font=font24, fill=0)
    draw.text((inhouse_humidity_bb[2], humidity_pos[1] + 11), '%', font=font12, fill=0)
