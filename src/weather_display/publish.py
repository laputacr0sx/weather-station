"""Draw both dashboard pages on the Lifebook and publish the one to show.

The Pi never runs this. A timer calls it, the image server reads the files
it leaves, and the panel only downloads ``current.png``.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

from weather_display.paths import state_dir
from weather_display.refresh import GlassFacts, decide_refresh, load_refresh, save_refresh
from weather_display.run import choose_page, render_pair

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s\t[%(levelname)s]\t%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def publish_directory(directory: Path, when: datetime | None = None) -> str:
    """Render both pages and point ``current.png`` at the page to display.

    A failed fetch leaves the previous image in place. A successful fetch
    still keeps that image when the refresh policy says the panel should
    wait. The page flips only on the slow interval, not on an urgent update.
    """
    rendered = render_pair()
    now_image, forecast_image, rendered_at = rendered[:3]
    facts = rendered[3] if len(rendered) >= 4 else GlassFacts("quiet")
    moment = when or rendered_at
    refreshed_at, attention, warnings = load_refresh(directory / "refresh")
    kind = decide_refresh(moment, refreshed_at, attention, warnings, facts)
    if kind == "keep":
        logging.info("Keeping the glass image (%s)", facts.attention)
        return "kept"
    directory.mkdir(parents=True, exist_ok=True)
    page = choose_page(directory / "page", moment, flip=kind != "urgent")
    _atomic_png(now_image, directory / "now.png")
    _atomic_png(forecast_image, directory / "forecast.png")
    chosen = forecast_image if page == "forecast" else now_image
    _atomic_png(chosen, directory / "current.png")
    (directory / "current.page").write_text(page + "\n", encoding="utf-8")
    save_refresh(directory / "refresh", moment, facts)
    logging.info("Published %s page (%s) to %s", page, kind, directory)
    return page


def _atomic_png(image, path: Path) -> None:
    temporary = path.with_name(path.name + ".tmp")
    image.save(temporary, format="PNG")
    os.replace(temporary, path)


def main() -> None:
    try:
        publish_directory(state_dir())
    except Exception:
        logging.error("Render failed; keeping the previous image", exc_info=True)


if __name__ == "__main__":
    main()
