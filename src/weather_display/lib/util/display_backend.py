"""Choose e-paper vs desktop preview without importing Waveshare on a laptop.

Default is auto: Raspberry Pi (any model, including Zero 2 W) uses the EPD;
everything else calls ``Image.show()``. Override with ``WEATHER_DISPLAY_OUTPUT``:

* ``auto`` (default) — detect from the device tree / cpuinfo
* ``epd`` — force the panel (even if detection fails)
* ``preview`` — force a window, never touch SPI/GPIO
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from PIL import Image

_LOG = logging.getLogger(__name__)

_OUTPUT_ENV = "WEATHER_DISPLAY_OUTPUT"
_PI_MODEL_PATHS = (
    Path("/proc/device-tree/model"),
    Path("/sys/firmware/devicetree/base/model"),
)


def _pi_model() -> str | None:
    for path in _PI_MODEL_PATHS:
        try:
            text = path.read_bytes().split(b"\x00", 1)[0].decode("utf-8", "replace").strip()
        except OSError:
            continue
        if text:
            return text
    try:
        cpuinfo = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in cpuinfo.splitlines():
        if "raspberry" in line.lower():
            return line.strip()
    return None


def use_epd() -> bool:
    flag = os.environ.get(_OUTPUT_ENV, "auto").strip().lower()
    if flag in {"epd", "1", "true", "yes"}:
        return True
    if flag in {"preview", "show", "0", "false", "no"}:
        return False
    model = _pi_model()
    return bool(model and "raspberry pi" in model.lower())


def present(image: Image.Image) -> None:
    """Push ``image`` to the EPD on a Pi, otherwise open a desktop preview."""
    if use_epd():
        _LOG.info("Displaying on EPD")
        _present_epd(image)
        return
    _LOG.info("No Raspberry Pi EPD — opening preview")
    image.show()


def _present_epd(image: Image.Image) -> None:
    # Imported only on the Pi so Windows/dev never loads spidev/gpiozero.
    from weather_display.lib.waveshare_epd import epd7in5_V2

    epd = epd7in5_V2.EPD()
    epd.init()
    try:
        epd.display(epd.getbuffer(image))
    finally:
        epd.sleep()
