"""Tests for :mod:`weather_display.lib.waveshare_epd.epdconfig`.

``epdconfig.py`` runs board detection at import time (it spawns ``cat
/proc/cpuinfo`` and instantiates a board driver), so the tests execute the
module source in an isolated namespace with stubbed platform modules instead
of importing it normally.
"""
import io
import os
import sys
import types
from pathlib import Path

import pytest

EPDCONFIG_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "weather_display"
    / "lib"
    / "waveshare_epd"
    / "epdconfig.py"
)


class _FakeGPIO:
    """Stand-in for gpiozero.LED / gpiozero.Button."""

    def __init__(self, *args, **kwargs):
        pass

    def on(self):
        pass

    def off(self):
        pass

    def close(self):
        pass


def _fake_gpiozero():
    module = types.ModuleType("gpiozero")
    module.LED = _FakeGPIO
    module.Button = _FakeGPIO
    return module


def _fake_spidev():
    module = types.ModuleType("spidev")

    class SpiDev:
        def open(self, *a):
            pass

        def close(self):
            pass

        def writebytes(self, data):
            pass

        def writebytes2(self, data):
            pass

    module.SpiDev = SpiDev
    return module


def _fake_subprocess_output(text):
    """A subprocess stub whose Popen output is the given text."""
    module = types.ModuleType("subprocess")
    module.PIPE = -1

    class Popen:
        def __init__(self, *args, **kwargs):
            pass

        def communicate(self):
            return (text, None)

    module.Popen = Popen
    return module


@pytest.fixture
def epdconfig_on_raspberry_pi(monkeypatch):
    """Execute epdconfig.py as if running on a Raspberry Pi.

    Stubs ``subprocess`` (cpuinfo says "Raspberry Pi"), ``spidev`` and
    ``gpiozero``, and makes every ``.so`` lookup fail so the
    ``Cannot find DEV_Config.so`` path is exercised.
    """
    monkeypatch.setitem(sys.modules, "gpiozero", _fake_gpiozero())
    monkeypatch.setitem(sys.modules, "spidev", _fake_spidev())
    monkeypatch.setitem(
        sys.modules, "subprocess", _fake_subprocess_output("Hardware        : Raspberry Pi 4")
    )

    # 64-bit system, but no DEV_Config_64.so anywhere.
    monkeypatch.setattr(os, "popen", lambda cmd: io.StringIO("64"))
    monkeypatch.setattr(os.path, "exists", lambda p: False)

    module_name = "weather_display.lib.waveshare_epd.epdconfig"
    module = types.ModuleType(module_name)
    module.__file__ = str(EPDCONFIG_PATH)
    sys.modules[module_name] = module

    source = EPDCONFIG_PATH.read_text(encoding="utf-8")
    exec(compile(source, str(EPDCONFIG_PATH), "exec"), module.__dict__)
    return module


def test_module_init_raises_when_so_missing(epdconfig_on_raspberry_pi):
    """module_init(cleanup=True) must RAISE RuntimeError when no .so found.

    Regression test: the original code built the RuntimeError object but
    forgot ``raise``, so execution fell through to ``DEV_Module_Init`` on a
    ``None`` pointer and died with ``AttributeError`` instead.
    """
    epd = epdconfig_on_raspberry_pi

    with pytest.raises(RuntimeError, match="DEV_Config"):
        epd.module_init(cleanup=True)
