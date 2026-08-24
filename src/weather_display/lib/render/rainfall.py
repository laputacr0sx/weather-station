"""Render the home rainfall-nowcast section as a 1-bit black-and-white panel.

Full-width band under the 5-day forecast, sized to be glanceable from ~4 m:

  1. Verdict (font40) - "is it going to rain in the next 2 hours?"
  2. Time-to-rain (font18)
  3. Four half-hour slots: 24-hour clock (font18), 48px icon, mm (font14)
"""
import os
from datetime import datetime, timedelta

from PIL import Image, ImageDraw

from weather_display import PIC_DIR
from weather_display.assest.font.cubic_font import font14, font18, font40
from weather_display.lib.util.rainfall_nowcast import HomeNowcast, NowcastSlot

SECTION_X = 8
SECTION_Y = 242
SECTION_W = 784
SECTION_H = 150

SLOT_COUNT = 4
SLOT_GAP = 12
SLOT_W = (SECTION_W - SLOT_GAP * (SLOT_COUNT - 1)) // SLOT_COUNT
ICON_SIZE = 48


# Severity thresholds in mm per 30 min. These bracket the official HKO
# classification: <2.5 light, 2.5-10 steady, 10-25 heavy, >=25 torrential.
def _icon_for(per_slot_mm: float) -> str | None:
    """Map a 30-min rainfall amount to an icon filename in PIC_DIR.

    Returns ``None`` for dry slots so the renderer can leave the icon
    cell blank instead of drawing a cloud - the empty cell already
    communicates "no rain in this 30 min".
    """
    if per_slot_mm <= 0:
        return None
    if per_slot_mm < 2.5:
        # Light drizzle: 60.png is "rainy cloud" in the HKO set.
        return "60.png"
    if per_slot_mm < 10.0:
        # Steady rain: 64.png is a heavier "showers" icon.
        return "64.png"
    if per_slot_mm < 25.0:
        # Heavy rain: 65.png denotes heavier showers in the HKO set.
        return "65.png"
    # Torrential: thunderstorm icon.
    return "wi_thunderstorms.png"


def _verdict_text(nowcast: HomeNowcast) -> str:
    """One-line Chinese verdict for the verdict row."""
    if nowcast.is_dry:
        return "未來兩小時無雨"
    peak = nowcast.peak_per_slot_mm
    if peak >= 10.0:
        return "未來兩小時將有大雨"
    return "未來兩小時有雨，請帶傘"


def _minutes_to_first_wet(nowcast: HomeNowcast) -> int | None:
    """Minutes from now until the start of the first wet 30-min slot.

    Each CSV value is rainfall accumulated through ``ended_at``, so the
    slot itself covers the 30 minutes before that. If that start time
    has already passed, returns 0 to convey "rain is happening now".
    """
    first = nowcast.first_wet_slot
    if first is None:
        return None
    now = datetime.now()
    slot_start = first.ended_at - timedelta(minutes=30)
    minutes = int(round((slot_start - now).total_seconds() / 60))
    return max(minutes, 0)


def _slot_label(slot: NowcastSlot) -> str:
    return slot.ended_at.strftime("%H:%M")


def _mm_text(per_slot_mm: float) -> str:
    """Format per-slot mm so a wet slot never displays as ``0mm``."""
    if per_slot_mm <= 0:
        return "0mm"
    return f"{per_slot_mm:g}mm"


def _draw_one_slot(
    draw: ImageDraw.ImageDraw,
    image: Image.Image,
    slot: NowcastSlot,
    x: int,
    y: int,
):
    # Time label centred in the cell
    time_text = _slot_label(slot)
    cx = x + SLOT_W // 2
    draw.text((cx, y + 14), time_text, font=font18, fill=0, anchor="ms")

    # Icon centred below the time label
    icon_name = _icon_for(slot.per_slot_mm)
    if icon_name:
        try:
            icon = Image.open(os.path.join(PIC_DIR, icon_name)).convert("1")
            icon = icon.resize((ICON_SIZE, ICON_SIZE))
            image.paste(icon, (x + (SLOT_W - ICON_SIZE) // 2, y + 20))
        except FileNotFoundError:
            pass  # icon missing - cell just shows the time, no crash

    # Per-slot mm text below the icon
    mm_text = _mm_text(slot.per_slot_mm)
    draw.text(
        (x + SLOT_W // 2, y + 20 + ICON_SIZE + 14),
        mm_text,
        font=font14,
        fill=0,
        anchor="ms",
    )


def _draw_section_frame(draw: ImageDraw.ImageDraw):
    """Light bounding rectangle around the rainfall panel."""
    draw.rectangle(
        (SECTION_X, SECTION_Y, SECTION_X + SECTION_W, SECTION_Y + SECTION_H),
        outline=0,
        width=1,
    )


def _draw_verdict(draw: ImageDraw.ImageDraw, nowcast: HomeNowcast):
    text = _verdict_text(nowcast)
    draw.text(
        (SECTION_X + 8, SECTION_Y + 38), text, font=font40, fill=0, anchor="ls"
    )

    minutes = _minutes_to_first_wet(nowcast)
    if minutes is None:
        sub = "適合外出" if nowcast.is_dry else ""
    elif minutes == 0:
        sub = "正在下雨"
    elif minutes < 60:
        sub = f"約 {minutes} 分鐘後開始"
    else:
        hours = minutes // 60
        sub = f"約 {hours} 小時後開始"
    if sub:
        draw.text(
            (SECTION_X + 8, SECTION_Y + 60),
            sub,
            font=font18,
            fill=0,
            anchor="ls",
        )


def _draw_slots(draw: ImageDraw.ImageDraw, image: Image.Image, nowcast: HomeNowcast):
    slots_y = SECTION_Y + 66
    for i, slot in enumerate(nowcast.slots[:SLOT_COUNT]):
        x = SECTION_X + i * (SLOT_W + SLOT_GAP)
        _draw_one_slot(draw, image, slot, x, slots_y)


def render_rainfall_section(image: Image.Image, nowcast: HomeNowcast | None):
    """Draw the rainfall-nowcast panel onto ``image``.

    If ``nowcast`` is ``None`` (network or parse failure), the section is
    filled with a single "nowcast unavailable" line - blanking the
    section is worse than admitting we don't have data.
    """
    draw = ImageDraw.Draw(image)
    _draw_section_frame(draw)

    if nowcast is None:
        draw.text(
            (SECTION_X + 8, SECTION_Y + 44),
            "未來兩小時雨量預報 暫時無法取得",
            font=font40,
            fill=0,
            anchor="ls",
        )
        return

    _draw_verdict(draw, nowcast)
    _draw_slots(draw, image, nowcast)
