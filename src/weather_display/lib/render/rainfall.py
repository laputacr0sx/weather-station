"""Render the home rainfall-nowcast section as a 1-bit black-and-white panel.

Layout, top-down, in the (290, 220) -> (790, 350) region of the dashboard:

  1. Verdict line (font24, bold by virtue of size) - the answer
     "is it going to rain in the next 2 hours?"
  2. Time-to-rain line (font14) - "approximately N minutes from now",
     only when rain is forecast and the first slot is still in the future.
  3. Four half-hour slots, each with:
       - the slot's end time in 24-hour clock (font14)
       - an intensity icon (36x36) chosen from the existing picture set
       - the per-slot mm value in plain text (font12)

The section always renders, even for an all-zero forecast - the user wants
to know "no rain" too, not a blank space.
"""
import os
from datetime import datetime, timedelta

from PIL import Image, ImageDraw

from weather_display import PIC_DIR
from weather_display.assest.font.cubic_font import font12, font14, font18
from weather_display.lib.util.rainfall_nowcast import HomeNowcast, NowcastSlot

# Section geometry. Aligned with the previous chart paste at (290, 220);
# now hard-stopped at y=350 so it does not collide with render_minor_dashboard
# (which starts at y=358).
SECTION_X = 290
SECTION_Y = 220
SECTION_W = 510
SECTION_H = 130

# Per-slot layout
SLOT_COUNT = 4
SLOT_GAP = 8
SLOT_W = (SECTION_W - SLOT_GAP * (SLOT_COUNT - 1)) // SLOT_COUNT
ICON_SIZE = 36


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
    bbox = draw.textbbox((0, 0), time_text, font=font14)
    text_w = bbox[2] - bbox[0]
    draw.text((x + (SLOT_W - text_w) // 2, y), time_text, font=font14, fill=0)

    # Icon centred below the time label
    icon_name = _icon_for(slot.per_slot_mm)
    if icon_name:
        try:
            icon = Image.open(os.path.join(PIC_DIR, icon_name)).convert("1")
            icon = icon.resize((ICON_SIZE, ICON_SIZE))
            image.paste(icon, (x + (SLOT_W - ICON_SIZE) // 2, y + 22))
        except FileNotFoundError:
            pass  # icon missing - cell just shows the time, no crash

    # Per-slot mm text below the icon
    mm_text = _mm_text(slot.per_slot_mm)
    bbox = draw.textbbox((0, 0), mm_text, font=font12)
    text_w = bbox[2] - bbox[0]
    draw.text(
        (x + (SLOT_W - text_w) // 2, y + 22 + ICON_SIZE + 4),
        mm_text,
        font=font12,
        fill=0,
    )


def _draw_section_frame(draw: ImageDraw.ImageDraw):
    """Light bounding rectangle around the rainfall panel."""
    draw.rectangle(
        (SECTION_X, SECTION_Y, SECTION_X + SECTION_W, SECTION_Y + SECTION_H),
        outline=0,
        width=1,
    )


def _draw_verdict(draw: ImageDraw.ImageDraw, nowcast: HomeNowcast):
    # font18 keeps the verdict on a single line within the 510 px section
    # while still being larger than the supporting time-to-rain text.
    text = _verdict_text(nowcast)
    draw.text((SECTION_X + 6, SECTION_Y + 4), text, font=font18, fill=0)

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
            (SECTION_X + 6, SECTION_Y + 36),
            sub,
            font=font14,
            fill=0,
        )


def _draw_slots(draw: ImageDraw.ImageDraw, image: Image.Image, nowcast: HomeNowcast):
    slots_y = SECTION_Y + 68
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
            (SECTION_X + 6, SECTION_Y + 4),
            "未來兩小時雨量預報: 暫時無法取得",
            font=font18,
            fill=0,
        )
        return

    _draw_verdict(draw, nowcast)
    _draw_slots(draw, image, nowcast)
