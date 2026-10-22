"""The systemd service is a template; install.sh fills in user and paths."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEMPLATE = REPO / "deploy" / "systemd" / "weather-display.service.in"


def test_service_template_has_placeholders_not_pi_user():
    text = TEMPLATE.read_text(encoding="utf-8")
    assert "__USER__" in text
    assert "__REPO__" in text
    assert "__PYTHON__" in text
    assert "EnvironmentFile=-__REPO__/.env" in text
    assert "StateDirectory=weather-display" in text
    assert "weather_display.panel" in text
    assert "weather_display.run" not in text
    assert "User=pi" not in text
    assert "%h/weather-station" not in text


def test_lifebook_units_render_and_serve():
    publish = (REPO / "deploy" / "systemd" / "weather-publish.service.in").read_text(encoding="utf-8")
    serve = (REPO / "deploy" / "systemd" / "weather-serve.service.in").read_text(encoding="utf-8")
    assert "weather_display.publish" in publish
    assert "weather_display.serve" in serve
    assert "Type=simple" in serve
    assert "__USER__" in publish and "__USER__" in serve
