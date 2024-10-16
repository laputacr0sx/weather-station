from datetime import datetime

from PIL import ImageDraw

from weather_display.assest.font.cubic_font import font12


def render_footer_section(draw: ImageDraw.ImageDraw, time_diff: float, now: datetime):
    draw.text((390, 464), f"資料更新於: {time_diff:.0f} 分鐘前", font=font12, fill=0)
    draw.text(
        (620, 464), f"渲染於:{now.strftime("%Y-%m-%d %H:%M:%S")}", font=font12, fill=0
    )
