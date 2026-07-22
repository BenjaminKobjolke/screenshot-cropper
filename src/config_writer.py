"""
Config writer for the Screenshot Cropper application.

Round-trips screenshot-cropper.json: only keys managed by the editor are
updated; every other key (directories, font names, per-locale font files,
unknown sections) is preserved verbatim.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from src.models.settings import (
    BackgroundSettings,
    CropSettings,
    ExportSettings,
    OverlaySettings,
    ScreenshotMaskSettings,
    TextSettings,
)

logger = logging.getLogger("screenshot_cropper")


def _merge_crop(raw: dict[str, Any], key: str, crop: CropSettings) -> None:
    """Write a crop-shaped section (top/left/right/bottom) under the given key."""
    section = raw.setdefault(key, {})
    section.update(top=crop.top, left=crop.left, right=crop.right, bottom=crop.bottom)


def merge_settings_into_config(
    raw: dict[str, Any],
    crop: CropSettings | None,
    background: BackgroundSettings | None,
    overlay: OverlaySettings | None,
    text: TextSettings | None,
    export: ExportSettings | None,
    final_crop: CropSettings | None = None,
    screenshot_mask: ScreenshotMaskSettings | None = None,
) -> dict[str, Any]:
    """Merge settings objects into a raw config dict, preserving unmanaged keys.

    `crop` and `export` are always-present sections: None leaves them untouched.
    Optional sections (background, overlay, text, final_crop, screenshot_mask):
    None means the section is off and it is REMOVED from the config.

    Args:
        raw: Raw config dict loaded from JSON (mutated and returned).
        crop: Screenshot crop settings, or None to leave the section untouched.
        background: Background settings, or None to remove the section.
        overlay: Overlay settings, or None to remove the section.
        text: Text settings, or None to remove the section.
        export: Export settings, or None to leave the section untouched.
        final_crop: Final-image crop settings, or None to remove the section.
        screenshot_mask: Screenshot mask settings, or None to remove the section.

    Returns:
        The merged config dict.
    """
    if crop is not None:
        _merge_crop(raw, "crop", crop)

    if final_crop is not None:
        _merge_crop(raw, "final_crop", final_crop)
    else:
        raw.pop("final_crop", None)

    if screenshot_mask is not None:
        raw.setdefault("screenshot_mask", {})["file"] = screenshot_mask.file
    else:
        raw.pop("screenshot_mask", None)

    if background is not None:
        section = raw.setdefault("background", {})
        section["file"] = background.file
        section.setdefault("position", {}).update(x=background.position_x,
                                                  y=background.position_y)
        section.setdefault("size", {}).update(width=background.width, height=background.height)
    else:
        raw.pop("background", None)

    if overlay is not None:
        section = raw.setdefault("overlay", {})
        section["file"] = overlay.file
        section.setdefault("position", {}).update(x=overlay.position_x, y=overlay.position_y)
    else:
        raw.pop("overlay", None)

    if text is not None:
        text_section = raw.setdefault("text", {})
        if not text.enabled:
            text_section["enabled"] = False
        else:
            # Enabled is the default — absent key means on
            text_section.pop("enabled", None)
        font = text_section.setdefault("font", {})
        font.update(size=text.font_size, align=text.align, x=text.x, y=text.y,
                    width=text.width, height=text.height)
        font["vertical-align"] = text.vertical_align
        font["color"] = {"r": text.color[0], "g": text.color[1], "b": text.color[2]}
        if text.line_height is not None:
            font["line-height"] = text.line_height
        else:
            # Auto means absent — allows the editor to unset a previous value
            font.pop("line-height", None)
        # Only the default font file is editable; per-locale entries stay as-is
        font.setdefault("files", {})["default"] = text.font_files["default"]
    else:
        raw.pop("text", None)

    if export is not None:
        section = raw.setdefault("export", {})
        section.update(format=export.format, quality=export.quality,
                       keep_cropped=export.keep_cropped, lossless=export.lossless)

    return raw


class ConfigWriter:
    """Loads and saves the raw config JSON for round-trip editing."""

    def __init__(self, config_file: str) -> None:
        """
        Args:
            config_file: Path to screenshot-cropper.json.
        """
        self.config_file = config_file

    def load_raw(self) -> dict[str, Any]:
        """Load the raw config dict from disk.

        Returns:
            The parsed JSON object.

        Raises:
            FileNotFoundError: If the config file does not exist.
        """
        with open(self.config_file, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
        return data

    def save(self, raw: dict[str, Any]) -> None:
        """Write the raw config dict back to disk.

        Args:
            raw: Config dict to serialize.
        """
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(raw, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved configuration to: {self.config_file}")
