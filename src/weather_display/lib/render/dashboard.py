import os

from PIL import Image, ImageDraw
from weather_display import EPD_WIDTH, PIC_DIR
from weather_display.assest.font.cubic_font import font14, font18, font40
from weather_display.lib.render.text import draw_run
from weather_display.lib.util.sun import SunStatus
from weather_display.lib.util.uv_index import UVIndex
from weather_display.lib.util.wind import WindData


def render_minor_dashboard(
    wind: WindData,
    uv: UVIndex,
    sun: SunStatus,
    draw: ImageDraw.ImageDraw,
    image: Image.Image,
):
    cells = [
        {
            'icon_uri': '80.png',
            'name': f'{wind.station}風速',
            'data': f'{wind.avg_wind_speed}',
            'unit': f'{wind.wind_direction}',
        },
        {
            'icon_uri': 'uv.png',
            'name': '紫外線',
            'data': f'{uv.uv_index}',
            'unit': f"@{uv.datetime.strftime('%H:%M')}",
        },
        {
            'icon_uri': 'sunrise.png',
            'name': '日出',
            'data': sun.rise,
            'unit': None,
        },
        {
            'icon_uri': 'sunset.png',
            'name': '日落',
            'data': sun.set,
            'unit': None,
        },
    ]

    top_y = 400
    cell_width = EPD_WIDTH // 4
    icon_size = 48
    name_baseline = top_y + 14
    data_baseline = top_y + 52

    for i, cell in enumerate(cells):
        x1 = i * cell_width
        icon = Image.open(os.path.join(PIC_DIR, cell['icon_uri'] or 'na.png'))
        image.paste(icon.resize((icon_size, icon_size)), (x1 + 4, top_y + 6))

        draw.text((x1 + 56, name_baseline), cell['name'], font=font14, fill=0, anchor="ls")
        x = draw_run(draw, x1 + 56, data_baseline, [(cell['data'], font40)])
        if cell['unit']:
            draw_run(draw, x + 4, data_baseline, [(cell['unit'], font18)])
