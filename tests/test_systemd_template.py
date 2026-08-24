"""The systemd service is a template; install.sh fills in user and paths."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEMPLATE = REPO / "deploy" / "systemd" / "weather-display.service.in"


def test_service_template_has_placeholders_not_pi_user():
    text = TEMPLATE.read_text(encoding="utf-8")
    assert "__USER__" in text
    assert "__REPO__" in text
    assert "__PYTHON__" in text
    assert "User=pi" not in text
    assert "%h/weather-station" not in text
