from PIL import Image
from PIL.ImageDraw import ImageDraw
from weather_display import EPD_WIDTH, PIC_DIR
from weather_display.assest.font.cubic_font import font12, font24
from weather_display.lib.util.weather_forecast import WeatherForecastData


def render_forecast_section(
    forecast: WeatherForecastData, draw: ImageDraw, image: Image.Image
):
    MINIMUM_WIDTH = 74
    FORECAST_SECTION_COORD = (272, 124)
    FORECAST_LENGTH = 5
    maximum_cell_width = (EPD_WIDTH - FORECAST_SECTION_COORD[0]) // FORECAST_LENGTH

    forecast_cell_width = (
        maximum_cell_width if (maximum_cell_width > MINIMUM_WIDTH) else MINIMUM_WIDTH
    )

    for i in range(FORECAST_LENGTH):
        curr_cast = forecast.weather_forecast[i]
        x1 = FORECAST_SECTION_COORD[0] + i * forecast_cell_width
        y1 = FORECAST_SECTION_COORD[1]

        # date_str = curr_cast.forecast_date
        htemp = curr_cast.forecast_maxtemp.value
        ltemp = curr_cast.forecast_mintemp.value

        hhum = curr_cast.forecast_maxrh.value
        lhum = curr_cast.forecast_minrh.value

        weather_icon = Image.open(f"{PIC_DIR}/{curr_cast.forecast_icon}.png")
        icon_size = (48, 48)
        resize_weather_icon = weather_icon.resize(icon_size)

        icon_offset = (22, 28)
        image.paste(resize_weather_icon, (x1 + icon_offset[0], y1 + icon_offset[1]))

        # draw.rectangle(
        #     (
        #         x1 + icon_offset[0],
        #         y1 + icon_offset[1],
        #         x1 + icon_offset[0] + icon_size[0],
        #         y1 + icon_offset[1] + icon_size[1],
        #     ),
        #     outline=0,
        #     width=1,
        # )

        # Draw border of each forecast cell
        # draw.rectangle((x1, y1, x2, y2), outline=0, width=1)

        # Draw weekday text , ie 一， 二，三...
        draw.text((x1 + 44, y1 + 2), f"{curr_cast.week[2]}", font=font24, fill=0)

        # Draw TEMPERATURE text
        draw.text((x1 + 70, y1 + 28), f"{htemp:.0f}", font=font24, fill=0)
        draw.text((x1 + 70, y1 + 54), f"{ltemp:.0f}", font=font24, fill=0)

        # Draw HUMIDITY text
        draw.text((x1 + icon_offset[0], y1 + 78), f"{lhum:.0f}", font=font12, fill=0)
        draw.text(
            (x1 + icon_offset[0] + 30, y1 + 78), f"{hhum:.0f}", font=font12, fill=0
        )
