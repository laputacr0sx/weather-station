"""Tests for EPD vs preview selection."""
from __future__ import annotations

from unittest.mock import MagicMock

from weather_display.lib.util import display_backend as backend


def test_desktop_defaults_to_preview(monkeypatch):
    monkeypatch.delenv("WEATHER_DISPLAY_OUTPUT", raising=False)
    monkeypatch.setattr(backend, "_pi_model", lambda: None)
    assert backend.use_epd() is False


def test_pi_zero_2_w_uses_epd(monkeypatch):
    monkeypatch.delenv("WEATHER_DISPLAY_OUTPUT", raising=False)
    monkeypatch.setattr(backend, "_pi_model", lambda: "Raspberry Pi Zero 2 W Rev 1.0")
    assert backend.use_epd() is True


def test_any_raspberry_pi_uses_epd(monkeypatch):
    monkeypatch.delenv("WEATHER_DISPLAY_OUTPUT", raising=False)
    monkeypatch.setattr(backend, "_pi_model", lambda: "Raspberry Pi 4 Model B Rev 1.4")
    assert backend.use_epd() is True


def test_env_preview_overrides_pi(monkeypatch):
    monkeypatch.setenv("WEATHER_DISPLAY_OUTPUT", "preview")
    monkeypatch.setattr(backend, "_pi_model", lambda: "Raspberry Pi Zero 2 W Rev 1.0")
    assert backend.use_epd() is False


def test_env_epd_overrides_desktop(monkeypatch):
    monkeypatch.setenv("WEATHER_DISPLAY_OUTPUT", "epd")
    monkeypatch.setattr(backend, "_pi_model", lambda: None)
    assert backend.use_epd() is True


def test_present_preview_calls_show_not_epd(monkeypatch):
    monkeypatch.setattr(backend, "use_epd", lambda: False)
    epd = MagicMock()
    monkeypatch.setattr(backend, "_present_epd", epd)
    image = MagicMock()
    backend.present(image)
    image.show.assert_called_once_with()
    epd.assert_not_called()


def test_present_epd_skips_show(monkeypatch):
    monkeypatch.setattr(backend, "use_epd", lambda: True)
    epd = MagicMock()
    monkeypatch.setattr(backend, "_present_epd", epd)
    image = MagicMock()
    backend.present(image)
    epd.assert_called_once_with(image)
    image.show.assert_not_called()
