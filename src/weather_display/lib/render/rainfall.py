"""Render the home rainfall-nowcast section as a 1-bit black-and-white panel.

Full-width band under the 5-day forecast, sized to be glanceable from ~4 m
by elders and children:

  1. Action (font40) left - "bring an umbrella?" / "no rain"
  2. Timing (font18) right - when the first wet slot starts
  3. Five rain gauges: Sha Tin past-hour 現況, a vertical divider, then
     four half-hour nowcast cups (clock, fill, 無/小/中/大/暴)

The cup and the word answer different questions. The word is a class
(should I worry?). The cup is amount (how wet is this half hour?),
filled continuously so 2.5 mm and 10 mm are not the same height.

When the warning strip is on, pass ``COMPACT_RAINFALL`` so this band sits
under the strip and ends on the same baseline as the quiet layout.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from PIL import Image, ImageDraw

from weather_display.assest.font.cubic_font import font14, font18, font24, font32, font40
from weather_display.lib.util.hourly_rainfall import HourlyRainfall
from weather_display.lib.util.rainfall_nowcast import HomeNowcast, NowcastSlot

SECTION_X = 8
SECTION_Y = 242
SECTION_W = 784
SECTION_H = 150

SLOT_COUNT = 4
SLOT_GAP = 12
NOW_CAPTION = "現況"

# Slot values are millimetres in 30 minutes, not mm/h.
#
# Word bands follow the nowcast product's own legend (2.5 mm and 5 mm
# per half hour on the HKO regional portal) plus the Amber rainstorm
# rate expressed in a 30-min slot (30 mm/h => 15 mm). They were not
# fitted to a local nowcast climatology.
#
# Cup fill is independent of those bands: sqrt(mm / 15) so everyday
# 0-10 mm rain uses most of the cup, with a floor so drizzle is visible.
SEVERITY_DRY = 0
SEVERITY_LIGHT = 1
SEVERITY_STEADY = 2
SEVERITY_HEAVY = 3
SEVERITY_TORRENTIAL = 4

_SEVERITY_LABEL = ("無雨", "小雨", "中雨", "大雨", "暴雨")
_WORD_THRESHOLDS = (0.0, 2.5, 5.0, 15.0)
GAUGE_FULL_MM = 15.0
GAUGE_MIN_WET_RATIO = 0.18


@dataclass(frozen=True)
class RainfallLayout:
    x: int = SECTION_X
    y: int = SECTION_Y
    w: int = SECTION_W
    h: int = SECTION_H
    compact: bool = False
    now_col_w: int = 136
    divider_gap: int = 16
    verdict_dy: int = 34
    slots_dy: int = 44
    slot_time_dy: int = 14
    gauge_dy: int = 22
    gauge_w: int = 44
    gauge_h: int = 50
    label_dy: int = 90


QUIET_RAINFALL = RainfallLayout()

# Strip is y=232..282 plus a 6px white gap, so this band starts at 288.
# Keep the quiet bottom edge (392) so the wind/UV row does not move.
COMPACT_RAINFALL = RainfallLayout(
    y=288,
    h=104,
    compact=True,
    now_col_w=112,
    divider_gap=12,
    verdict_dy=24,
    slots_dy=32,
    slot_time_dy=12,
    gauge_dy=16,
    gauge_w=30,
    gauge_h=34,
    label_dy=66,
)


def _severity(per_slot_mm: float) -> int:
    """Map a 30-min rainfall amount to a word class, not a cup height."""
    if per_slot_mm <= _WORD_THRESHOLDS[0]:
        return SEVERITY_DRY
    if per_slot_mm < _WORD_THRESHOLDS[1]:
        return SEVERITY_LIGHT
    if per_slot_mm < _WORD_THRESHOLDS[2]:
        return SEVERITY_STEADY
    if per_slot_mm < _WORD_THRESHOLDS[3]:
        return SEVERITY_HEAVY
    return SEVERITY_TORRENTIAL


def _severity_label(per_slot_mm: float) -> str:
    return _SEVERITY_LABEL[_severity(per_slot_mm)]


def _gauge_fill_ratio(per_slot_mm: float) -> float:
    """Cup fill in 0..1 from the 30-min millimetre amount.

    Square-root so the common 1-10 mm range is spread across the cup
    instead of sitting in the bottom fifth. Full cup is 15 mm / 30 min
    (Amber rainstorm rate). Any wet slot is at least ``GAUGE_MIN_WET_RATIO``
    so drizzle does not disappear into the outline.
    """
    if per_slot_mm <= 0:
        return 0.0
    ratio = (per_slot_mm / GAUGE_FULL_MM) ** 0.5
    return min(1.0, max(GAUGE_MIN_WET_RATIO, ratio))


def _verdict_text(
    nowcast: HomeNowcast | None, observed: HourlyRainfall | None = None
) -> str:
    """One-line Chinese action for the left side of the header row."""
    if nowcast is None:
        if observed is not None and observed.is_wet:
            return "沙田過去一小時有雨"
        return "未來兩小時雨量預報 暫時無法取得"
    if nowcast.is_dry:
        if observed is not None and observed.is_wet:
            return "正在下雨，稍後無雨"
        return "未來兩小時無雨"
    peak = nowcast.peak_per_slot_mm
    if peak >= 15.0:
        return "未來兩小時將有暴雨"
    if peak >= 5.0:
        return "未來兩小時將有大雨"
    return "未來兩小時有雨，請帶傘"


def _when_text(
    nowcast: HomeNowcast | None, observed: HourlyRainfall | None = None
) -> str:
    """Right-side status: observed past hour first, else nowcast timing."""
    if observed is not None and observed.is_wet:
        return "沙田過去1小時有雨"
    if nowcast is None:
        return ""
    minutes = _minutes_to_first_wet(nowcast)
    if minutes is None:
        return "適合外出" if nowcast.is_dry else ""
    if minutes == 0:
        return "這半小時將有雨"
    if minutes < 60:
        return f"約 {minutes} 分鐘後開始"
    hours = minutes // 60
    return f"約 {hours} 小時後開始"


def _minutes_to_first_wet(nowcast: HomeNowcast) -> int | None:
    """Minutes from now until the start of the first wet 30-min slot.

    Each CSV value is rain in the 30 minutes ending at ``ended_at``.
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


def _draw_gauge(
    draw: ImageDraw.ImageDraw,
    cx: int,
    y: int,
    fill_ratio: float,
    layout: RainfallLayout,
):
    """One rain-gauge cup, filled from the bottom by ``fill_ratio`` (0..1)."""
    width = layout.gauge_w
    height = layout.gauge_h
    x0 = cx - width // 2
    x1 = x0 + width - 1
    y0 = y
    y1 = y + height - 1
    draw.rectangle((x0, y0, x1, y1), outline=0, width=1)
    if fill_ratio <= 0:
        return
    inset = 2
    inner_h = height - 2 * inset
    fill_h = max(inset, int(round(inner_h * fill_ratio)))
    fy1 = y1 - inset
    fy0 = fy1 - fill_h + 1
    draw.rectangle((x0 + inset, fy0, x1 - inset, fy1), fill=0)


def _forecast_geometry(layout: RainfallLayout) -> tuple[int, int, int]:
    """Return (forecast_origin_x, forecast_slot_w, divider_x)."""
    forecast_x = layout.x + layout.now_col_w + layout.divider_gap
    forecast_w = layout.w - layout.now_col_w - layout.divider_gap
    slot_w = (forecast_w - SLOT_GAP * (SLOT_COUNT - 1)) // SLOT_COUNT
    divider_x = layout.x + layout.now_col_w + layout.divider_gap // 2
    return forecast_x, slot_w, divider_x


def _draw_cup_column(
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    col_w: int,
    caption: str,
    mm: float | None,
    layout: RainfallLayout,
):
    cx = x + col_w // 2
    time_font = font14 if layout.compact else font18
    label_font = font14 if layout.compact else font24
    draw.text(
        (cx, y + layout.slot_time_dy),
        caption,
        font=time_font,
        fill=0,
        anchor="ms",
    )
    if mm is None:
        _draw_gauge(draw, cx, y + layout.gauge_dy, 0.0, layout)
        word = "無資料"
    else:
        _draw_gauge(draw, cx, y + layout.gauge_dy, _gauge_fill_ratio(mm), layout)
        word = _severity_label(mm)
    draw.text(
        (cx, y + layout.label_dy),
        word,
        font=label_font,
        fill=0,
        anchor="ms",
    )


def _draw_divider(draw: ImageDraw.ImageDraw, layout: RainfallLayout, divider_x: int):
    top = layout.y + layout.slots_dy + 8
    bottom = layout.y + layout.h - 8
    draw.line((divider_x, top, divider_x, bottom), fill=0, width=1)


def _draw_header(
    draw: ImageDraw.ImageDraw,
    nowcast: HomeNowcast | None,
    observed: HourlyRainfall | None,
    layout: RainfallLayout,
):
    """Action on the left, observed/timing on the right, same baseline."""
    verdict_font = font32 if layout.compact else font40
    when_font = font14 if layout.compact else font18
    baseline = layout.y + layout.verdict_dy
    draw.text(
        (layout.x + 8, baseline),
        _verdict_text(nowcast, observed),
        font=verdict_font,
        fill=0,
        anchor="ls",
    )
    when = _when_text(nowcast, observed)
    if when:
        draw.text(
            (layout.x + layout.w - 8, baseline),
            when,
            font=when_font,
            fill=0,
            anchor="rs",
        )


def _draw_slots(
    draw: ImageDraw.ImageDraw,
    nowcast: HomeNowcast | None,
    observed: HourlyRainfall | None,
    layout: RainfallLayout,
):
    slots_y = layout.y + layout.slots_dy
    forecast_x, slot_w, divider_x = _forecast_geometry(layout)

    _draw_cup_column(
        draw,
        x=layout.x,
        y=slots_y,
        col_w=layout.now_col_w,
        caption=NOW_CAPTION,
        mm=None if observed is None else observed.mm,
        layout=layout,
    )
    _draw_divider(draw, layout, divider_x)

    if nowcast is None:
        return
    for i, slot in enumerate(nowcast.slots[:SLOT_COUNT]):
        x = forecast_x + i * (slot_w + SLOT_GAP)
        _draw_cup_column(
            draw,
            x=x,
            y=slots_y,
            col_w=slot_w,
            caption=_slot_label(slot),
            mm=slot.per_slot_mm,
            layout=layout,
        )


def render_rainfall_section(
    image: Image.Image,
    nowcast: HomeNowcast | None,
    layout: RainfallLayout | None = None,
    observed: HourlyRainfall | None = None,
):
    """Draw observed past-hour rain plus the 2-hour nowcast onto ``image``.

    The 現況 cup is drawn even when the nowcast fetch failed. A full-width
    error line is used only when both sources are missing.
    """
    layout = layout or QUIET_RAINFALL
    draw = ImageDraw.Draw(image)

    if nowcast is None and (observed is None or not observed.available):
        draw.text(
            (layout.x + 8, layout.y + (28 if layout.compact else 44)),
            "雨量資料 暫時無法取得",
            font=font32 if layout.compact else font40,
            fill=0,
            anchor="ls",
        )
        return

    _draw_header(draw, nowcast, observed, layout)
    _draw_slots(draw, nowcast, observed, layout)
    if nowcast is None:
        forecast_x, _, _ = _forecast_geometry(layout)
        draw.text(
            (forecast_x + 8, layout.y + layout.slots_dy + layout.gauge_dy + 16),
            "兩小時預報無法取得",
            font=font14 if layout.compact else font18,
            fill=0,
            anchor="ls",
        )
