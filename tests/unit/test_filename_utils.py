"""
Unit tests for filename utilities (text index resolution).
"""
from __future__ import annotations

from src.filename_utils import extract_screenshot_number, resolve_text_index


def test_extract_screenshot_number():
    assert extract_screenshot_number("7.png") == 7
    assert extract_screenshot_number("screenshot_07.psd") == 7
    assert extract_screenshot_number("cover.png") is None


def test_resolve_text_index_numbered_file():
    """Numbered file: index = number, add_one False (mirrors image_processor semantics)."""
    assert resolve_text_index("07.psd", fallback_index=3) == (7, False)


def test_resolve_text_index_unnumbered_file():
    """Unnumbered file: positional fallback index, add_one True."""
    assert resolve_text_index("cover.png", fallback_index=3) == (3, True)
