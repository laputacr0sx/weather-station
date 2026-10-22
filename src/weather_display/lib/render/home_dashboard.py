"""Two home pages for the Waveshare 7.3-inch Spectra 6 panel.

The glass is 800×480. Children and older people read it, so every word is
Chinese and each page keeps its type large. The Pi shows one page per
refresh. Both pages show the home grid cell of the official two-hour
rainfall nowcast. The forecast page also shows the five-day outlook, wind,
UV, and sunrise. An Observatory warning is drawn only while one is in force.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta

from PIL import Image, ImageDraw

from weather_display import PIC_DIR
from weather_display.assest.font.cubic_font import (
    font14,
    font18,
    font24,
    font32,
    font40,
    font48,
    font64,
)
from weather_display.lib.render.palette import (
    BLACK,
    BLUE,
    EPD_HEIGHT,
    EPD_WIDTH,
    RED,
    WHITE,
    YELLOW,
    snap,
    temp_color,
)
from weather_display.lib.render.rainfall import _icon_for
from weather_display.lib.render.text import draw_celsius, draw_run
from weather_display.lib.util.convert_date_string import get_now_str
from weather_display.lib.util.home_assistant import RoomClimate
from weather_display.lib.util.rainfall_nowcast import HomeNowcast
from weather_display.lib.util.warnings import WeatherWarning

CARD_ORIGIN = (8, 112)
CARD_SIZE = (256, 120)
CARD_GAP = 8
ROOM_NOWCAST_TOP = 368
FORECAST_TOP = 100
FORECAST_BOTTOM = 270
NOWCAST_TOP = 276
_HEAVY_MM = 10.0
_UMBRELLA_MM = 0.5
_WEEKDAYS = "一二三四五六日"


def render_now_page(
    rooms: list[RoomClimate],
    *,
    outdoor_c: float | None,
    outdoor_humidity: str | None,
    icon_id: int | None,
    location: str,
    when: datetime,
    lunar: str | None = None,
    nowcast: HomeNowcast | None = None,
    warnings: list[WeatherWarning] | None = None,
) -> Image.Image:
    image = Image.new("RGB", (EPD_WIDTH, EPD_HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)
    _now_header(
        draw,
        image,
        outdoor_c=outdoor_c,
        outdoor_humidity=outdoor_humidity,
        icon_id=icon_id,
        location=location,
        when=when,
        lunar=lunar,
    )
    _rooms(draw, rooms)
    _paint_nowcast(
        draw,
        image,
        top=ROOM_NOWCAST_TOP,
        bottom=EPD_HEIGHT,
        nowcast=nowcast,
        when=when,
        warnings=warnings,
        detailed=False,
    )
    return snap(image)


def render_forecast_page(
    *,
    outdoor_c: float | None,
    outdoor_humidity: str | None,
    icon_id: int | None,
    location: str,
    when: datetime,
    lunar: str | None = None,
    forecast: list | None = None,
    nowcast: HomeNowcast | None = None,
    warnings: list[WeatherWarning] | None = None,
    wind_text: str = "",
    uv_text: str = "",
    sun_rise: str | None = None,
    sun_set: str | None = None,
) -> Image.Image:
    image = Image.new("RGB", (EPD_WIDTH, EPD_HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)
    _forecast_header(
        draw,
        outdoor_c=outdoor_c,
        outdoor_humidity=outdoor_humidity,
        location=location,
        when=when,
        wind_text=wind_text,
        uv_text=uv_text,
        sun_rise=sun_rise,
        sun_set=sun_set,
    )
    del icon_id, lunar
    _forecast_days(draw, image, forecast or [])
    _paint_nowcast(
        draw,
        image,
        top=NOWCAST_TOP,
        bottom=EPD_HEIGHT,
        nowcast=nowcast,
        when=when,
        warnings=warnings,
        detailed=True,
    )
    return snap(image)


def _now_header(draw, image, *, outdoor_c, outdoor_humidity, icon_id, location, when, lunar):
    _paste_icon(image, icon_id, (10, 8), 86)
    draw.text((108, 20), "室外", font=font14, fill=BLACK, anchor="ls")
    end = _outdoor_temp(draw, 108, 78, outdoor_c, font64, font18, font32)
    humidity = _humidity_text(outdoor_humidity)
    if humidity:
        draw_run(draw, end + 14, 78, [(humidity, font32), ("%", font24)], fill=BLUE)
    _header_clock(draw, location, when, lunar)
    draw.rectangle((0, 98, EPD_WIDTH, 104), fill=BLUE)


def _forecast_header(
    draw,
    *,
    outdoor_c,
    outdoor_humidity,
    location,
    when,
    wind_text,
    uv_text,
    sun_rise,
    sun_set,
):
    draw.text((16, 36), "預報", font=font32, fill=BLACK, anchor="ls")
    end = _outdoor_temp(draw, 110, 40, outdoor_c, font40, font14, font18)
    humidity = _humidity_text(outdoor_humidity)
    if humidity:
        draw_run(draw, end + 12, 40, [(humidity, font24), ("%", font18)], fill=BLUE)
    draw.text((790, 22), location, font=font24, fill=BLACK, anchor="rs")
    draw.text(
        (790, 46),
        f"{get_now_str(when)} {when.strftime('%H:%M')}",
        font=font18,
        fill=BLACK,
        anchor="rs",
    )
    conditions = _conditions_text(wind_text, uv_text, sun_rise, sun_set)
    if conditions:
        draw.text((16, 74), conditions, font=font18, fill=BLACK, anchor="ls")
    draw.rectangle((0, 86, EPD_WIDTH, 92), fill=BLUE)


def _outdoor_temp(draw, x, baseline, outdoor_c, number_font, o_font, c_font) -> int:
    color = temp_color(outdoor_c)
    number = "--" if outdoor_c is None else f"{outdoor_c:.0f}"
    return draw_celsius(draw, x, baseline, number, number_font, o_font, c_font, fill=color)


def _header_clock(draw, location, when, lunar):
    draw.text((790, 28), location, font=font32, fill=BLACK, anchor="rs")
    draw.text(
        (790, 58),
        f"{get_now_str(when)} {when.strftime('%H:%M')}",
        font=font18,
        fill=BLACK,
        anchor="rs",
    )
    if lunar:
        draw.text((790, 84), lunar, font=font14, fill=BLACK, anchor="rs")


def _forecast_days(draw, image, days: list):
    if not days:
        draw.text((16, FORECAST_TOP + 70), "預報暫時無法取得", font=font40, fill=BLACK, anchor="ls")
        return
    cell = EPD_WIDTH // 5
    for index, day in enumerate(days[:5]):
        x = index * cell
        label = "今日" if index == 0 else _weekday(day)
        if label:
            draw.text((x + cell // 2, FORECAST_TOP + 26), label, font=font32, fill=BLACK, anchor="ms")
        _paste_icon(image, getattr(day, "forecast_icon", None), (x + 8, FORECAST_TOP + 34), 72)
        hi = _depth(day, "forecast_maxtemp")
        lo = _depth(day, "forecast_mintemp")
        if hi is not None:
            draw_celsius(
                draw, x + 88, FORECAST_TOP + 70, f"{hi:.0f}", font40, font14, font24, fill=RED
            )
        if lo is not None:
            draw_celsius(
                draw, x + 88, FORECAST_TOP + 116, f"{lo:.0f}", font32, font14, font18, fill=BLUE
            )


def _paint_nowcast(draw, image, *, top, bottom, nowcast, when, warnings, detailed: bool):
    shown = list(warnings or [])[:2]
    tone = _alert_tone(nowcast, when, shown)
    _fill, ink = _tone_colors(tone)
    _fill_alert_band(draw, top, bottom, tone, _fill)
    if shown:
        _warning_names(draw, top, shown, _warning_ink(tone, shown), detailed)
    status = _unavailable_text(nowcast, when)
    if status:
        _status_line(draw, top, bottom, status, ink, detailed, has_warning=bool(shown))
        return
    _verdict_line(draw, top, nowcast, when, ink, detailed, has_warning=bool(shown))
    _slot_row(
        draw,
        image,
        list(nowcast.slots[:4]),
        top=top,
        ink=ink,
        detailed=detailed,
        has_warning=bool(shown),
    )


def _fill_alert_band(draw, top, bottom, tone, fill):
    if tone == "white":
        draw.rectangle((8, top + 4, EPD_WIDTH - 8, bottom - 8), outline=BLACK, width=2)
        return
    draw.rectangle((0, top, EPD_WIDTH, bottom), fill=fill)


def _warning_names(draw, top, warnings, fill, detailed: bool):
    font = font24 if detailed else font18
    names = "  ".join(warning.name for warning in warnings)
    draw.text((16, top + 28), names, font=font, fill=fill, anchor="ls")


def _status_line(draw, top, bottom, status, ink, detailed: bool, has_warning: bool):
    font = font32 if has_warning or not detailed else font40
    if has_warning:
        baseline = top + (64 if detailed else 58)
    else:
        baseline = top + (bottom - top) // 2 + 10
    draw.text((16, baseline), status, font=font, fill=ink, anchor="ls")


def _verdict_line(draw, top, nowcast, when, ink, detailed: bool, has_warning: bool):
    verdict, level = _family_verdict(nowcast)
    fill = WHITE if ink == WHITE else (RED if level == "heavy" else ink)
    font, baseline = _verdict_style(top, detailed, has_warning)
    draw.text((16, baseline), verdict, font=font, fill=fill, anchor="ls")
    if not detailed:
        return
    subtitle = _timing_text(nowcast, when)
    if not subtitle or (has_warning and subtitle == "適合外出"):
        return
    used = draw.textlength(verdict, font=font)
    draw.text((16 + used + 16, baseline), subtitle, font=font24, fill=ink, anchor="ls")


def _verdict_style(top: int, detailed: bool, has_warning: bool):
    if has_warning:
        return (font32, top + 64) if detailed else (font32, top + 56)
    if detailed:
        return font40, top + 52
    return font40, top + 44


def _slot_row(draw, image, slots, *, top, ink, detailed: bool, has_warning: bool):
    if not slots:
        return
    slot_w = EPD_WIDTH // len(slots)
    for index, slot in enumerate(slots):
        cx = index * slot_w + slot_w // 2
        amount_fill = _amount_fill(slot.per_slot_mm, ink)
        if detailed:
            _detailed_slot(draw, image, slot, cx, top, ink, amount_fill, has_warning)
        else:
            _compact_slot(draw, slot, cx, top, ink, amount_fill, has_warning)


def _detailed_slot(draw, image, slot, cx, top, ink, amount_fill, has_warning: bool):
    time_y = top + (100 if has_warning else 112)
    draw.text((cx, time_y), slot.ended_at.strftime("%H:%M"), font=font24, fill=ink, anchor="ms")
    if ink != WHITE:
        icon_name = _icon_for(slot.per_slot_mm)
        if icon_name:
            size = 48 if has_warning else 56
            _paste_file(image, icon_name, (cx - size // 2, time_y + 6), size, fallback=False)
    draw.text((cx, time_y + 74), _amount_text(slot.per_slot_mm), font=font24, fill=amount_fill, anchor="ms")


def _compact_slot(draw, slot, cx, top, ink, amount_fill, has_warning: bool):
    time_y = top + (82 if has_warning else 76)
    amount_y = top + (104 if has_warning else 102)
    draw.text((cx, time_y), slot.ended_at.strftime("%H:%M"), font=font18, fill=ink, anchor="ms")
    draw.text((cx, amount_y), _amount_text(slot.per_slot_mm), font=font18, fill=amount_fill, anchor="ms")


def _rooms(draw, rooms: list[RoomClimate]):
    origin_x, origin_y = CARD_ORIGIN
    card_w, card_h = CARD_SIZE
    for index in range(6):
        room = rooms[index] if index < len(rooms) else RoomClimate("—", None, None)
        column = index % 3
        row = index // 3
        x = origin_x + column * (card_w + CARD_GAP)
        y = origin_y + row * (card_h + CARD_GAP)
        _room_card(draw, room, x, y, card_w, card_h)


def _room_card(draw, room: RoomClimate, x: int, y: int, w: int, h: int):
    accent = temp_color(room.temperature_c)
    draw.rectangle((x, y, x + w - 1, y + h - 1), outline=BLACK, width=2)
    draw.rectangle((x + 3, y + 3, x + 14, y + h - 4), fill=accent)
    name_y = y + 34
    _room_name(draw, room, x, name_y, w)
    temp_y = y + h - 22
    if room.temperature_c is None:
        draw.text((x + 24, temp_y), "--", font=font48, fill=YELLOW, anchor="ls")
        return
    draw_celsius(
        draw,
        x + 24,
        temp_y,
        f"{room.temperature_c:.1f}",
        font48,
        font14,
        font24,
        fill=accent,
    )


def _room_name(draw, room: RoomClimate, x: int, baseline: int, width: int):
    humidity = _humidity_text(room.humidity_pct)
    right = x + width - 12
    reserved = humidity if humidity else "--"
    taken = draw.textlength(reserved, font=font24) + 28
    name_font = _name_font(draw, room.name, width - 36 - int(taken))
    draw.text((x + 24, baseline), room.name, font=name_font, fill=BLACK, anchor="ls")
    if humidity:
        _draw_right(draw, right, baseline, [(humidity, font24), ("%", font18)], BLUE)
        return
    draw.text((right, baseline), "--", font=font24, fill=YELLOW, anchor="rs")


def _alert_tone(nowcast: HomeNowcast | None, when: datetime, warnings: list[WeatherWarning]) -> str:
    tones = {warning.tone for warning in warnings}
    if "black" in tones:
        return "black"
    peak = nowcast.peak_per_slot_mm if nowcast is not None and _is_current(nowcast, when) else 0.0
    if "red" in tones or peak >= _HEAVY_MM:
        return "red"
    if "yellow" in tones or peak >= _UMBRELLA_MM:
        return "yellow"
    return "white"


def _tone_colors(tone: str):
    if tone == "black":
        return BLACK, WHITE
    if tone in {"red", "yellow"}:
        return YELLOW, BLACK
    return WHITE, BLACK


def _warning_ink(tone: str, warnings: list[WeatherWarning]):
    if tone == "black":
        return WHITE
    if any(warning.tone == "red" for warning in warnings):
        return RED
    if tone == "white" and any(warning.tone == "blue" for warning in warnings):
        return BLUE
    return BLACK


def _amount_fill(per_slot_mm: float, ink):
    if ink == WHITE:
        return WHITE
    if per_slot_mm >= _HEAVY_MM:
        return RED
    return ink


def _family_verdict(nowcast: HomeNowcast) -> tuple[str, str]:
    peak = nowcast.peak_per_slot_mm
    if peak <= 0:
        return "未來兩小時無雨", "dry"
    if peak < _UMBRELLA_MM:
        return "未來兩小時有小雨", "light"
    if peak >= _HEAVY_MM:
        return "未來兩小時將有大雨", "heavy"
    return "未來兩小時有雨，請帶傘", "umbrella"


def _unavailable_text(nowcast: HomeNowcast | None, when: datetime) -> str | None:
    if nowcast is None:
        return "未來兩小時雨量暫時無法取得"
    if not _is_current(nowcast, when):
        return "未來兩小時雨量預報已過時"
    return None


def _is_current(nowcast: HomeNowcast, when: datetime) -> bool:
    if not nowcast.slots:
        return False
    return nowcast.slots[-1].ended_at > when


def _timing_text(nowcast: HomeNowcast, when: datetime) -> str:
    if nowcast.peak_per_slot_mm < _UMBRELLA_MM:
        return "適合外出" if nowcast.is_dry else ""
    first = nowcast.first_wet_slot
    if first is None:
        return ""
    slot_start = first.ended_at - timedelta(minutes=30)
    minutes = max(int(round((slot_start - when).total_seconds() / 60)), 0)
    if minutes == 0:
        return "正在下雨"
    if minutes < 60:
        return f"約 {minutes} 分鐘後開始"
    return f"約 {minutes // 60} 小時後開始"


def _amount_text(per_slot_mm: float) -> str:
    if per_slot_mm <= 0:
        return "0毫米"
    return f"{per_slot_mm:g}毫米"


def _conditions_text(wind_text, uv_text, sun_rise, sun_set) -> str:
    parts = []
    if wind_text:
        parts.append(wind_text)
    if uv_text:
        parts.append(f"紫外線 {uv_text}")
    if sun_rise or sun_set:
        parts.append(f"日出 {sun_rise or '--'}  日落 {sun_set or '--'}")
    return "   ".join(parts)


def _weekday(day) -> str:
    week = str(getattr(day, "week", "") or "")
    for char in reversed(week):
        if char in _WEEKDAYS:
            return char
    return ""


def _depth(day, name: str) -> float | None:
    value = getattr(getattr(day, name, None), "value", None)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _draw_right(draw, right: int, baseline: int, parts, fill):
    width = 0
    for text, font in parts:
        width += draw.textlength(str(text), font=font)
    draw_run(draw, int(right - width), baseline, parts, fill=fill)


def _name_font(draw, name: str, max_width: int):
    for font in (font32, font24, font18, font14):
        if draw.textlength(name, font=font) <= max_width:
            return font
    return font14


def _humidity_text(value) -> str:
    if value is None:
        return ""
    text = str(value).replace("%", "").strip()
    if not text or text.lower() in {"unknown", "unavailable", "none"}:
        return ""
    try:
        return f"{float(text):.0f}"
    except ValueError:
        return text


def _paste_icon(image: Image.Image, icon_id, box, size: int):
    if icon_id is None:
        return
    _paste_file(image, f"{icon_id}.png", box, size)


def _paste_file(image: Image.Image, filename: str, box, size: int, fallback: bool = True):
    path = os.path.join(PIC_DIR, filename)
    if not os.path.exists(path):
        if not fallback:
            return
        path = os.path.join(PIC_DIR, "na.png")
        if not os.path.exists(path):
            return
    icon = Image.open(path).convert("RGBA").resize((size, size), Image.Resampling.NEAREST)
    plate = Image.new("RGBA", icon.size, (*WHITE, 255))
    plate.alpha_composite(icon)
    image.paste(plate.convert("RGB"), box)
