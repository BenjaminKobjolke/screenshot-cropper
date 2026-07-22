"""
Integration smoke test for the PySide6 editor (offscreen).
"""
from __future__ import annotations

import json
import os

import pytest
from PIL import Image

pytest.importorskip("PySide6")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from src.editor.main_window import MainWindow  # noqa: E402
from src.editor.recents import RecentProjects  # noqa: E402

CONFIG = {
    "crop": {"top": 0, "left": 4, "right": 2, "bottom": 6},
    "background": {
        "file": "bg.png",
        "position": {"x": 5, "y": 5},
        "size": {"width": 30, "height": 40},
    },
    "overlay": {"file": "overlay.png", "position": {"x": 0, "y": 0}},
    "screenshot_mask": {"file": "mask.png"},
    "export": {"format": "png"},
    "custom_key": "keep me",
}


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def project(tmp_path):
    (tmp_path / "input" / "screenshots").mkdir(parents=True)
    (tmp_path / "input" / "locales").mkdir(parents=True)
    Image.new("RGB", (100, 80), (10, 20, 30)).save(tmp_path / "input" / "bg.png")
    Image.new("RGBA", (100, 80), (0, 0, 0, 0)).save(tmp_path / "input" / "overlay.png")
    Image.new("RGBA", (36, 36), (0, 0, 0, 0)).save(tmp_path / "input" / "mask.png")
    Image.new("RGB", (40, 40), (200, 100, 50)).save(
        tmp_path / "input" / "screenshots" / "00.png"
    )
    (tmp_path / "input" / "locales" / "en.json").write_text(
        json.dumps({"Text_1": "Hello"}), encoding="utf-8"
    )
    config_file = tmp_path / "screenshot-cropper.json"
    config_file.write_text(json.dumps(CONFIG), encoding="utf-8")
    return tmp_path


def test_editor_starts_without_config(qapp, tmp_path):
    """Missing screenshot-cropper.json must not crash — empty window, save is a no-op."""
    recents = RecentProjects(str(tmp_path / "recents.json"))
    window = MainWindow(str(tmp_path), str(tmp_path / "screenshot-cropper.json"),
                        recents=recents)
    assert window.state is None
    window.save()  # must not raise
    window.close()


def test_optional_sections_can_be_added_and_removed(qapp, tmp_path):
    """Unconfigured sections show unchecked panels; checking adds them on save,
    unchecking a configured section removes it."""
    (tmp_path / "input").mkdir()
    Image.new("RGB", (100, 80)).save(tmp_path / "input" / "bg.png")
    Image.new("RGBA", (30, 30), (0, 0, 0, 0)).save(tmp_path / "input" / "the_mask.png")
    config_file = tmp_path / "screenshot-cropper.json"
    config_file.write_text(json.dumps({
        "crop": {"top": 1},
        "overlay": {"file": "bg.png", "position": {"x": 0, "y": 0}},
    }), encoding="utf-8")

    window = MainWindow(str(tmp_path), str(config_file),
                        recents=RecentProjects(str(tmp_path / "recents.json")))
    # Unconfigured sections: panels exist, unchecked, values None
    assert window.mask_panel.isChecked() is False
    assert window.mask_panel.values() is None
    assert window.background_panel.values() is None
    # Configured section: checked
    assert window.overlay_panel.isChecked() is True

    # Add mask section, remove overlay section
    window.mask_panel.setChecked(True)
    window.mask_panel.file.setCurrentText("the_mask.png")
    window.overlay_panel.setChecked(False)
    window.save()

    raw = json.loads(config_file.read_text(encoding="utf-8"))
    assert raw["screenshot_mask"] == {"file": "the_mask.png"}
    assert "overlay" not in raw
    window.close()


def test_start_page_lists_recents_and_opens_project(qapp, project, tmp_path):
    """Start page shows recent-project buttons; clicking one loads the project."""
    recents = RecentProjects(str(tmp_path / "recents.json"))
    recents.add(str(project))

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    window = MainWindow(str(empty_dir), str(empty_dir / "screenshot-cropper.json"),
                        recents=recents)
    assert window.state is None
    assert len(window.recent_buttons) == 1

    window.recent_buttons[0].click()
    assert window.state is not None
    assert window.crop_panel.values().left == 4
    # Opening moved the project to the front of the store (still deduped)
    assert recents.load()[0] == str(project)
    window.close()


def test_editor_smoke(qapp, project):
    window = MainWindow(str(project), str(project / "screenshot-cropper.json"))

    # Panels populated from config
    assert window.crop_panel.values().left == 4
    assert window.background_panel.values().width == 30
    assert window.mask_panel.values().file == "mask.png"

    # Force a synchronous render; preview pixmap matches background canvas
    window.renderer.render_now()
    pixmap = window.preview.pixmap()
    assert pixmap is not None
    assert (pixmap.width(), pixmap.height()) == (100, 80)

    # Edit values, save, verify round-trip incl. unknown keys
    window.crop_panel.top.setValue(9)
    window.final_crop_panel.bottom.setValue(11)
    window.save()
    raw = json.loads(
        (project / "screenshot-cropper.json").read_text(encoding="utf-8")
    )
    assert raw["crop"]["top"] == 9
    assert raw["final_crop"]["bottom"] == 11
    assert raw["screenshot_mask"] == {"file": "mask.png"}
    assert raw["custom_key"] == "keep me"
    window.close()
