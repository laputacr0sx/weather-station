"""Tests for the home rainfall-nowcast renderer.

Assert the action verdict, the 4-level rain-gauge mapping, and that dry /
unavailable / wet paths all draw ink. Severity is a cup fill plus a
2-character word, not an HKO weather icon.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from PIL import Image

from weather_display import EPD_WIDTH
from weather_display.lib.render.rainfall import (
    GAUGE_FULL_MM,
    GAUGE_MIN_WET_RATIO,
    SECTION_H,
    SECTION_W,
    SECTION_X,
    SECTION_Y,
    SEVERITY_DRY,
    SEVERITY_HEAVY,
    SEVERITY_LIGHT,
    SEVERITY_STEADY,
    SEVERITY_TORRENTIAL,
    _gauge_fill_ratio,
    _minutes_to_first_wet,
    _mm_text,
    _severity,
    _severity_label,
    _slot_label,
    _verdict_text,
    _when_text,
    render_rainfall_section,
)
from weather_display.lib.util.hourly_rainfall import HourlyRainfall
from weather_display.lib.util.rainfall_nowcast import HomeNowcast, NowcastSlot


def _make_nowcast(per_slot_mm):
    """Build a HomeNowcast with the given per-slot mm values."""
    base_dt = datetime(2026, 8, 24, 12, 0)
    ends = [base_dt + timedelta(minutes=30 * (i + 1)) for i in range(4)]
    cumulatives = []
    running = 0.0
    for v in per_slot_mm:
        running += v
        cumulatives.append(round(running, 3))
    slots = [
        NowcastSlot(
            ended_at=ends[i],
            cumulative_mm=cumulatives[i],
            per_slot_mm=per_slot_mm[i],
        )
        for i in range(4)
    ]
    return HomeNowcast(base_at=base_dt, lat=22.43, lon=114.221, slots=slots)


def test_severity_dry():
    assert _severity(0.0) == SEVERITY_DRY
    assert _severity_label(0.0) == "無雨"


def test_severity_light():
    assert _severity(1.0) == SEVERITY_LIGHT
    assert _severity_label(1.0) == "小雨"


def test_severity_steady():
    assert _severity(4.0) == SEVERITY_STEADY
    assert _severity_label(4.0) == "中雨"


def test_severity_heavy():
    assert _severity(8.0) == SEVERITY_HEAVY
    assert _severity_label(8.0) == "大雨"


def test_severity_torrential():
    assert _severity(15.0) == SEVERITY_TORRENTIAL
    assert _severity_label(40.0) == "暴雨"


def test_gauge_fill_is_zero_when_dry():
    assert _gauge_fill_ratio(0.0) == 0.0


def test_gauge_fill_spreads_common_amounts():
    """2.5 mm and 10 mm must not share a cup height."""
    light = _gauge_fill_ratio(2.5)
    heavy = _gauge_fill_ratio(10.0)
    assert light >= GAUGE_MIN_WET_RATIO
    assert heavy > light + 0.2
    assert _gauge_fill_ratio(GAUGE_FULL_MM) == 1.0
    assert _gauge_fill_ratio(GAUGE_FULL_MM + 10) == 1.0


def test_gauge_fill_keeps_drizzle_visible():
    assert _gauge_fill_ratio(0.2) == GAUGE_MIN_WET_RATIO


def test_verdict_dry_says_no_rain():
    nc = _make_nowcast([0.0, 0.0, 0.0, 0.0])
    assert "無雨" in _verdict_text(nc)


def test_verdict_light_rain_says_bring_umbrella():
    nc = _make_nowcast([1.0, 0.0, 0.0, 0.0])
    assert "帶傘" in _verdict_text(nc)


def test_verdict_heavy_rain_says_heavy():
    nc = _make_nowcast([0.0, 0.0, 12.0, 0.0])
    assert "大雨" in _verdict_text(nc)


def test_verdict_torrential_says_torrential():
    nc = _make_nowcast([0.0, 0.0, 30.0, 0.0])
    assert "暴雨" in _verdict_text(nc)


def test_when_text_dry_says_ok_to_go_out():
    assert _when_text(_make_nowcast([0.0, 0.0, 0.0, 0.0])) == "適合外出"


def test_when_text_uses_observed_rain_not_nowcast_window():
    observed = HourlyRainfall("沙田", "RF020", 2.0, datetime(2026, 9, 1, 10, 45))
    assert "過去1小時" in _when_text(_make_nowcast([0.0, 0.0, 0.0, 0.0]), observed)


def test_verdict_observed_wet_nowcast_dry():
    observed = HourlyRainfall("沙田", "RF020", 1.0, datetime(2026, 9, 1, 10, 45))
    assert "正在下雨" in _verdict_text(_make_nowcast([0.0, 0.0, 0.0, 0.0]), observed)


def test_mm_text_keeps_fractional_wet_amounts():
    assert _mm_text(0.0) == "0mm"
    assert _mm_text(0.5) == "0.5mm"
    assert _mm_text(1.5) == "1.5mm"
    assert _mm_text(6.0) == "6mm"


def test_slot_label_uses_24_hour_clock():
    nc = _make_nowcast([0.0, 0.0, 0.0, 0.0])
    assert _slot_label(nc.slots[0]) == "12:30"
    assert _slot_label(nc.slots[1]) == "13:00"


@patch("weather_display.lib.render.rainfall.datetime")
def test_minutes_to_first_wet_uses_slot_start_not_end(mock_datetime):
    mock_datetime.now.return_value = datetime(2026, 8, 24, 12, 0)
    # Slot 0 dry (ends 12:30), slot 1 wet (ends 13:00 => starts 12:30).
    nc = _make_nowcast([0.0, 1.0, 0.0, 0.0])
    assert _minutes_to_first_wet(nc) == 30


@pytest.fixture
def blank_image():
    return Image.new("1", (EPD_WIDTH, 480), 255)


def test_render_dry_nowcast_writes_verdict(blank_image):
    """All-zero forecast should still render the 'no rain' verdict."""
    nowcast = _make_nowcast([0.0, 0.0, 0.0, 0.0])
    render_rainfall_section(blank_image, nowcast)
    crop = blank_image.crop(
        (SECTION_X, SECTION_Y, SECTION_X + SECTION_W, SECTION_Y + SECTION_H)
    )
    hist = crop.histogram()
    assert hist[0] > 0, "dry section should still draw text, not be blank"


def test_render_unavailable_draws_error_line(blank_image):
    render_rainfall_section(blank_image, None)
    crop = blank_image.crop(
        (SECTION_X, SECTION_Y, SECTION_X + SECTION_W, SECTION_Y + SECTION_H)
    )
    hist = crop.histogram()
    assert hist[0] > 0, "unavailable-section should draw the error text"


def test_render_wet_nowcast_does_not_crash(blank_image):
    """A mixed wet nowcast exercises gauges, labels, and mm text."""
    nowcast = _make_nowcast([0.0, 1.5, 12.0, 4.0])
    render_rainfall_section(blank_image, nowcast)
    crop = blank_image.crop(
        (SECTION_X, SECTION_Y, SECTION_X + SECTION_W, SECTION_Y + SECTION_H)
    )
    hist = crop.histogram()
    assert hist[0] > 0
