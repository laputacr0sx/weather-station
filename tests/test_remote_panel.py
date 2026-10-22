import io
import threading
from datetime import datetime, timedelta

import pytest
import requests
from PIL import Image

from weather_display import panel
from weather_display.publish import publish_directory
from weather_display.refresh import GlassFacts
from weather_display.serve import make_server, tokens_match


def _png(size=(800, 480), color=(255, 0, 0)) -> bytes:
    image = Image.new("RGB", size, color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _rendered(now_color, forecast_color, facts):
    return (
        Image.new("RGB", (800, 480), now_color),
        Image.new("RGB", (800, 480), forecast_color),
        datetime(2026, 10, 23, 5, 0),
        facts,
    )


def test_publish_waits_out_a_quiet_hour_then_flips(tmp_path, monkeypatch):
    quiet = GlassFacts("quiet")
    frames = [
        _rendered((255, 0, 0), (0, 0, 255), quiet),
        _rendered((255, 0, 0), (0, 0, 255), quiet),
        _rendered((255, 0, 0), (0, 0, 255), quiet),
        _rendered((0, 180, 0), (0, 180, 0), GlassFacts("rain")),
    ]
    monkeypatch.setattr("weather_display.publish.render_pair", lambda: frames.pop(0))
    morning = datetime(2026, 10, 23, 5, 0)
    assert publish_directory(tmp_path, morning) == "now"
    with Image.open(tmp_path / "current.png") as image:
        assert image.getpixel((10, 10)) == (255, 0, 0)
    assert publish_directory(tmp_path, morning + timedelta(minutes=15)) == "kept"
    with Image.open(tmp_path / "current.png") as image:
        assert image.getpixel((10, 10)) == (255, 0, 0)
    assert (tmp_path / "page").read_text(encoding="utf-8").strip() == "now"
    assert publish_directory(tmp_path, morning + timedelta(hours=1)) == "forecast"
    with Image.open(tmp_path / "current.png") as image:
        assert image.getpixel((10, 10)) == (0, 0, 255)
    assert publish_directory(tmp_path, morning + timedelta(hours=1, minutes=15)) == "forecast"
    with Image.open(tmp_path / "current.png") as image:
        assert image.getpixel((10, 10)) == (0, 180, 0)
    assert (tmp_path / "page").read_text(encoding="utf-8").strip() == "forecast"


def test_failed_render_keeps_the_previous_image(tmp_path, monkeypatch):
    current = tmp_path / "current.png"
    current.write_bytes(b"old")

    def boom():
        raise RuntimeError("observatory down")

    monkeypatch.setattr("weather_display.publish.render_pair", boom)
    with pytest.raises(RuntimeError):
        publish_directory(tmp_path, datetime(2026, 10, 23, 5, 0))
    assert current.read_bytes() == b"old"
    assert not (tmp_path / "page").exists()


def test_token_must_match_exactly():
    assert tokens_match("Bearer secret", "secret")
    assert not tokens_match("Bearer secreT", "secret")
    assert not tokens_match("", "secret")


def test_image_api_checks_the_token(tmp_path):
    image = Image.new("RGB", (800, 480), (255, 255, 0))
    image.save(tmp_path / "current.png")
    (tmp_path / "current.page").write_text("forecast\n", encoding="utf-8")
    server = make_server(tmp_path, "secret", host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        assert requests.get(f"{base}/health", timeout=2).status_code == 200
        assert requests.get(f"{base}/current.png", timeout=2).status_code == 401
        response = requests.get(
            f"{base}/current.png",
            headers={"Authorization": "Bearer secret"},
            timeout=2,
        )
        assert response.status_code == 200
        assert response.headers["X-Dashboard-Page"] == "forecast"
        assert response.content.startswith(b"\x89PNG")
    finally:
        server.shutdown()
        server.server_close()


def test_panel_shows_a_new_image_once(tmp_path, monkeypatch):
    payload = _png()
    monkeypatch.setenv("STATE_DIRECTORY", str(tmp_path))
    shown = []
    monkeypatch.setattr(panel, "fetch_png", lambda: (payload, "now"))
    monkeypatch.setattr(panel, "present", lambda image: shown.append(image.size))
    assert panel.show_latest() == "shown"
    assert panel.show_latest() == "unchanged"
    assert shown == [(800, 480)]


def test_panel_leaves_the_glass_alone_when_the_server_is_down(tmp_path, monkeypatch):
    monkeypatch.setenv("STATE_DIRECTORY", str(tmp_path))

    def boom():
        raise requests.ConnectionError("down")

    monkeypatch.setattr(panel, "fetch_png", boom)
    shown = []
    monkeypatch.setattr(panel, "present", lambda image: shown.append(image))
    assert panel.show_latest() == "skipped"
    assert shown == []


def test_panel_rejects_the_wrong_size(tmp_path, monkeypatch):
    monkeypatch.setenv("STATE_DIRECTORY", str(tmp_path))
    monkeypatch.setattr(panel, "fetch_png", lambda: (_png(size=(4, 4)), ""))
    shown = []
    monkeypatch.setattr(panel, "present", lambda image: shown.append(image))
    assert panel.show_latest() == "rejected"
    assert shown == []
    assert not (tmp_path / "shown.sha256").exists()
