"""
Filename utility functions for the Screenshot Cropper application.
"""
from __future__ import annotations

import os
import re


def extract_screenshot_number(filename: str) -> int | None:
    """Extract the screenshot number from a filename.

    Supports various filename patterns:
    - Purely numeric: "7.png" -> 7
    - With prefix: "screenshot_07.psd" -> 7
    - With prefix (no padding): "screenshot_7.jpg" -> 7

    Args:
        filename: The filename (with or without extension).

    Returns:
        The extracted screenshot number, or None if no number found.
    """
    # Remove extension if present
    name, _ = os.path.splitext(filename)

    # First, check if the entire name is a number (e.g., "7")
    if name.isdigit():
        return int(name)

    # Try to find numbers in the filename using regex
    # This will match patterns like "screenshot_07" or "img_123"
    match = re.search(r"(\d+)", name)
    if match:
        return int(match.group(1))

    return None
