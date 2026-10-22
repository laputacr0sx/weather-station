"""E Ink Spectra 6 (E6) palette for the Waveshare 7.3-inch panel.

The panel stores one of six colors per pixel, packed as a 4-bit nibble:

    0 black, 1 white, 2 yellow, 3 red, 5 blue, 6 green

Nibble 4 is unused (it was orange on the older 7-color panel). Black must
not be packed as 4, or the glass paints it as the wrong color.
"""
from __future__ import annotations

from PIL import Image

EPD_WIDTH = 800
EPD_HEIGHT = 480

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

COLORS = (BLACK, WHITE, YELLOW, RED, BLUE, GREEN)

# Index 4 is a duplicate of black so nearest-color matching can pick it.
# ``frame_buffer`` collapses that index back to 0 before the bytes go out.
_PALETTE = BLACK + WHITE + YELLOW + RED + BLACK + BLUE + GREEN
_NIBBLE = {
    0: 0,
    1: 1,
    2: 2,
    3: 3,
    4: 0,
    5: 5,
    6: 6,
}


def temp_color(celsius: float | None) -> tuple[int, int, int]:
    """Blue under 26°C, green through 28°C, red from 28°C, yellow if missing."""
    if celsius is None:
        return YELLOW
    if celsius >= 28:
        return RED
    if celsius < 26:
        return BLUE
    return GREEN


def snap(image: Image.Image) -> Image.Image:
    """Nearest-color the image onto the six panel colors. No dithering."""
    indexed = _indexed(image)
    return indexed.convert("RGB")


def frame_buffer(image: Image.Image) -> list[int]:
    """Pack an 800×480 image into the 4-bit buffer the 7.3-inch E6 expects."""
    if image.size != (EPD_WIDTH, EPD_HEIGHT):
        raise ValueError(
            f"E6 image must be {EPD_WIDTH}x{EPD_HEIGHT}, got {image.size[0]}x{image.size[1]}"
        )
    raw = bytearray(_indexed(image).tobytes("raw"))
    packed = [0] * (len(raw) // 2)
    for index in range(0, len(raw), 2):
        high = _NIBBLE.get(raw[index], 0)
        low = _NIBBLE.get(raw[index + 1], 0)
        packed[index // 2] = (high << 4) | low
    return packed


def _indexed(image: Image.Image) -> Image.Image:
    palette = Image.new("P", (1, 1))
    palette.putpalette(_PALETTE + (0, 0, 0) * 249)
    return image.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE)
