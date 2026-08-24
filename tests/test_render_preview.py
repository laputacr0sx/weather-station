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
from weather_display.lib.render.rainfall import render_rainfall_section
from weather_display.lib.util.calculate_time import get_record_time_diff
from weather_display.lib.util.convert_date_string import get_now_str
from weather_display.lib.util.rainfall_nowcast import HomeNowcast, NowcastSlot

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
    icons = [50, 60, 70, 80, 90]
    weeks = ["一(一)", "二(二)", "三(三)", "四(四)", "五(五)"]
    return SimpleNamespace(
        weather_forecast=[
            SimpleNamespace(
                forecast_maxtemp=SimpleNamespace(value=31.0),
                forecast_mintemp=SimpleNamespace(value=26.0),
                forecast_maxrh=SimpleNamespace(value=90.0),
                forecast_minrh=SimpleNamespace(value=70.0),
                forecast_icon=icons[i],
                week=weeks[i],
            )
            for i in range(5)
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
    """Two wet slots: light rain in slot 1, steady in slot 2.

    Slot end times are relative to now so the time-to-rain line is a
    future estimate rather than "raining now" from stale fixture hours.
    """
    base = datetime.now().replace(second=0, microsecond=0)
    ends = [base + timedelta(minutes=30 * (i + 1)) for i in range(4)]
    cumulatives = [0.0, 1.5, 8.0, 8.5]
    per_slot = [cumulatives[0]] + [
        cumulatives[i] - cumulatives[i - 1] for i in range(1, 4)
    ]
    slots = [
        NowcastSlot(
            ended_at=ends[i],
            cumulative_mm=cumulatives[i],
            per_slot_mm=per_slot[i],
        )
        for i in range(4)
    ]
    return HomeNowcast(base_at=base, lat=22.43, lon=114.221, slots=slots)


def test_render_full_dashboard_to_png():
    """Render every section to a single 800x480 image and save it.

    Mirrors run.main() but without the EPD hardware or any network call.
    """
    now = datetime.now()
    weather = _weather()
    time_diff = get_record_time_diff(now, weather.temperature.record_time)

    main_image = Image.new("1", (EPD_WIDTH, EPD_HEIGHT), 255)
    draw = PILImageDraw.Draw(main_image)

    render_header_section(
        _greg(), weather, _humidity(), "沙田馬鞍山", get_now_str(now), draw, main_image, _env()
    )
    render_forecast_section(_forecast(), draw, main_image)
    render_rainfall_section(main_image, _nowcast_wet())
    render_minor_dashboard(_wind(), _uv(), _sun(), draw, main_image)
    render_footer_section(draw, time_diff, now)

    assert main_image.size == (EPD_WIDTH, EPD_HEIGHT)
    histogram = main_image.histogram()
    assert histogram[0] > 0, "dashboard rendered blank - no black pixels drawn"

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    main_image.save(OUTPUT_PATH)
    assert os.path.exists(OUTPUT_PATH)
    assert os.path.getsize(OUTPUT_PATH) > 0
