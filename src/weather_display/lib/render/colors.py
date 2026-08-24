"""Color helpers for the weather dashboard render pipeline.

The dashboard supports two output targets behind a single feature flag:

* **B/W mode** (default) - the original 1-bit (``mode='1'``) black-on-white
  e-ink display.  Every ``fill`` value is the integer ``0`` (black).
* **Color mode** - the Waveshare 7.3inch e-Paper HAT (E), a 7-color (Spectra)
  panel at the same 800x480 resolution.  Its driver
  (:mod:`weather_display.lib.waveshare_epd.epd7in3e`) quantizes any RGB image
  down to six colors - black, white, green, blue, red, yellow.

Rather than branching in every render module, the helpers here resolve the
*semantic* color (e.g. "a hot temperature is red") into the concrete fill value
for the active mode: an ``(R, G, B)`` tuple in color mode, or ``0`` in B/W mode.
This keeps B/W output pixel-identical to the pre-color codebase while letting
color mode assign meaning to each drawn element.

Color mode is toggled with the ``WEATHER_DISPLAY_COLOR`` environment variable
(``1``/``true`` -> color mode; anything else / unset -> B/W).
"""
import os

# --- 6-color palette (matches epd7in3e.getbuffer palette, in order) ---------
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# --- thresholds for semantic color choices ---------------------------------
HOT_THRESHOLD_C = 30.0  # at/above this -> hot (red)
COLD_THRESHOLD_C = 15.0  # at/below this -> cold (blue)

_COLOR_MODE: bool | None = None


def color_mode_enabled() -> bool:
    """Whether color rendering is active for this process.

    Reads ``WEATHER_DISPLAY_COLOR`` once and caches the result so all render
    modules agree on the mode within a single render pass. Defaults to B/W
    (``False``) when unset.
    """
    global _COLOR_MODE
    if _COLOR_MODE is None:
        _COLOR_MODE = os.environ.get('WEATHER_DISPLAY_COLOR', '').strip().lower() in (
            '1',
            'true',
            'yes',
            'on',
        )
    return _COLOR_MODE


def ink(color_rgb: tuple) -> tuple | int:
    """Resolve a semantic color to the fill value for the active mode.

    Returns the ``(R, G, B)`` tuple in color mode, or ``0`` (black) in B/W
    mode - the same integer the original code passed as ``fill=0``.
    """
    return color_rgb if color_mode_enabled() else 0


def temperature_ink(temp: float) -> tuple | int:
    """Hot -> red, cold -> blue, comfortable -> green (or black in B/W)."""
    if temp >= HOT_THRESHOLD_C:
        return ink(RED)
    if temp <= COLD_THRESHOLD_C:
        return ink(BLUE)
    return ink(GREEN)


def uv_ink(uv_index: float) -> tuple | int:
    """UV index color scale: low -> green, moderate -> yellow, high -> red."""
    if uv_index < 3:
        return ink(GREEN)
    if uv_index <= 5:
        return ink(YELLOW)
    return ink(RED)
