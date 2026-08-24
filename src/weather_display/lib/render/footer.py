from datetime import datetime

from PIL import ImageDraw
from weather_display.assest.font.cubic_font import font14


def render_footer_section(draw: ImageDraw.ImageDraw, time_diff: float, now: datetime):
    baseline = 476
    draw.text(
        (8, baseline),
        f"資料更新於 {time_diff:.0f} 分鐘前",
        font=font14,
        fill=0,
        anchor="ls",
    )
    draw.text(
        (798, baseline),
        now.strftime("%Y-%m-%d %H:%M"),
        font=font14,
        fill=0,
        anchor="rs",
    )
