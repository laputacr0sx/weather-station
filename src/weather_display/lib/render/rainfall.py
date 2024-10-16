import io
from PIL import Image

from weather_display.lib.util.rainfall import render_rainfall_chart


def render_rainfall_section(image: Image.Image):
    chart_byte = render_rainfall_chart()
    chart = Image.open(io.BytesIO(chart_byte))
    image.paste(chart, (290, 220))
