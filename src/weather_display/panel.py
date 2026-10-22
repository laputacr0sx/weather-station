"""Download the published dashboard image and refresh the e-paper panel.

This is the only weather-station command the Pi runs. It does not call the
Observatory or Home Assistant, and it leaves the glass alone when the
download fails or the picture has not changed.
"""
from __future__ import annotations

import hashlib
import io
import logging
import os

import requests
from PIL import Image, UnidentifiedImageError

from weather_display.lib.render.palette import EPD_HEIGHT, EPD_WIDTH
from weather_display.lib.util.display_backend import present
from weather_display.paths import state_dir

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s\t[%(levelname)s]\t%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class PanelError(Exception):
    pass


def fetch_png() -> tuple[bytes, str]:
    url = os.environ.get("DASHBOARD_URL", "").strip()
    token = os.environ.get("DASHBOARD_TOKEN", "").strip()
    if not url or not token:
        raise PanelError("DASHBOARD_URL and DASHBOARD_TOKEN are required")
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    response.raise_for_status()
    return response.content, response.headers.get("X-Dashboard-Page", "")


def show_latest() -> str:
    try:
        payload, page = fetch_png()
    except (requests.RequestException, PanelError) as exc:
        logging.warning("Dashboard image unavailable: %s", exc)
        return "skipped"
    digest = hashlib.sha256(payload).hexdigest()
    directory = state_dir()
    stamp = directory / "shown.sha256"
    try:
        previous = stamp.read_text(encoding="utf-8").strip()
    except OSError:
        previous = ""
    if previous == digest:
        logging.info("Image unchanged; leaving the panel as it is")
        return "unchanged"
    image = _open_panel_image(payload)
    if image is None:
        return "rejected"
    if page:
        logging.info("Display %s page", page)
    present(image)
    directory.mkdir(parents=True, exist_ok=True)
    stamp.write_text(digest + "\n", encoding="utf-8")
    return "shown"


def _open_panel_image(payload: bytes) -> Image.Image | None:
    try:
        image = Image.open(io.BytesIO(payload)).convert("RGB")
    except (OSError, UnidentifiedImageError):
        logging.warning("Dashboard response is not a PNG")
        return None
    if image.size != (EPD_WIDTH, EPD_HEIGHT):
        logging.warning("Dashboard image is %sx%s", image.size[0], image.size[1])
        return None
    return image


def main() -> None:
    show_latest()


if __name__ == "__main__":
    main()
