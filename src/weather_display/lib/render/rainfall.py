import io

from PIL import Image
from weather_display.lib.util.rainfall import render_rainfall_chart
from weather_display.lib.temperature_forecast.app import get_temperature_plot


def render_rainfall_section(image: Image.Image):
    rainfall_bytes = render_rainfall_chart()

    if rainfall_bytes is None:
        temperature_bytes = get_temperature_plot()
        chart = Image.open(io.BytesIO(temperature_bytes))
    else:
        chart = Image.open(io.BytesIO(rainfall_bytes))
    # resized_chart = chart.resize((500, 240), Image.Resampling.LANCZOS)
    image.paste(chart, (290, 220))
