"""
Unit tests for EditorState (Qt-free editor core).
"""
from __future__ import annotations

import json

from src.config import ConfigHandler
from src.config_writer import ConfigWriter
from src.editor.state import EditorState
from src.models.settings import CropSettings

CONFIG = {
    "crop": {"top": 0, "left": 40, "right": 10, "bottom": 95},
    "background": {
        "file": "bg.png",
        "position": {"x": 306, "y": 795},
        "size": {"width": 928, "height": 2158},
    },
    "overlay": {"file": "overlay.png", "position": {"x": 0, "y": 0}},
    "export": {"format": "webp", "lossless": True},
    "custom_key": "keep me",
}


def _make_state(tmp_path) -> EditorState:
    config_file = tmp_path / "screenshot-cropper.json"
    config_file.write_text(json.dumps(CONFIG), encoding="utf-8")
    return EditorState(
        base_dir=str(tmp_path),
        config_handler=ConfigHandler(str(config_file)),
        config_writer=ConfigWriter(str(config_file)),
    )


def test_state_loads_initial_settings(tmp_path):
    state = _make_state(tmp_path)
    assert state.crop == CropSettings(top=0, left=40, right=10, bottom=95)
    assert state.background is not None
    assert state.background.width == 928
    assert state.overlay is not None
    assert state.text is None
    assert state.export.format == "webp"


def test_state_build_compositor(tmp_path):
    state = _make_state(tmp_path)
    compositor = state.build_compositor()
    assert compositor.crop_settings == state.crop
    assert compositor.background_settings == state.background
    assert compositor.base_dir == str(tmp_path)
    assert compositor.text_processor is None


def test_state_final_crop_defaults_to_zeros_and_is_not_written(tmp_path):
    """Absent final_crop: state exposes zeros; saving zeros must not add the section."""
    state = _make_state(tmp_path)
    assert state.final_crop == CropSettings(top=0, left=0, right=0, bottom=0)
    state.save()
    raw = json.loads((tmp_path / "screenshot-cropper.json").read_text(encoding="utf-8"))
    assert "final_crop" not in raw


def test_state_final_crop_saved_when_nonzero(tmp_path):
    state = _make_state(tmp_path)
    state.final_crop = CropSettings(top=0, left=0, right=0, bottom=120)
    state.save()
    raw = json.loads((tmp_path / "screenshot-cropper.json").read_text(encoding="utf-8"))
    assert raw["final_crop"]["bottom"] == 120


def test_state_final_crop_kept_when_section_exists_and_zeroed(tmp_path):
    """Existing final_crop section stays managed even when edited back to zeros."""
    config_file = tmp_path / "screenshot-cropper.json"
    config = dict(CONFIG)
    config["final_crop"] = {"top": 10}
    config_file.write_text(json.dumps(config), encoding="utf-8")
    state = EditorState(
        base_dir=str(tmp_path),
        config_handler=ConfigHandler(str(config_file)),
        config_writer=ConfigWriter(str(config_file)),
    )
    assert state.final_crop.top == 10
    state.final_crop = CropSettings(top=0)
    state.save()
    raw = json.loads(config_file.read_text(encoding="utf-8"))
    assert raw["final_crop"] == {"top": 0, "left": 0, "right": 0, "bottom": 0}


def test_state_save_roundtrip_preserves_unknown_keys(tmp_path):
    state = _make_state(tmp_path)
    state.crop = CropSettings(top=1, left=2, right=3, bottom=4)
    state.save()

    raw = json.loads((tmp_path / "screenshot-cropper.json").read_text(encoding="utf-8"))
    assert raw["crop"] == {"top": 1, "left": 2, "right": 3, "bottom": 4}
    assert raw["custom_key"] == "keep me"
    assert raw["background"]["size"]["width"] == 928
