import os

from PIL import Image, ImageDraw
from weather_display import PIC_DIR
from weather_display.assest.font.cubic_font import font12, font14, font32
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
    valid_data = [
        [
            {
                'icon_uri': '80.png',
                'name': f'{wind.station}風速',
                'data': f'{wind.avg_wind_speed}',
                'unit': f'{wind.wind_direction}',
            },
            {
                'icon_uri': 'sunrise.png',
                'name': '日出時間',
                'data': sun.rise,
                'unit': None,
            },
        ],
        [
            {
                'icon_uri': 'uv.png',
                'name': '紫外線指數',
                # "data": weather.uvindex.data[0].value,
                'data': uv.uv_index,
                'unit': f"@{uv.datetime.strftime("%H:%M")}",
            },
            {
                'icon_uri': 'sunset.png',
                'name': '日落時間',
                'data': sun.set,
                'unit': None,
            },
        ],
    ]

    ROW = 2
    COL = 2
    top_left_x = 2
    top_left_y = 358
    cell_width = 150
    cell_height = 64

    for i in range(ROW):
        for j in range(COL):
            x1 = top_left_x + i * cell_width
            y1 = top_left_y + j * cell_height

            cell = valid_data[i][j]
            name = cell['name']
            data = cell['data']
            img = cell['icon_uri'] or 'na.png'
            unit = cell['unit'] or ''

            data_length = len(data) if type(data) is str else len(str(abs(data)))

            draw.text((x1 + 48, y1), f'{name}', font=font12, fill=0)
            draw.text((x1 + 48, y1 + 16), f'{data}', font=font32, fill=0)
            draw.text(
                (x1 + 48 + data_length * 14 + 4, y1 + cell_height - 30),
                unit,
                font=font14,
                fill=0,
            )

            icon = Image.open(os.path.join(PIC_DIR, img))
            resized_icon = icon.resize((48, 48))
            image.paste(resized_icon, (x1, y1))
