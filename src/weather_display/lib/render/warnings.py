"""Inverted warning strip between the 5-day forecast and the rainfall band."""
from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageOps

from weather_display import PIC_DIR
from weather_display.assest.font.cubic_font import font14, font24
from weather_display.lib.util.warnings import (
    CHIP_ICON_SIZE,
    CHIP_ICON_TEXT_GAP,
    STRIP_PAD,
    PackedStrip,
    WarningStrip,
    pack_warning_strip,
)

# Inset to match the rainfall frame; white gap below so the bar is not flush
# on the nowcast. Height leaves ~7px above/below the 36px icons.
STRIP_X = 8
STRIP_Y = 232
STRIP_W = 784
STRIP_H = 50
STRIP_GAP_BELOW = 6


def _measure(font, text: str) -> int:
    box = font.getbbox(text)
    return box[2] - box[0]


def layout_strip(strip: WarningStrip) -> PackedStrip:
    return pack_warning_strip(
        strip.chips,
        strip.tip,
        measure_label=lambda s: _measure(font24, s),
        measure_tip=lambda s: _measure(font14, s),
        icon_size=CHIP_ICON_SIZE,
        origin_x=STRIP_X + STRIP_PAD,
        inner_width=STRIP_W - 2 * STRIP_PAD,
    )


def _load_icon(filename: str, size: int) -> Image.Image | None:
    path = os.path.join(PIC_DIR, filename)
    try:
        icon = Image.open(path).convert("1")
    except FileNotFoundError:
        return None
    icon = icon.resize((size, size), Image.Resampling.NEAREST)
    # Stored black-on-white; the strip is black, so invert to white ink.
    return ImageOps.invert(icon.convert("L")).convert("1")


def render_warning_strip(image: Image.Image, strip: WarningStrip) -> bool:
    """Draw the inverted strip. Returns True when anything was drawn.

    Callers compact the rainfall band when this returns True so the strip
    does not collide with the nowcast frame.
    """
    if not strip.active:
        return False

    packed = layout_strip(strip)
    draw = ImageDraw.Draw(image)
    y = STRIP_Y
    draw.rectangle(
        (STRIP_X, y, STRIP_X + STRIP_W - 1, y + STRIP_H - 1),
        fill=0,
    )

    icon_y = y + (STRIP_H - CHIP_ICON_SIZE) // 2
    mid_y = y + STRIP_H // 2
    for placed in packed.chips:
        icon = _load_icon(placed.chip.icon, placed.icon_size)
        if icon is not None:
            image.paste(icon, (placed.x, icon_y))
        if placed.show_label:
            text_x = placed.x + placed.icon_size + CHIP_ICON_TEXT_GAP
            draw.text(
                (text_x, mid_y),
                placed.chip.label,
                font=font24,
                fill=255,
                anchor="lm",
            )

    if packed.tip and packed.tip_x is not None:
        draw.text(
            (packed.tip_x, mid_y),
            packed.tip,
            font=font14,
            fill=255,
            anchor="lm",
        )

    return True
