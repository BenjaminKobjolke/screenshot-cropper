"""
Unit tests for config round-trip writing.
"""
from __future__ import annotations

import json

import pytest

from src.config import ConfigHandler
from src.config_writer import ConfigWriter, merge_settings_into_config
from src.models.settings import (
    BackgroundSettings,
    CropSettings,
    ExportSettings,
    OverlaySettings,
    ScreenshotMaskSettings,
    TextSettings,
)

RAW = {
    "export": {"format": "webp", "lossless": True},
    "crop": {"top": 0, "left": 40, "right": 10, "bottom": 95},
    "background": {
        "file": "bg.png",
        "position": {"x": 306, "y": 795},
        "size": {"width": 928, "height": 2158},
    },
    "overlay": {"file": "overlay.png", "position": {"x": 0, "y": 0}},
    "text": {
        "font": {
            "names": {"default": "NotoSans-Regular", "ar": "DroidSans-Regular-Arabic"},
            "files": {"default": "NotoSans-Bold.ttf", "ar": "DroidSans-Bold_ar.ttf"},
            "size": 100,
            "align": "center",
            "vertical-align": "middle",
            "x": 50,
            "y": 0,
            "width": 1450,
            "height": 650,
            "color": {"r": 255, "g": 255, "b": 255},
        }
    },
    "directories": {"screenshots": "shots", "locales": "loc", "output": "out"},
    "custom_unknown_key": {"nested": [1, 2, 3]},
}


def _settings():
    crop = CropSettings(top=1, left=2, right=3, bottom=4)
    background = BackgroundSettings(file="new_bg.png", position_x=10, position_y=20,
                                    width=500, height=600)
    overlay = OverlaySettings(file="new_overlay.png", position_x=7, position_y=8)
    text = TextSettings(
        font_files={"default": "Other.ttf", "ar": "DroidSans-Bold_ar.ttf"},
        font_size=48, align="left", x=5, y=6, width=700, height=200,
        vertical_align="bottom", color=(1, 2, 3),
        font_names={"default": "NotoSans-Regular", "ar": "DroidSans-Regular-Arabic"},
    )
    export = ExportSettings(format="png", quality=80, keep_cropped=True, lossless=False)
    return crop, background, overlay, text, export


def test_merge_updates_managed_keys_and_preserves_unknown():
    raw = json.loads(json.dumps(RAW))
    crop, background, overlay, text, export = _settings()
    merged = merge_settings_into_config(raw, crop, background, overlay, text, export)

    assert merged["crop"] == {"top": 1, "left": 2, "right": 3, "bottom": 4}
    assert merged["background"]["file"] == "new_bg.png"
    assert merged["background"]["position"] == {"x": 10, "y": 20}
    assert merged["background"]["size"] == {"width": 500, "height": 600}
    assert merged["overlay"] == {"file": "new_overlay.png", "position": {"x": 7, "y": 8}}
    font = merged["text"]["font"]
    assert font["size"] == 48
    assert font["align"] == "left"
    assert font["vertical-align"] == "bottom"
    assert (font["x"], font["y"], font["width"], font["height"]) == (5, 6, 700, 200)
    assert font["color"] == {"r": 1, "g": 2, "b": 3}
    assert font["files"]["default"] == "Other.ttf"
    assert merged["export"] == {"format": "png", "quality": 80,
                                "keep_cropped": True, "lossless": False}

    # Unknown/unmanaged keys preserved verbatim
    assert merged["directories"] == RAW["directories"]
    assert merged["custom_unknown_key"] == RAW["custom_unknown_key"]
    assert font["names"] == RAW["text"]["font"]["names"]
    assert font["files"]["ar"] == "DroidSans-Bold_ar.ttf"


def test_merge_skips_none_sections():
    raw = {"crop": {"top": 9}}
    merged = merge_settings_into_config(raw, CropSettings(top=1), None, None, None, None)
    assert merged["crop"]["top"] == 1
    assert "background" not in merged
    assert "overlay" not in merged
    assert "text" not in merged
    assert "final_crop" not in merged


def test_merge_none_removes_disabled_sections():
    """None for an optional section means 'section off' — removed from the config."""
    raw = json.loads(json.dumps(RAW))
    raw["screenshot_mask"] = {"file": "old.png"}
    merged = merge_settings_into_config(raw, CropSettings(top=1), None, None, None, None)
    assert "background" not in merged
    assert "overlay" not in merged
    assert "text" not in merged
    assert "screenshot_mask" not in merged
    # Unknown keys still preserved
    assert merged["custom_unknown_key"] == RAW["custom_unknown_key"]


def test_merge_writes_line_height():
    raw = json.loads(json.dumps(RAW))
    crop, background, overlay, text, export = _settings()
    text.line_height = 1.5
    merged = merge_settings_into_config(raw, crop, background, overlay, text, export)
    assert merged["text"]["font"]["line-height"] == 1.5


def test_merge_removes_line_height_when_none():
    raw = json.loads(json.dumps(RAW))
    raw["text"]["font"]["line-height"] = 1.3
    crop, background, overlay, text, export = _settings()
    assert text.line_height is None
    merged = merge_settings_into_config(raw, crop, background, overlay, text, export)
    assert "line-height" not in merged["text"]["font"]


def test_merge_writes_enabled_only_when_false():
    raw = json.loads(json.dumps(RAW))
    crop, background, overlay, text, export = _settings()
    text.enabled = False
    merged = merge_settings_into_config(raw, crop, background, overlay, text, export)
    assert merged["text"]["enabled"] is False

    text.enabled = True
    merged = merge_settings_into_config(merged, crop, background, overlay, text, export)
    assert "enabled" not in merged["text"]


def test_merge_writes_screenshot_mask():
    merged = merge_settings_into_config(
        {}, None, None, None, None, None,
        screenshot_mask=ScreenshotMaskSettings(file="mask.png"),
    )
    assert merged["screenshot_mask"] == {"file": "mask.png"}


def test_merge_none_mask_removes_section():
    raw = {"screenshot_mask": {"file": "old.png"}}
    merged = merge_settings_into_config(raw, None, None, None, None, None)
    assert "screenshot_mask" not in merged


def test_merge_writes_final_crop():
    merged = merge_settings_into_config(
        {}, None, None, None, None, None, final_crop=CropSettings(top=5, bottom=7)
    )
    assert merged["final_crop"] == {"top": 5, "left": 0, "right": 0, "bottom": 7}


def test_writer_roundtrip_readable_by_config_handler(tmp_path):
    """Written config must load back into identical settings via ConfigHandler."""
    config_file = tmp_path / "screenshot-cropper.json"
    config_file.write_text(json.dumps(RAW), encoding="utf-8")

    writer = ConfigWriter(str(config_file))
    raw = writer.load_raw()
    crop, background, overlay, text, export = _settings()
    writer.save(merge_settings_into_config(raw, crop, background, overlay, text, export))

    handler = ConfigHandler(str(config_file))
    assert handler.get_crop_settings() == crop
    assert handler.get_background_settings() == background
    assert handler.get_overlay_settings() == overlay
    assert handler.get_text_settings() == text
    assert handler.get_export_settings() == export


def test_writer_load_raw_missing_file(tmp_path):
    writer = ConfigWriter(str(tmp_path / "nope.json"))
    with pytest.raises(FileNotFoundError):
        writer.load_raw()
