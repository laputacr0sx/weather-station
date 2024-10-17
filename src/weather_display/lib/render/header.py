import os

from PIL import Image, ImageDraw
from weather_display import PIC_DIR
from weather_display.lib.util.current_weather import CurrentWeather
from weather_display.lib.util.gregorian import GregorianDate
from weather_display.lib.util.humidity import HumidityData

from ...assest.font.cubic_font import font18, font24, font32, font48, font64

# def render_major_section(
#     image: Image.Image, draw: ImageDraw.ImageDraw, weather: CurrentWeather
# ):


def render_header_section(
    gregorian: GregorianDate,
    weather: CurrentWeather,
    humidity: HumidityData,
    location: str,
    now: str,
    draw: ImageDraw.ImageDraw,
    image: Image.Image,
):
    # Render weather icon
    icon = Image.open(os.path.join(PIC_DIR, f"{weather.icon[0]}.png"))
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

    # Render temperature
    draw.text((278, 2), f"{weather.temperature.data[0].value} C", font=font64, fill=0)
    draw.text((358, 2), "o", font=font24, fill=0)
    # Render humidity
    draw.text((278, 72), f"{humidity.humidity}%", font=font32, fill=0)

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
        f"{gregorian.lunar_year[:3]}{gregorian.lunar_date}[{gregorian.lunar_year[4:5]}]"
    )
    greg_date_length = len(gregorian_date)
    greg_x_position = 800 - (
        (greg_date_length - 2) * 18 + 2 * 9 + (greg_date_length - 1) * 2 + 2
    )

    draw.text((greg_x_position, 92), gregorian_date, font=font18, fill=0)
