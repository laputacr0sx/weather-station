from datetime import datetime, timedelta
from types import SimpleNamespace

from weather_display.lib.render.home_dashboard import (
    CARD_GAP,
    CARD_ORIGIN,
    CARD_SIZE,
    FORECAST_BOTTOM,
    FORECAST_TOP,
    NOWCAST_TOP,
    ROOM_NOWCAST_TOP,
    _amount_text,
    _family_verdict,
    _timing_text,
    render_forecast_page,
    render_now_page,
)
from weather_display.lib.render.palette import BLACK, BLUE, COLORS, RED, YELLOW
from weather_display.lib.util.home_assistant import RoomClimate
from weather_display.lib.util.rainfall_nowcast import HomeNowcast, NowcastSlot
from weather_display.lib.util.warnings import WeatherWarning
from weather_display.run import _wind_text, choose_page, page_for


def _rooms():
    specs = [
        ("客房", 28.3, 74),
        ("睡房門口", 25.2, 44),
        ("睡房", 24.7, 44),
        ("客廳", 28.6, 73),
        ("大門", 28.3, 73),
        ("露台", None, None),
    ]
    return [RoomClimate(name, temp, humidity) for name, temp, humidity in specs]


def _day(week, icon, high, low):
    return SimpleNamespace(
        week=week,
        forecast_icon=icon,
        forecast_maxtemp=SimpleNamespace(value=high),
        forecast_mintemp=SimpleNamespace(value=low),
    )


def _forecast():
    return [
        _day("星期日", 50, 31, 26),
        _day("星期一", 51, 30, 25),
        _day("星期二", 52, 29, 25),
        _day("星期三", 60, 28, 24),
        _day("星期四", 62, 29, 24),
    ]


def _nowcast(amounts, base=None):
    base = base or datetime(2026, 10, 18, 4, 0)
    slots = []
    cumulative = 0.0
    for index, amount in enumerate(amounts):
        cumulative += amount
        slots.append(
            NowcastSlot(
                ended_at=base + timedelta(minutes=30 * (index + 1)),
                cumulative_mm=cumulative,
                per_slot_mm=amount,
            )
        )
    return HomeNowcast(base_at=base, lat=22.43, lon=114.221, slots=slots)


def _when():
    return datetime(2026, 10, 18, 4, 20)


def _now_image(**overrides):
    fields = dict(
        outdoor_c=31,
        outdoor_humidity="80",
        icon_id=50,
        location="沙田馬鞍山",
        when=_when(),
        lunar="乙巳八月",
        nowcast=_nowcast([0, 0, 0, 0]),
        warnings=None,
    )
    fields.update(overrides)
    return render_now_page(_rooms(), **fields)


def _forecast_image(**overrides):
    fields = dict(
        outdoor_c=31,
        outdoor_humidity="80",
        icon_id=50,
        location="沙田馬鞍山",
        when=_when(),
        lunar="乙巳八月",
        forecast=_forecast(),
        nowcast=_nowcast([0, 0, 0, 0]),
        warnings=None,
        wind_text="風 沙田東 12公里",
        uv_text="3",
        sun_rise="06:21",
        sun_set="17:58",
    )
    fields.update(overrides)
    return render_forecast_page(**fields)


def _accent(image, index):
    origin_x, origin_y = CARD_ORIGIN
    card_w, card_h = CARD_SIZE
    x = origin_x + (index % 3) * (card_w + CARD_GAP)
    y = origin_y + (index // 3) * (card_h + CARD_GAP)
    return image.getpixel((x + 8, y + 40))


def _band_has(image, top, bottom, color):
    for y in range(top, bottom):
        for x in range(image.size[0]):
            if image.getpixel((x, y)) == color:
                return True
    return False


def test_now_page_is_panel_size_and_palette():
    image = _now_image()
    assert image.size == (800, 480)
    assert image.mode == "RGB"
    used = {color for _count, color in image.getcolors(maxcolors=800 * 480)}
    assert used <= set(COLORS)


def test_room_accent_follows_temperature():
    image = _now_image()
    assert _accent(image, 0) == RED
    assert _accent(image, 2) == BLUE
    assert _accent(image, 5) == YELLOW


def test_forecast_page_shows_the_high_in_red():
    image = _forecast_image()
    assert image.size == (800, 480)
    assert _band_has(image, FORECAST_TOP, FORECAST_BOTTOM, RED)


def test_rain_alert_turns_the_nowcast_yellow():
    dry = _forecast_image()
    wet = _forecast_image(nowcast=_nowcast([0, 2.5, 0, 0]))
    assert dry.getpixel((4, NOWCAST_TOP + 8)) != YELLOW
    assert wet.getpixel((4, NOWCAST_TOP + 8)) == YELLOW


def test_stale_nowcast_stays_white():
    stale = _nowcast([1, 0, 0, 0], base=datetime(2026, 10, 17, 22, 0))
    image = _forecast_image(nowcast=stale)
    assert image.getpixel((4, NOWCAST_TOP + 8)) != YELLOW
    assert _band_has(image, NOWCAST_TOP, image.size[1], BLACK)


def test_missing_nowcast_stays_white():
    image = _forecast_image(nowcast=None)
    assert image.getpixel((4, NOWCAST_TOP + 8)) != YELLOW
    assert _band_has(image, NOWCAST_TOP, image.size[1], BLACK)


def test_trace_rain_is_not_an_umbrella_alert():
    nowcast = _nowcast([0.01, 0, 0, 0])
    assert _family_verdict(nowcast) == ("未來兩小時有小雨", "light")
    assert _timing_text(nowcast, _when()) == ""
    image = _forecast_image(nowcast=nowcast)
    assert image.getpixel((4, NOWCAST_TOP + 8)) != YELLOW


def test_heavy_rain_is_yellow_with_red_text():
    image = _forecast_image(nowcast=_nowcast([0, 12, 0, 0]))
    assert image.getpixel((4, NOWCAST_TOP + 8)) == YELLOW
    assert _band_has(image, NOWCAST_TOP, image.size[1], RED)


def test_room_page_shows_the_two_hour_rain():
    wet = _now_image(nowcast=_nowcast([0, 2.5, 0, 0]))
    dry = _now_image()
    assert wet.getpixel((4, ROOM_NOWCAST_TOP + 8)) == YELLOW
    assert dry.getpixel((4, ROOM_NOWCAST_TOP + 8)) != YELLOW


def test_black_warning_fills_the_room_band():
    image = _now_image(warnings=[WeatherWarning("黑色暴雨警告信號", "black")])
    assert image.getpixel((4, ROOM_NOWCAST_TOP + 4)) == BLACK


def test_thunderstorm_warning_turns_the_band_yellow():
    image = _forecast_image(warnings=[WeatherWarning("雷暴警告", "yellow")])
    assert image.getpixel((4, NOWCAST_TOP + 8)) == YELLOW


def test_cold_warning_stays_on_white():
    image = _forecast_image(warnings=[WeatherWarning("寒冷天氣警告", "blue")])
    assert image.getpixel((4, NOWCAST_TOP + 8)) != YELLOW
    assert _band_has(image, NOWCAST_TOP, image.size[1], BLUE)


def test_slot_amount_uses_chinese_unit():
    assert _amount_text(0) == "0毫米"
    assert _amount_text(2.5) == "2.5毫米"
    assert "mm" not in _amount_text(12)


def test_wind_text_uses_chinese_unit():
    wind = SimpleNamespace(station="沙田", wind_direction="東", avg_wind_speed="1")
    text = _wind_text(wind)
    assert text == "風 沙田東 1公里"
    assert "km" not in text


def test_day_timer_alternates_pages():
    assert page_for(datetime(2026, 10, 18, 5, 0)) == "now"
    assert page_for(datetime(2026, 10, 18, 5, 15)) == "forecast"
    assert page_for(datetime(2026, 10, 18, 5, 30)) == "now"


def test_night_timer_alternates_pages():
    assert page_for(datetime(2026, 10, 18, 0, 0)) == "now"
    assert page_for(datetime(2026, 10, 18, 1, 0)) == "forecast"
    assert page_for(datetime(2026, 10, 18, 4, 0)) == "now"


def test_stored_page_flips_each_refresh(tmp_path):
    path = tmp_path / "page"
    when = datetime(2026, 10, 18, 5, 0)
    assert choose_page(path, when) == "now"
    assert choose_page(path, when) == "forecast"
    assert choose_page(path, when) == "now"


def test_urgent_refresh_keeps_the_page_on_the_glass(tmp_path):
    path = tmp_path / "page"
    when = datetime(2026, 10, 18, 5, 0)
    assert choose_page(path, when) == "now"
    assert choose_page(path, when, flip=False) == "now"
    assert path.read_text(encoding="utf-8").strip() == "now"
