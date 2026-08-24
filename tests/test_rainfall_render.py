"""Tests for the home rainfall-nowcast renderer.

These tests stub the icon-set file lookups so the renderer can run in
isolation, then assert the verdict text and per-slot icon choices
match the design intent (dry -> "no rain"; wet -> "rain, bring umbrella";
heavy -> "heavy rain"; none / unavailable -> error line).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from PIL import Image, ImageDraw

from weather_display import EPD_WIDTH
from weather_display.lib.render.rainfall import (
    SECTION_H,
    SECTION_W,
    SECTION_X,
    SECTION_Y,
    _icon_for,
    _minutes_to_first_wet,
    _mm_text,
    _slot_label,
    _verdict_text,
    render_rainfall_section,
)
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


def test_icon_for_dry_slot_returns_none():
    assert _icon_for(0.0) is None


def test_icon_for_light_rain_returns_60():
    assert _icon_for(1.0) == "60.png"


def test_icon_for_steady_rain_returns_64():
    assert _icon_for(5.0) == "64.png"


def test_icon_for_heavy_rain_returns_65():
    assert _icon_for(20.0) == "65.png"


def test_icon_for_torrential_rain_returns_thunderstorm():
    assert _icon_for(40.0) == "wi_thunderstorms.png"


def test_verdict_dry_says_no_rain():
    nc = _make_nowcast([0.0, 0.0, 0.0, 0.0])
    assert "無雨" in _verdict_text(nc)


def test_verdict_light_rain_says_bring_umbrella():
    nc = _make_nowcast([1.0, 0.0, 0.0, 0.0])
    assert "帶傘" in _verdict_text(nc)


def test_verdict_heavy_rain_says_heavy():
    nc = _make_nowcast([0.0, 0.0, 12.0, 0.0])
    assert "大雨" in _verdict_text(nc)


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


@patch("weather_display.lib.render.rainfall.Image.open")
def test_render_dry_nowcast_writes_verdict(mock_open, blank_image):
    """All-zero forecast should still render the 'no rain' verdict."""
    nowcast = _make_nowcast([0.0, 0.0, 0.0, 0.0])
    render_rainfall_section(blank_image, nowcast)
    mock_open.assert_not_called()
    crop = blank_image.crop(
        (SECTION_X, SECTION_Y, SECTION_X + SECTION_W, SECTION_Y + SECTION_H)
    )
    hist = crop.histogram()
    assert hist[0] > 0, "dry section should still draw text, not be blank"


@patch("weather_display.lib.render.rainfall.Image.open")
def test_render_unavailable_draws_error_line(mock_open, blank_image):
    render_rainfall_section(blank_image, None)
    crop = blank_image.crop(
        (SECTION_X, SECTION_Y, SECTION_X + SECTION_W, SECTION_Y + SECTION_H)
    )
    hist = crop.histogram()
    assert hist[0] > 0, "unavailable-section should draw the error text"
    mock_open.assert_not_called()


@patch("weather_display.lib.render.rainfall.Image.open")
def test_render_wet_nowcast_does_not_crash(mock_open, blank_image):
    """A wet nowcast exercises the icon-load + paste path."""
    fake = Image.new("1", (64, 64), 255)
    mock_open.return_value = fake

    nowcast = _make_nowcast([1.0, 0.0, 0.0, 0.0])
    render_rainfall_section(blank_image, nowcast)
    assert mock_open.called
