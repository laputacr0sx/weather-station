import os

from PIL import Image, ImageDraw
from weather_display import PIC_DIR
from weather_display.lib.util.current_weather import CurrentWeather

from ...assest.font.cubic_font import font32, font48, font24, font64

# def render_major_section(
#     image: Image.Image, draw: ImageDraw.ImageDraw, weather: CurrentWeather
# ):


def render_header_section(
    weather: CurrentWeather,
    location: str,
    now: str,
    draw: ImageDraw.ImageDraw,
    image: Image.Image,
):
    # Render weather icon
    icon = Image.open(os.path.join(PIC_DIR, f"{weather.icon[0]}.png"))
    resized_icon = icon.resize((256, 256))
    image.paste(resized_icon, (-10, -20))

    # Render temperature
    draw.text((278, 2), f"{weather.temperature.data[0].value} C", font=font64, fill=0)
    draw.text((358, 2), "o", font=font24, fill=0)
    # Render humidity
    draw.text((278, 72), f"{weather.humidity.data[0].value}%", font=font32, fill=0)

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
