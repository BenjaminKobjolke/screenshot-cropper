"""
Unit tests for text line spacing (constant line advance regardless of glyphs).
"""
from __future__ import annotations

import os

import pytest
from PIL import Image

from src.models.settings import TextSettings
from src.text_processor import TextProcessor

FONT_FILE = "NotoSans-Bold.ttf"


def _band_tops(img: Image.Image) -> list[int]:
    """Return the starting y of each horizontal band containing non-black pixels."""
    gray = img.convert("L")
    width, height = gray.size
    row_has_ink = [
        any(gray.getpixel((x, y)) > 30 for x in range(width))
        for y in range(height)
    ]
    tops = [
        y for y in range(height)
        if row_has_ink[y] and (y == 0 or not row_has_ink[y - 1])
    ]
    return tops


@pytest.fixture
def processor() -> TextProcessor:
    if not os.path.isfile(os.path.join("fonts", FONT_FILE)):
        pytest.skip(f"fonts/{FONT_FILE} not available")
    return TextProcessor(TextSettings(
        font_files={"default": FONT_FILE},
        font_size=60, align="left", x=10, y=10, width=500, height=400,
        vertical_align="top", color=(255, 255, 255),
    ))


def test_line_advance_is_glyph_independent(processor):
    """'es' (x-height only glyphs) must not shrink the advance to the next line.

    Lines 1/3/4 are identical 'Ag'; band tops of identical glyphs cancel out
    glyph-shape offsets, so: top(Ag3) - top(Ag1) must equal exactly two line
    advances, and top(Ag4) - top(Ag3) exactly one.
    """
    img = Image.new("RGB", (520, 500), (0, 0, 0))
    processor.draw_text(img, "Ag\nes\nAg\nAg")

    tops = _band_tops(img)
    assert len(tops) == 4, f"expected 4 text bands, found tops at {tops}"
    two_advances_over_es = tops[2] - tops[0]
    one_advance = tops[3] - tops[2]
    assert abs(two_advances_over_es - 2 * one_advance) <= 2, (
        f"uneven line advance: Ag→es→Ag spans {two_advances_over_es}px, "
        f"but Ag→Ag advance is {one_advance}px"
    )


def test_line_height_multiplier_controls_advance():
    """line_height=2.0 at size 60 → identical lines exactly 120px apart."""
    if not os.path.isfile(os.path.join("fonts", FONT_FILE)):
        pytest.skip(f"fonts/{FONT_FILE} not available")
    processor = TextProcessor(TextSettings(
        font_files={"default": FONT_FILE},
        font_size=60, align="left", x=10, y=10, width=500, height=460,
        vertical_align="top", color=(255, 255, 255), line_height=2.0,
    ))
    img = Image.new("RGB", (520, 480), (0, 0, 0))
    processor.draw_text(img, "Ag\nAg\nAg")

    tops = _band_tops(img)
    assert len(tops) == 3, f"expected 3 text bands, found tops at {tops}"
    assert abs((tops[1] - tops[0]) - 120) <= 1
    assert abs((tops[2] - tops[1]) - 120) <= 1


def test_single_line_renders(processor):
    img = Image.new("RGB", (520, 420), (0, 0, 0))
    processor.draw_text(img, "Hello")
    assert len(_band_tops(img)) == 1


def test_disabled_text_draws_nothing():
    if not os.path.isfile(os.path.join("fonts", FONT_FILE)):
        pytest.skip(f"fonts/{FONT_FILE} not available")
    processor = TextProcessor(TextSettings(
        font_files={"default": FONT_FILE},
        font_size=60, align="left", x=10, y=10, width=500, height=400,
        vertical_align="top", color=(255, 255, 255), enabled=False,
    ))
    img = Image.new("RGB", (520, 420), (0, 0, 0))
    result = processor.draw_text(img, "Hello")
    assert _band_tops(result) == []
