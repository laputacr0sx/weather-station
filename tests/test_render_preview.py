"""Integration test: render a full preview of the dashboard to a PNG.

This exercises every render section exactly as ``run.py`` does, but with the
network and heavy-plotting layers stubbed:

* HKO data fetchers are bypassed - fixtures are built from ``SimpleNamespace``
  matching the dataclass shapes the renderers read.
* ``render_rainfall_chart`` / ``get_temperature_plot`` are patched to return a
  small PIL-generated PNG, so no ``pandas``/``matplotlib``/``selenium`` is
  needed to produce a complete image.

The resulting image is written to ``tests/output/dashboard_preview.png`` so it
can be opened and eyeballed.
"""
import importlib.util
import io
import os
import sys
import types
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from PIL import Image

# --- optional heavy dependencies --------------------------------------------
# The render modules import matplotlib/pandas/selenium transitively at import
# time even though this test patches the chart functions themselves. If those
# packages are not installed (e.g. a dev laptop without the plotting stack),
# fabricate inert stub modules so the imports resolve and every attribute /
# call on them is a no-op.

_HEAVY_DEPS = ("matplotlib", "pandas", "selenium")


class _Any:
    """Anything you ask of it, it returns itself."""

    def __getattr__(self, name):
        return self

    def __call__(self, *args, **kwargs):
        return self


class _StubModule(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        return _Any()


class _StubFinder:
    """Fabricates ``top.sub`` modules for uninstalled top-level packages."""

    def __init__(self, tops):
        self._tops = set(tops)

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] not in self._tops:
            return None
        spec = importlib.util.spec_from_loader(fullname, loader=None)
        spec.loader = _StubLoader()
        return spec


class _StubLoader:
    def create_module(self, spec):
        module = _StubModule(spec.name)
        module.__path__ = []  # mark as package so submodule imports work
        return module

    def exec_module(self, module):
        pass


_missing = [name for name in _HEAVY_DEPS if importlib.util.find_spec(name) is None]
if _missing:
    sys.meta_path.insert(0, _StubFinder(_missing))

# numpy._typing._UnknownType was removed in numpy >= 2.x but the visualizer
# module imports it as a type-hint (never evaluated at runtime).  Patch it in
# so the import doesn't fail.
try:
    import numpy._typing as _nt

    if not hasattr(_nt, "_UnknownType"):
        _nt._UnknownType = type(None)
except ImportError:
    pass

from weather_display import EPD_HEIGHT, EPD_WIDTH
from weather_display.lib.render import colors
from weather_display.lib.render.dashboard import render_minor_dashboard
from weather_display.lib.render.footer import render_footer_section
from weather_display.lib.render.forecast import render_forecast_section
from weather_display.lib.render.header import render_header_section
from weather_display.lib.render.rainfall import render_rainfall_section
from weather_display.lib.util.calculate_time import get_record_time_diff
from weather_display.lib.util.convert_date_string import get_now_str

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "dashboard_preview.png")

# 6-color palette of the epd7in3e driver (black, white, green, blue, red,
# yellow) - used to verify semantic colors survive panel quantization.
EPD7IN3E_PALETTE = (
    0, 0, 0, 255, 255, 255, 0, 255, 0, 0, 0, 255, 255, 0, 0, 255, 255, 0
)


# --- fixtures ---------------------------------------------------------------
def _weather():
    return SimpleNamespace(
        icon=[50],
        temperature=SimpleNamespace(
            record_time=datetime(2026, 8, 24, 10, 30),
            data=[SimpleNamespace(value=31.4, place="Hong Kong", unit="C")],
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
                forecast_mintemp=SimpleNamespace(value=14.0),
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


def _placeholder_chart_png():
    """A small solid PNG standing in for the rainfall/temperature chart."""
    chart = Image.new("L", (200, 120), 200)
    draw = ImageDraw(chart)
    draw.rectangle((0, 0, 199, 119), outline=0, width=2)
    return _to_png(chart)


def _to_png(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def ImageDraw(img):
    """Local alias - import lazily so a missing PIL aborts the test, not import."""
    from PIL import ImageDraw as _ID

    return _ID.Draw(img)


# --- test ------------------------------------------------------------------
@pytest.fixture
def stubbed_charts():
    """Patch both chart sources to return a placeholder PNG."""
    with patch(
        "weather_display.lib.render.rainfall.render_rainfall_chart",
        return_value=_placeholder_chart_png(),
    ), patch(
        "weather_display.lib.temperature_forecast.app.get_temperature_plot",
        return_value=_placeholder_chart_png(),
    ):
        yield


@pytest.fixture
def color_mode(monkeypatch):
    """Enable color mode (WEATHER_DISPLAY_COLOR=1) and reset the cache after."""
    monkeypatch.setenv("WEATHER_DISPLAY_COLOR", "1")
    colors._COLOR_MODE = True
    yield
    colors._COLOR_MODE = None


def _render_dashboard(now: datetime):
    """Render every section onto a fresh canvas, as run.main() does."""
    weather = _weather()
    time_diff = get_record_time_diff(now, weather.temperature.record_time)

    if colors.color_mode_enabled():
        main_image = Image.new("RGB", (EPD_WIDTH, EPD_HEIGHT), colors.WHITE)
    else:
        main_image = Image.new("1", (EPD_WIDTH, EPD_HEIGHT), 255)

    draw = ImageDraw(main_image)

    render_header_section(
        _greg(), weather, _humidity(), "沙田馬鞍山", get_now_str(now), draw, main_image, _env()
    )
    render_forecast_section(_forecast(), draw, main_image)
    render_rainfall_section(main_image)
    render_minor_dashboard(_wind(), _uv(), _sun(), draw, main_image)
    render_footer_section(draw, time_diff, now)
    return main_image


def test_render_full_dashboard_to_png_bw(stubbed_charts):
    """B/W mode: 1-bit image, all-black drawing - the original behavior."""
    colors._COLOR_MODE = None
    now = datetime.now()
    main_image = _render_dashboard(now)

    assert main_image.mode == "1"
    assert main_image.size == (EPD_WIDTH, EPD_HEIGHT)
    histogram = main_image.histogram()
    assert histogram[0] > 0, "dashboard rendered blank - no black pixels drawn"

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    preview_path = os.path.join(OUTPUT_DIR, "dashboard_preview_bw.png")
    main_image.save(preview_path)
    assert os.path.getsize(preview_path) > 0


def test_render_full_dashboard_to_png_color(stubbed_charts, color_mode):
    """Color mode: RGB image with semantic colors surviving panel quantization."""
    now = datetime.now()
    main_image = _render_dashboard(now)

    assert main_image.mode == "RGB"
    assert main_image.size == (EPD_WIDTH, EPD_HEIGHT)

    colors_found = _quantized_colors(main_image)
    for name, rgb in {"red": (255, 0, 0), "blue": (0, 0, 255), "green": (0, 255, 0)}.items():
        assert rgb in colors_found, (
            f"quantized preview lacks {name} pixels - semantic color lost "
            f"(found: {sorted(colors_found)})"
        )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    main_image.save(OUTPUT_PATH)
    assert os.path.getsize(OUTPUT_PATH) > 0


def _quantized_colors(image: Image.Image) -> set:
    """Quantize like epd7in3e.getbuffer() and return the set of colors present."""
    pal_image = Image.new("P", (1, 1))
    pal_image.putpalette(EPD7IN3E_PALETTE + (0, 0, 0) * 250)
    quantized = image.convert("RGB").quantize(palette=pal_image).convert("RGB")
    return {c[1] for c in quantized.getcolors(maxcolors=8)}
