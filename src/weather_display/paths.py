"""Directories shared by the publisher, the image server, and the panel."""
from __future__ import annotations

import os
from pathlib import Path


def state_dir() -> Path:
    """Where the current PNG and the last-shown hash live.

    Systemd sets ``STATE_DIRECTORY``. ``DASHBOARD_DIR`` overrides it for a
    manual run. The Pi and the Lifebook each have their own copy.
    """
    override = os.environ.get("DASHBOARD_DIR", "").strip()
    if override:
        return Path(override)
    state = os.environ.get("STATE_DIRECTORY", "").split(":", 1)[0].strip()
    if state:
        return Path(state)
    return Path("var/weather-display")
