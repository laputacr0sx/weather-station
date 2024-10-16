from PIL import Image
from PIL.ImageDraw import ImageDraw
from weather_display import PIC_DIR
from weather_display.assest.font.cubic_font import font12, font24
from weather_display.lib.util.weather_forecast import WeatherForecastData


def render_forecast_section(
    forecast: WeatherForecastData, draw: ImageDraw, image: Image.Image
):
    for i in range(5):
        curr_cast = forecast.weather_forecast[i]
        x1 = 260 + i * 110
        y1 = 124
        # x2 = x1 + 110
        # y2 = 220

        # date_str = curr_cast.forecast_date
        htemp = curr_cast.forecast_maxtemp.value
        ltemp = curr_cast.forecast_mintemp.value

        hhum = curr_cast.forecast_maxrh.value
        lhum = curr_cast.forecast_minrh.value

        bmp = Image.open(f"{PIC_DIR}/{curr_cast.forecast_icon}.png")
        resize_bmp = bmp.resize((72, 72))
        image.paste(resize_bmp, (x1 + 4, y1 + 20))

        # Draw border of each forecast cell
        # draw.rectangle((x1, y1, x2, y2), outline=0, width=1)

        # Draw weekday text , ie 一， 二，三...
        draw.text((x1 + 44, y1 + 2), f"{curr_cast.week[2]}", font=font24, fill=0)

        # Draw TEMPERATURE text
        draw.text((x1 + 70, y1 + 28), f"{htemp:.0f}", font=font24, fill=0)
        draw.text((x1 + 70, y1 + 54), f"{ltemp:.0f}", font=font24, fill=0)

        # Draw TEMPERATURE text
        draw.text((x1 + 20, y1 + 78), f"{lhum:.0f}", font=font12, fill=0)
        draw.text((x1 + 48, y1 + 78), f"{hhum:.0f}", font=font12, fill=0)
