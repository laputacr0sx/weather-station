from PIL import Image

from weather_display.lib.render.palette import (
    BLACK,
    BLUE,
    GREEN,
    RED,
    WHITE,
    YELLOW,
    frame_buffer,
    temp_color,
)


def _solid(color):
    return Image.new("RGB", (800, 480), color)


def test_temp_color_bands():
    assert temp_color(None) == YELLOW
    assert temp_color(24.7) == BLUE
    assert temp_color(25.9) == BLUE
    assert temp_color(26.0) == GREEN
    assert temp_color(27.6) == GREEN
    assert temp_color(28.0) == RED
    assert temp_color(28.6) == RED


def test_frame_buffer_packs_spectra6_nibbles():
    assert frame_buffer(_solid(BLACK))[0] == 0x00
    assert frame_buffer(_solid(WHITE))[0] == 0x11
    assert frame_buffer(_solid(YELLOW))[0] == 0x22
    assert frame_buffer(_solid(RED))[0] == 0x33
    assert frame_buffer(_solid(BLUE))[0] == 0x55
    assert frame_buffer(_solid(GREEN))[0] == 0x66
    assert len(frame_buffer(_solid(WHITE))) == 800 * 480 // 2


def test_black_is_not_packed_as_the_unused_orange_nibble():
    packed = frame_buffer(_solid(BLACK))
    assert all(byte == 0x00 for byte in packed)
    assert all((byte >> 4) != 4 and (byte & 0x0F) != 4 for byte in packed)
