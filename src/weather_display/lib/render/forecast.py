from PIL import Image
from PIL.ImageDraw import ImageDraw
from weather_display import EPD_WIDTH, PIC_DIR
from weather_display.assest.font.cubic_font import font32
from weather_display.lib.util.weather_forecast import WeatherForecastData


def render_forecast_section(
    forecast: WeatherForecastData, draw: ImageDraw, image: Image.Image
):
    origin_x, origin_y = 236, 140
    n = 5
    cell_width = (EPD_WIDTH - origin_x) // n
    icon_size = 56

    for i in range(n):
        curr_cast = forecast.weather_forecast[i]
        x1 = origin_x + i * cell_width
        cx = x1 + cell_width // 2

        draw.text(
            (cx, origin_y + 26),
            f'{curr_cast.week[2]}',
            font=font32,
            fill=0,
            anchor="ms",
        )

        icon = Image.open(f'{PIC_DIR}/{curr_cast.forecast_icon}.png')
        image.paste(icon.resize((icon_size, icon_size)), (x1 + 4, origin_y + 34))

        hi = f'{curr_cast.forecast_maxtemp.value:.0f}'
        lo = f'{curr_cast.forecast_mintemp.value:.0f}'
        draw.text((x1 + 64, origin_y + 58), hi, font=font32, fill=0, anchor="ls")
        draw.text((x1 + 64, origin_y + 90), lo, font=font32, fill=0, anchor="ls")
