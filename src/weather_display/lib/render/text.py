"""Left-to-right text runs that share a baseline across font sizes."""
from __future__ import annotations


def draw_run(draw, x, baseline, parts, fill=0):
    """Draw ``(text, font)`` parts on ``baseline``. Returns the x after the last glyph."""
    for text, font in parts:
        if text is None or text == "":
            continue
        s = str(text)
        draw.text((x, baseline), s, font=font, fill=fill, anchor="ls")
        x = draw.textbbox((x, baseline), s, font=font, anchor="ls")[2]
    return x


def draw_celsius(draw, x, baseline, number, number_font, o_font, c_font, fill=0):
    """Number and ``C`` share ``baseline``; ``o`` is a superscript at cap-height."""
    number = str(number)
    draw.text((x, baseline), number, font=number_font, fill=fill, anchor="ls")
    nb = draw.textbbox((x, baseline), number, font=number_font, anchor="ls")
    draw.text((nb[2] + 1, nb[1] + 1), "o", font=o_font, fill=fill, anchor="lt")
    c_x = nb[2] + max(4, o_font.size // 2)
    draw.text((c_x, baseline), "C", font=c_font, fill=fill, anchor="ls")
    return draw.textbbox((c_x, baseline), "C", font=c_font, anchor="ls")[2]
