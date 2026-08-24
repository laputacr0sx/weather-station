"""Tests for :mod:`weather_display.assest.font.cubic_font`.

The fonts are module-level singletons, so loading the module must succeed no
matter what the current working directory is. This is also a prerequisite for
importing anything else in ``weather_display``: ``__init__.py`` imports
``cubic_font`` at package import time, so a broken font path makes the entire
package unimportable.
"""
import subprocess
import sys
from pathlib import Path

from PIL import ImageFont

SRC_DIR = Path(__file__).resolve().parents[1] / "src"


def test_font_module_loads_from_any_cwd():
    """Importing the font module must not depend on the working directory.

    Runs in a fresh interpreter from the repo root (not the font directory).
    With the old ``./Cubic_11.ttf`` path this crashed with
    ``OSError: cannot open resource``.
    """
    code = "from weather_display.assest.font import cubic_font; print(cubic_font.CUBIC_FONT_PATH)"
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=SRC_DIR.parent,
        env={"PYTHONPATH": str(SRC_DIR), **_base_env()},
    )
    assert result.returncode == 0, f"import failed:\n{result.stderr}"
    assert "Cubic_11.ttf" in result.stdout


def test_fonts_are_valid_truetype():
    """Each module-level font must be a usable FreeType font instance."""
    from weather_display.assest.font import cubic_font

    fonts = [
        cubic_font.font80,
        cubic_font.font64,
        cubic_font.font48,
        cubic_font.font40,
        cubic_font.font32,
        cubic_font.font24,
        cubic_font.font18,
        cubic_font.font14,
        cubic_font.font12,
    ]
    for f in fonts:
        assert isinstance(f, ImageFont.FreeTypeFont)


def test_font_path_is_module_relative():
    """CUBIC_FONT_PATH points inside the package, not at the CWD."""
    from weather_display.assest.font import cubic_font

    path = Path(cubic_font.CUBIC_FONT_PATH)
    assert path.is_absolute(), "font path must be absolute, not CWD-relative"
    assert path.exists(), f"font file not found at {path}"


def _base_env():
    """Strip PYTHONPATH from the inherited environment for a clean run."""
    import os

    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return env
