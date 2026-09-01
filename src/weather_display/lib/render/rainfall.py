"""Render the home rainfall-nowcast section as a 1-bit black-and-white panel.

Full-width band under the 5-day forecast, sized to be glanceable from ~4 m
by elders and children:

  1. Action (font40) left - "bring an umbrella?" / "no rain"
  2. Timing (font18) right - when the first wet slot starts
  3. Four half-hour rain gauges: 24-hour clock, cup fill, 無/小/中/大/暴

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
from weather_display.lib.util.rainfall_nowcast import HomeNowcast, NowcastSlot

SECTION_X = 8
SECTION_Y = 242
SECTION_W = 784
SECTION_H = 150

SLOT_COUNT = 4
SLOT_GAP = 16
SLOT_W = (SECTION_W - SLOT_GAP * (SLOT_COUNT - 1)) // SLOT_COUNT

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
    verdict_dy: int = 34
    slots_dy: int = 44
    slot_time_dy: int = 14
    gauge_dy: int = 22
    gauge_w: int = 48
    gauge_h: int = 50
    label_dy: int = 90


QUIET_RAINFALL = RainfallLayout()

# Strip is y=232..282 plus a 6px white gap, so this band starts at 288.
# Keep the quiet bottom edge (392) so the wind/UV row does not move.
COMPACT_RAINFALL = RainfallLayout(
    y=288,
    h=104,
    compact=True,
    verdict_dy=24,
    slots_dy=32,
    slot_time_dy=12,
    gauge_dy=16,
    gauge_w=32,
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


def _verdict_text(nowcast: HomeNowcast) -> str:
    """One-line Chinese action for the left side of the header row."""
    if nowcast.is_dry:
        return "未來兩小時無雨"
    peak = nowcast.peak_per_slot_mm
    if peak >= 15.0:
        return "未來兩小時將有暴雨"
    if peak >= 5.0:
        return "未來兩小時將有大雨"
    return "未來兩小時有雨，請帶傘"


def _when_text(nowcast: HomeNowcast) -> str:
    """Right-side timing: when the first wet slot starts, or a dry cue."""
    minutes = _minutes_to_first_wet(nowcast)
    if minutes is None:
        return "適合外出" if nowcast.is_dry else ""
    if minutes == 0:
        return "正在下雨"
    if minutes < 60:
        return f"約 {minutes} 分鐘後開始"
    hours = minutes // 60
    return f"約 {hours} 小時後開始"


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


def _draw_one_slot(
    draw: ImageDraw.ImageDraw,
    slot: NowcastSlot,
    x: int,
    y: int,
    layout: RainfallLayout,
):
    cx = x + SLOT_W // 2
    time_font = font14 if layout.compact else font18
    label_font = font14 if layout.compact else font24
    draw.text(
        (cx, y + layout.slot_time_dy),
        _slot_label(slot),
        font=time_font,
        fill=0,
        anchor="ms",
    )

    level = _severity(slot.per_slot_mm)
    _draw_gauge(draw, cx, y + layout.gauge_dy, _gauge_fill_ratio(slot.per_slot_mm), layout)

    draw.text(
        (cx, y + layout.label_dy),
        _SEVERITY_LABEL[level],
        font=label_font,
        fill=0,
        anchor="ms",
    )


def _draw_header(draw: ImageDraw.ImageDraw, nowcast: HomeNowcast, layout: RainfallLayout):
    """Action on the left, timing on the right, same baseline."""
    verdict_font = font32 if layout.compact else font40
    when_font = font14 if layout.compact else font18
    baseline = layout.y + layout.verdict_dy
    draw.text(
        (layout.x + 8, baseline),
        _verdict_text(nowcast),
        font=verdict_font,
        fill=0,
        anchor="ls",
    )
    when = _when_text(nowcast)
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
    nowcast: HomeNowcast,
    layout: RainfallLayout,
):
    slots_y = layout.y + layout.slots_dy
    for i, slot in enumerate(nowcast.slots[:SLOT_COUNT]):
        x = layout.x + i * (SLOT_W + SLOT_GAP)
        _draw_one_slot(draw, slot, x, slots_y, layout)


def render_rainfall_section(
    image: Image.Image,
    nowcast: HomeNowcast | None,
    layout: RainfallLayout | None = None,
):
    """Draw the rainfall-nowcast panel onto ``image``.

    If ``nowcast`` is ``None`` (network or parse failure), the section is
    filled with a single "nowcast unavailable" line - blanking the
    section is worse than admitting we don't have data.
    """
    layout = layout or QUIET_RAINFALL
    draw = ImageDraw.Draw(image)

    if nowcast is None:
        draw.text(
            (layout.x + 8, layout.y + (28 if layout.compact else 44)),
            "未來兩小時雨量預報 暫時無法取得",
            font=font32 if layout.compact else font40,
            fill=0,
            anchor="ls",
        )
        return

    _draw_header(draw, nowcast, layout)
    _draw_slots(draw, nowcast, layout)
