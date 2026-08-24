from PIL import Image, ImageDraw

from weather_display.assest.font.cubic_font import font24, font40
from weather_display.lib.render.text import draw_celsius, draw_run


def _draw():
    image = Image.new("1", (240, 80), 255)
    return image, ImageDraw.Draw(image)


def test_draw_run_places_unit_after_number_on_same_line():
    _, draw = _draw()
    baseline = 50
    draw_run(draw, 10, baseline, [("12", font40), ("mm", font24)])
    num = draw.textbbox((10, baseline), "12", font=font40, anchor="ls")
    unit = draw.textbbox((num[2], baseline), "mm", font=font24, anchor="ls")
    assert unit[0] == num[2]
    assert abs(num[3] - baseline) <= 4
    assert abs(unit[3] - baseline) <= 4


def test_draw_celsius_puts_c_on_number_baseline():
    _, draw = _draw()
    baseline = 50
    draw_celsius(draw, 10, baseline, "28", font40, font24, font24)
    num = draw.textbbox((10, baseline), "28", font=font40, anchor="ls")
    c_x = num[2] + max(4, font24.size // 2)
    c = draw.textbbox((c_x, baseline), "C", font=font24, anchor="ls")
    assert c[0] == c_x
    assert abs(num[3] - c[3]) <= 2
