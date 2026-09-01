"""Integration test: render a full preview of the dashboard to a PNG.

This exercises every render section exactly as ``run.py`` does, but with the
network layer stubbed:

* HKO data fetchers are bypassed - fixtures are built from ``SimpleNamespace``
  matching the dataclass shapes the renderers read.
* A synthetic ``HomeNowcast`` is passed to the rainfall renderer so no
  network call is needed to produce a complete image.

The resulting image is written to ``tests/output/dashboard_preview.png`` so it
can be opened and eyeballed.
"""
import os
from datetime import datetime, timedelta
from types import SimpleNamespace

from PIL import Image, ImageDraw as PILImageDraw

from weather_display import EPD_HEIGHT, EPD_WIDTH
from weather_display.lib.render.dashboard import render_minor_dashboard
from weather_display.lib.render.footer import render_footer_section
from weather_display.lib.render.forecast import render_forecast_section
from weather_display.lib.render.header import render_header_section
from weather_display.lib.render.rainfall import COMPACT_RAINFALL, render_rainfall_section
from weather_display.lib.render.warnings import (
    STRIP_H,
    STRIP_W,
    STRIP_X,
    STRIP_Y,
    layout_strip,
    render_warning_strip,
)
from weather_display.lib.util.calculate_time import get_record_time_diff
from weather_display.lib.util.convert_date_string import get_now_str
from weather_display.lib.util.hourly_rainfall import HourlyRainfall
from weather_display.lib.util.rainfall_nowcast import HomeNowcast, NowcastSlot
from weather_display.lib.util.warnings import WarningStrip, parse_warnsum

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "dashboard_preview.png")


def _weather():
    return SimpleNamespace(
        icon=[50],
        temperature=SimpleNamespace(
            record_time=datetime(2026, 8, 24, 10, 30),
            data=[SimpleNamespace(value=28.3, place="Hong Kong", unit="C")],
        ),
    )


def _humidity():
    return SimpleNamespace(humidity=75)


def _forecast():
    icons = [50, 60, 70, 80, 90, 51, 62, 63, 65]
    weeks = [
        "星期一",
        "星期二",
        "星期三",
        "星期四",
        "星期五",
        "星期六",
        "星期日",
        "星期一",
        "星期二",
    ]
    return SimpleNamespace(
        weather_forecast=[
            SimpleNamespace(
                forecast_maxtemp=SimpleNamespace(value=31.0 - (i % 3)),
                forecast_mintemp=SimpleNamespace(value=26.0 - (i % 2)),
                forecast_maxrh=SimpleNamespace(value=90.0),
                forecast_minrh=SimpleNamespace(value=70.0),
                forecast_icon=icons[i],
                week=weeks[i],
            )
            for i in range(9)
        ]
    )


def _wind():
    return SimpleNamespace(station="沙田", avg_wind_speed=15, wind_direction="東")


def _uv():
    return SimpleNamespace(uv_index=7, datetime=datetime(2026, 8, 24, 11, 0))


def _sun():
    return SimpleNamespace(rise="06:12", set="18:34")


def _greg():
    return SimpleNamespace(lunar_year="甲辰龍年", lunar_date="八月十五")


def _env():
    return SimpleNamespace(temperature=27.9, humidity=63.4, pressure=1009.5)


def _nowcast_wet():
    """Four-step gauge: dry, light, heavy, steady.

    Slot end times are relative to now so the time-to-rain line is a
    future estimate rather than "raining now" from stale fixture hours.
    """
    base = datetime.now().replace(second=0, microsecond=0)
    ends = [base + timedelta(minutes=30 * (i + 1)) for i in range(4)]
    per_slot = [0.0, 1.5, 12.0, 4.0]
    cumulatives = []
    running = 0.0
    for v in per_slot:
        running += v
        cumulatives.append(running)
    slots = [
        NowcastSlot(
            ended_at=ends[i],
            cumulative_mm=cumulatives[i],
            per_slot_mm=per_slot[i],
        )
        for i in range(4)
    ]
    return HomeNowcast(base_at=base, lat=22.43, lon=114.221, slots=slots)


def _render_dashboard(warning_strip: WarningStrip | None = None) -> Image.Image:
    now = datetime.now()
    weather = _weather()
    time_diff = get_record_time_diff(now, weather.temperature.record_time)

    main_image = Image.new("1", (EPD_WIDTH, EPD_HEIGHT), 255)
    draw = PILImageDraw.Draw(main_image)

    render_header_section(
        _greg(), weather, _humidity(), "沙田馬鞍山", get_now_str(now), draw, main_image, _env()
    )
    render_forecast_section(_forecast(), draw, main_image)
    rainfall_layout = None
    if warning_strip is not None and render_warning_strip(main_image, warning_strip):
        rainfall_layout = COMPACT_RAINFALL
    observed = HourlyRainfall("沙田", "RF020", 2.0, datetime(2026, 9, 1, 10, 45))
    render_rainfall_section(
        main_image, _nowcast_wet(), rainfall_layout, observed=observed
    )
    render_minor_dashboard(_wind(), _uv(), _sun(), draw, main_image)
    render_footer_section(draw, time_diff, now)
    return main_image


def test_render_full_dashboard_to_png():
    """Render every section to a single 800x480 image and save it.

    Mirrors run.main() but without the EPD hardware or any network call.
    Quiet-day path: no warning strip, rainfall at the original y=242 band.
    """
    main_image = _render_dashboard()

    assert main_image.size == (EPD_WIDTH, EPD_HEIGHT)
    histogram = main_image.histogram()
    assert histogram[0] > 0, "dashboard rendered blank - no black pixels drawn"

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    main_image.save(OUTPUT_PATH)
    assert os.path.exists(OUTPUT_PATH)
    assert os.path.getsize(OUTPUT_PATH) > 0


def _strip_is_inverted(image: Image.Image) -> bool:
    """The warning bar is a black rectangle; most pixels in it must be ink."""
    crop = image.crop((STRIP_X, STRIP_Y, STRIP_X + STRIP_W, STRIP_Y + STRIP_H))
    hist = crop.histogram()
    return hist[0] > hist[255]


def test_render_two_warnings_and_tip_to_png():
    """Today-shaped case: 黃雨 + 雷暴 + a pre-signal tip."""
    chips = parse_warnsum(
        {
            "WRAIN": {
                "name": "暴雨警告信號",
                "code": "WRAINA",
                "type": "黃色",
                "actionCode": "ISSUE",
            },
            "WTS": {
                "name": "雷暴警告",
                "code": "WTS",
                "actionCode": "ISSUE",
            },
        }
    )
    strip = WarningStrip(chips=chips, tip="黃昏或考慮發出一號")
    image = _render_dashboard(strip)
    assert _strip_is_inverted(image)
    path = os.path.join(OUTPUT_DIR, "dashboard_preview_warnings.png")
    image.save(path)
    assert os.path.getsize(path) > 0


def test_render_six_warnings_to_png():
    """Typhoon-day overlap: six chips, no wrap, tip yields to the chips."""
    chips = parse_warnsum(
        {
            "WTCSGNL": {
                "name": "熱帶氣旋警告信號",
                "code": "TC8NE",
                "actionCode": "ISSUE",
            },
            "WRAIN": {
                "name": "暴雨警告信號",
                "code": "WRAINB",
                "type": "黑色",
                "actionCode": "ISSUE",
            },
            "WTS": {"name": "雷暴警告", "code": "WTS", "actionCode": "ISSUE"},
            "WL": {"name": "山泥傾瀉警告", "code": "WL", "actionCode": "ISSUE"},
            "WFNTSA": {
                "name": "新界北部水浸特別報告",
                "code": "WFNTSA",
                "actionCode": "ISSUE",
            },
            "WMSGNL": {
                "name": "強烈季候風信號",
                "code": "WMSGNL",
                "actionCode": "ISSUE",
            },
        }
    )
    strip = WarningStrip(
        chips=chips,
        tip="沙德爾殘餘靠近，黃昏或考慮發出一號戒備信號",
    )
    packed = layout_strip(strip)
    assert packed.show_labels is True
    assert packed.tip is None
    image = _render_dashboard(strip)
    assert _strip_is_inverted(image)
    path = os.path.join(OUTPUT_DIR, "dashboard_preview_warnings_six.png")
    image.save(path)
    assert os.path.getsize(path) > 0


def test_render_eight_warnings_icons_only_to_png():
    """Synthetic overflow: eight chips drop labels rather than wrap."""
    chips = parse_warnsum(
        {
            "WTCSGNL": {
                "name": "熱帶氣旋警告信號",
                "code": "TC8NE",
                "actionCode": "ISSUE",
            },
            "WRAIN": {
                "name": "暴雨警告信號",
                "code": "WRAINB",
                "type": "黑色",
                "actionCode": "ISSUE",
            },
            "WTS": {"name": "雷暴警告", "code": "WTS", "actionCode": "ISSUE"},
            "WL": {"name": "山泥傾瀉警告", "code": "WL", "actionCode": "ISSUE"},
            "WFNTSA": {
                "name": "新界北部水浸特別報告",
                "code": "WFNTSA",
                "actionCode": "ISSUE",
            },
            "WMSGNL": {
                "name": "強烈季候風信號",
                "code": "WMSGNL",
                "actionCode": "ISSUE",
            },
            "WHOT": {"name": "酷熱天氣警告", "code": "WHOT", "actionCode": "ISSUE"},
            "WFIRE": {
                "name": "火災危險警告",
                "code": "WFIRER",
                "actionCode": "ISSUE",
            },
        }
    )
    strip = WarningStrip(chips=chips, tip="will not fit")
    packed = layout_strip(strip)
    assert packed.show_labels is False
    assert packed.tip is None
    assert len(packed.chips) == 8
    image = _render_dashboard(strip)
    assert _strip_is_inverted(image)
    path = os.path.join(OUTPUT_DIR, "dashboard_preview_warnings_eight.png")
    image.save(path)
    assert os.path.getsize(path) > 0
