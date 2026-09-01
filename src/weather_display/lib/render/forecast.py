from PIL import Image
from PIL.ImageDraw import ImageDraw
from weather_display import EPD_WIDTH, PIC_DIR
from weather_display.assest.font.cubic_font import font18
from weather_display.lib.util.weather_forecast import WeatherForecastData

# Right of the 156px hero icon; must finish above the warning strip at y=232.
_ORIGIN_X = 172
_ORIGIN_Y = 138
_FORECAST_DAYS = 9
_ICON_SIZE = 40
_WEEKDAY_CHARS = "一二三四五六日"


def _weekday_char(week: str) -> str:
    for char in week:
        if char in _WEEKDAY_CHARS:
            return char
    return week[-1] if week else ""


def render_forecast_section(
    forecast: WeatherForecastData, draw: ImageDraw, image: Image.Image
):
    days = forecast.weather_forecast[:_FORECAST_DAYS]
    n = len(days)
    if n == 0:
        return
    cell_width = (EPD_WIDTH - _ORIGIN_X) // n

    for i, curr_cast in enumerate(days):
        x1 = _ORIGIN_X + i * cell_width
        cx = x1 + cell_width // 2

        draw.text(
            (cx, _ORIGIN_Y + 16),
            _weekday_char(curr_cast.week),
            font=font18,
            fill=0,
            anchor="ms",
        )

        try:
            icon = Image.open(f'{PIC_DIR}/{curr_cast.forecast_icon}.png')
            image.paste(
                icon.resize((_ICON_SIZE, _ICON_SIZE)),
                (cx - _ICON_SIZE // 2, _ORIGIN_Y + 22),
            )
        except FileNotFoundError:
            pass

        hi = f'{curr_cast.forecast_maxtemp.value:.0f}'
        lo = f'{curr_cast.forecast_mintemp.value:.0f}'
        draw.text((cx, _ORIGIN_Y + 72), hi, font=font18, fill=0, anchor="ms")
        draw.text((cx, _ORIGIN_Y + 90), lo, font=font18, fill=0, anchor="ms")
