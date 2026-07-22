"""
Source discovery for the editor: screenshots and locale texts.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from adobe_document_handler import LocaleHandler

from src.constants import DIRS, FILE_EXT
from src.filename_utils import resolve_text_index

logger = logging.getLogger("screenshot_cropper")

_IMAGE_EXTENSIONS = (FILE_EXT.PNG, FILE_EXT.JPG, FILE_EXT.JPEG, FILE_EXT.PSD)


@dataclass(frozen=True)
class ScreenshotEntry:
    """A previewable screenshot with its locale-text mapping."""
    path: str
    name: str
    text_index: int
    add_one: bool


def discover_screenshots(base_dir: str) -> list[ScreenshotEntry]:
    """Find screenshots in base_dir/input/screenshots with pipeline index semantics.

    PSD files are indexed first, regular images after, matching ImageProcessor
    ordering so preview text matches pipeline output.

    Args:
        base_dir: Project base directory.

    Returns:
        Screenshot entries, PSDs first; empty list when the directory is missing.
    """
    screenshots_dir = os.path.join(base_dir, DIRS.INPUT, DIRS.SCREENSHOTS)
    if not os.path.isdir(screenshots_dir):
        logger.warning(f"Screenshots directory not found: {screenshots_dir}")
        return []

    files = sorted(
        f for f in os.listdir(screenshots_dir)
        if f.lower().endswith(_IMAGE_EXTENSIONS)
        and os.path.isfile(os.path.join(screenshots_dir, f))
    )
    psd_files = [f for f in files if f.lower().endswith(FILE_EXT.PSD)]
    regular_files = [f for f in files if not f.lower().endswith(FILE_EXT.PSD)]

    def _entry(filename: str, fallback_index: int) -> ScreenshotEntry:
        text_index, add_one = resolve_text_index(filename, fallback_index)
        return ScreenshotEntry(
            path=os.path.join(screenshots_dir, filename),
            name=filename, text_index=text_index, add_one=add_one,
        )

    entries = [_entry(f, i) for i, f in enumerate(psd_files)]
    entries += [_entry(f, i + len(psd_files)) for i, f in enumerate(regular_files)]

    logger.info(f"Editor found {len(entries)} screenshots in {screenshots_dir}")
    return entries


def load_locales(base_dir: str) -> LocaleHandler | None:
    """Load the locale handler for base_dir/input/locales.

    Args:
        base_dir: Project base directory.

    Returns:
        A LocaleHandler, or None when the locales directory is missing.
    """
    locales_dir = os.path.join(base_dir, DIRS.INPUT, DIRS.LOCALES)
    if not os.path.isdir(locales_dir):
        logger.warning(f"Locales directory not found: {locales_dir}")
        return None
    return LocaleHandler(locales_dir)
