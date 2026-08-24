"""
Pytest configuration.

Adds the ``src`` directory to ``sys.path`` so the test-suite can import the
``weather_display`` package without an editable install::

    from weather_display.lib.util.current_weather import parse_current_weather
"""
import os
import sys

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
