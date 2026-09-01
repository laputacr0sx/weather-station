"""Tests for the rainfall_nowcast data layer.

These pin down the data-shaping rules: each CSV value is rain in that
30-min window (not a running total), the wet-slot finding logic returns
the first slot with non-zero per-slot rain, and ``None`` propagates when
the CSV fetch fails. The CSV itself is mocked so these tests do not hit
the network.
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

from weather_display.lib.util.rainfall_nowcast import (
    HomeNowcast,
    NowcastSlot,
    _load_csv,
    _nearest_node,
    _pick_nearest,
    get_home_nowcast,
)


CSV_HEADER = (
    "Updated Date and Time (in Hong Kong Time),"
    "Ending Date and Time (in Hong Kong Time),"
    "Latitude (degree),Longitude (degree),"
    "Half-hourly Nowcast Accumulated Rainfall (mm)\n"
)


def _make_csv(per_cell_cumulatives, order="cell"):
    """Build a 4-slot CSV in memory.

    ``per_cell_cumulatives`` maps (lat, lon) -> [c0, c1, c2, c3]. Slot
    end times are 12:30, 13:00, 13:30, 14:00 HKT.

    ``order="cell"`` writes all slots of a cell together (the layout the
    original tests used). ``order="slot"`` writes the real HKO layout:
    every cell of slot 0, then every cell of slot 1, and so on.
    """
    ends = ["202608241230", "202608241300", "202608241330", "202608241400"]
    base = "202608241200"
    lines = [CSV_HEADER]
    cells = list(per_cell_cumulatives.items())
    if order == "slot":
        for i, end in enumerate(ends):
            for (lat, lon), cumulatives in cells:
                lines.append(f"{base},{end},{lat},{lon},{cumulatives[i]:.2f}\n")
    else:
        for (lat, lon), cumulatives in cells:
            for i, end in enumerate(ends):
                lines.append(f"{base},{end},{lat},{lon},{cumulatives[i]:.2f}\n")
    return "".join(lines)


def _fake_response(text):
    resp = MagicMock()
    resp.content = text.encode("utf-8")
    resp.raise_for_status = MagicMock()
    return resp


def _load_patched(csv_text):
    with patch(
        "weather_display.lib.util.rainfall_nowcast.requests.get",
        return_value=_fake_response(csv_text),
    ):
        return _load_csv()


def test_load_csv_parses_times_and_coords():
    csv_text = _make_csv({(22.43, 114.221): [0.0, 1.0, 2.0, 3.0]})
    rows = _load_patched(csv_text)
    assert rows[0]["lat"] == 22.43
    assert rows[0]["lon"] == 114.221
    assert rows[0]["endedAt"] == datetime(2026, 8, 24, 12, 30)
    assert rows[0]["updatedAt"] == datetime(2026, 8, 24, 12, 0)
    assert rows[0]["rainfall"] == 0.0


def test_pick_nearest_prefers_closer_cell():
    nodes = [
        (22.412, 114.221),
        (22.430, 114.221),
        (22.448, 114.221),
    ]
    assert _pick_nearest(nodes, 22.424, 114.227) == (22.430, 114.221)


def test_nearest_node_picks_closest_cell_cell_major_csv():
    csv_text = _make_csv(
        {
            (22.412, 114.221): [0.0, 0.0, 0.0, 0.0],
            (22.430, 114.221): [0.0, 0.0, 0.0, 0.0],
            (22.448, 114.221): [0.0, 0.0, 0.0, 0.0],
        },
        order="cell",
    )
    rows = _load_patched(csv_text)
    lat, lon = _nearest_node(rows, 22.424, 114.227)
    assert (lat, lon) == (22.43, 114.221)


def test_nearest_node_picks_closest_cell_slot_major_csv():
    """HKO files list every grid point of slot 0, then slot 1, etc."""
    csv_text = _make_csv(
        {
            (22.412, 114.221): [0.0, 0.0, 0.0, 0.0],
            (22.430, 114.221): [0.0, 0.0, 0.0, 0.0],
            (22.448, 114.221): [0.0, 0.0, 0.0, 0.0],
        },
        order="slot",
    )
    rows = _load_patched(csv_text)
    lat, lon = _nearest_node(rows, 22.424, 114.227)
    assert (lat, lon) == (22.43, 114.221)


def test_get_home_nowcast_treats_csv_values_as_per_slot():
    """HKO 'half-hourly accumulated' is rain in that 30 min, not a running total.

    Live cells rise and fall (e.g. 2.63, 3.99, 8.52, 3.67). Differencing
    those would invent a negative last slot and under-state the peak.
    """
    csv_text = _make_csv({(22.43, 114.221): [2.63, 3.99, 8.52, 3.67]})
    with patch(
        "weather_display.lib.util.rainfall_nowcast.requests.get",
        return_value=_fake_response(csv_text),
    ):
        nowcast = get_home_nowcast()
    assert isinstance(nowcast, HomeNowcast)
    per_slot = [s.per_slot_mm for s in nowcast.slots]
    cumulatives = [s.cumulative_mm for s in nowcast.slots]
    assert per_slot == [2.63, 3.99, 8.52, 3.67]
    assert cumulatives == [2.63, 6.62, 15.14, 18.81]
    assert nowcast.peak_per_slot_mm == 8.52
    assert nowcast.total_mm == 18.81


def test_first_wet_slot_finds_earliest_rain():
    csv_text = _make_csv({(22.43, 114.221): [0.0, 0.0, 4.0, 4.0]})
    with patch(
        "weather_display.lib.util.rainfall_nowcast.requests.get",
        return_value=_fake_response(csv_text),
    ):
        nowcast = get_home_nowcast()
    first = nowcast.first_wet_slot
    assert first is not None
    assert first.ended_at == datetime(2026, 8, 24, 13, 30)
    assert first.per_slot_mm == 4.0


def test_is_dry_true_when_all_zero():
    csv_text = _make_csv({(22.43, 114.221): [0.0, 0.0, 0.0, 0.0]})
    with patch(
        "weather_display.lib.util.rainfall_nowcast.requests.get",
        return_value=_fake_response(csv_text),
    ):
        nowcast = get_home_nowcast()
    assert nowcast.is_dry
    assert nowcast.first_wet_slot is None
    assert nowcast.peak_per_slot_mm == 0.0
    assert nowcast.total_mm == 0.0


def test_get_home_nowcast_returns_none_on_network_failure():
    import requests

    with patch(
        "weather_display.lib.util.rainfall_nowcast.requests.get",
        side_effect=requests.RequestException("network down"),
    ):
        assert get_home_nowcast() is None


def test_get_home_nowcast_returns_none_on_empty_csv():
    with patch(
        "weather_display.lib.util.rainfall_nowcast.requests.get",
        return_value=_fake_response(CSV_HEADER),
    ):
        assert get_home_nowcast() is None


def test_nowcast_slot_dataclass():
    s = NowcastSlot(
        ended_at=datetime(2026, 8, 24, 12, 30),
        cumulative_mm=1.5,
        per_slot_mm=1.5,
    )
    assert s.cumulative_mm == 1.5
    assert s.per_slot_mm == 1.5
