"""Tests for the ``date`` default argument of the HKO fetchers.

Regression tests for the frozen-default bug: ``def f(date: datetime =
datetime.now())`` evaluates ``datetime.now()`` once at *definition* time, so
the fallback date was stuck at module-import time regardless of when the
function was actually called.
"""
from datetime import datetime, timedelta
from unittest.mock import patch

import requests


class _FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        # gregorian: {"LunarYear": ..., "LunarDate": ...}
        # sun: {"data": [["...", "rise", "transit", "set"]]}
        return {"LunarYear": "甲辰龍年", "LunarDate": "正月初一"}


def _requested_params(call):
    """Extract the params dict whether requests.get got it positionally or by kwarg."""
    if "params" in call.kwargs:
        return call.kwargs["params"]
    # gregorian.py / sun.py pass params positionally: get(url, params)
    return call.args[1] if len(call.args) > 1 else {}


def test_gregorian_default_uses_call_time_date():
    """No-arg call must request *today's* date, not import-time's.

    The module is imported long before the call; if the default were frozen at
    def-time (the old bug), the requested date would drift stale as the day
    rolls over. We simulate the drift by patching ``requests.get`` and checking
    the ``date`` param is generated at call time from a fresh now().
    """
    from weather_display.lib.util import gregorian

    with patch.object(gregorian.requests, "get", return_value=_FakeResponse()) as m:
        gregorian.get_gregorian_date()

    requested = _requested_params(m.call_args).get("date")
    today = datetime.now()
    # Must match today's date (Y-M-D without zero padding, as the module formats it)
    assert requested == f"{today.year}-{today.month}-{today.day}"


def test_sun_default_uses_call_time_date():
    """No-arg call must request *today's* sun times, not import-time's."""
    from weather_display.lib.util import sun

    fake = _FakeResponse()
    fake.json = lambda: {"data": [["2024-01-01", "07:03", "12:24", "17:45"]]}

    with patch.object(sun.requests, "get", return_value=fake) as m:
        sun.get_sun_status()

    params = _requested_params(m.call_args)
    today = datetime.now()
    assert params.get("year") == f"{today.year}"
    assert params.get("month") == f"{today.month}"
    assert params.get("day") == f"{today.day}"


def test_explicit_date_still_overrides_default():
    """Passing a date explicitly must still be honoured."""
    from weather_display.lib.util import gregorian

    explicit = datetime(2024, 1, 1)
    with patch.object(gregorian.requests, "get", return_value=_FakeResponse()) as m:
        gregorian.get_gregorian_date(date=explicit)

    requested = _requested_params(m.call_args).get("date")
    assert requested == "2024-1-1"


def test_defaults_are_none_not_frozen_datetime():
    """The signatures must use the None-sentinel pattern, not a frozen now().

    This is the mechanism that makes lazy evaluation possible. With the old
    code, ``__defaults__`` held a datetime captured at import time.
    """
    from weather_display.lib.util.gregorian import get_gregorian_date
    from weather_display.lib.util.sun import get_sun_status

    assert get_gregorian_date.__defaults__[0] is None
    assert get_sun_status.__defaults__[0] is None
