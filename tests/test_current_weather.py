"""Tests for :mod:`weather_display.lib.util.current_weather`."""
import json
from datetime import datetime

from weather_display.lib.util.current_weather import parse_current_weather


def _minimal_rhrread_payload(*, uvindex):
    """Build a minimal but schema-valid HKO ``rhrread`` JSON payload.

    The ``uvindex`` field accepts either the documented dict form or the
    placeholder string the API occasionally returns, so both code paths can be
    exercised.
    """
    return {
        "rainfall": {
            "data": [
                {"unit": "mm", "place": "Hong Kong", "max": 0, "main": ""}
            ],
            "startTime": "2024-01-01T00:00:00+08:00",
            "endTime": "2024-01-01T00:15:00+08:00",
        },
        "uvindex": uvindex,
        "icon": [50],
        "iconUpdateTime": "2024-01-01T00:00:00+08:00",
        "updateTime": "2024-01-01T00:00:00+08:00",
        "temperature": {
            "recordTime": "2024-01-01T00:00:00+08:00",
            "data": [
                {"unit": "C", "value": 20, "place": "Hong Kong"}
            ],
        },
        "humidity": {
            "recordTime": "2024-01-01T00:00:00+08:00",
            "data": [
                {"unit": "percent", "value": 80, "place": "Hong Kong"}
            ],
        },
    }


def test_uvindex_dict_payload_is_parsed_not_discarded():
    """Real uvindex data must survive parsing.

    Regression test for the ``type(json_data["uvindex"] is str)`` paren bug,
    which made the empty-uvindex branch run unconditionally and threw away
    every uvindex entry.
    """
    payload = _minimal_rhrread_payload(
        uvindex={
            "data": [
                {"place": "Hong Kong", "value": 7, "desc": "High"}
            ],
            "recordDesc": "High UV index",
        }
    )

    result = parse_current_weather(json.loads(json.dumps(payload)))

    assert result.uvindex.record_desc == "High UV index"
    assert len(result.uvindex.data) == 1
    assert result.uvindex.data[0].value == 7


def test_uvindex_string_placeholder_yields_empty_data():
    """When the API returns the placeholder string, data stays empty.

    This is the intended behaviour for the ``else`` branch the bug never let
    run, kept here so the fix does not over-correct.
    """
    payload = _minimal_rhrread_payload(uvindex="")

    result = parse_current_weather(json.loads(json.dumps(payload)))

    assert result.uvindex.data == []
    assert result.uvindex.record_desc == ""
