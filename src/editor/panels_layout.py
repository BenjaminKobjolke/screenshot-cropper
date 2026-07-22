"""
Settings panels: base class + crop, background and overlay panels.
"""
from __future__ import annotations

import logging
import os

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QWidget,
)

from src.constants import DIRS, FILE_EXT
from src.models.settings import (
    BackgroundSettings,
    CropSettings,
    OverlaySettings,
    ScreenshotMaskSettings,
)

logger = logging.getLogger("screenshot_cropper")

MAX_PIXELS = 20000


class SettingsPanel(QGroupBox):
    """Base panel: a form layout plus a changed signal and widget factories."""

    changed = Signal()

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(title, parent)
        self.form = QFormLayout(self)

    def make_optional(self, configured: bool) -> None:
        """Give the panel a title checkbox: checked = section present in the JSON.

        Unchecked panels return None from values(), which removes the section
        on save; checking an unconfigured panel adds it with the shown values.
        """
        self.setCheckable(True)
        self.setChecked(configured)
        self.toggled.connect(self.changed)

    def spin_row(self, label: str, value: int, maximum: int = MAX_PIXELS,
                 minimum: int = 0) -> QSpinBox:
        """Add a spinbox row wired to the changed signal."""
        spin = QSpinBox(self)
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        spin.valueChanged.connect(self.changed)
        self.form.addRow(label, spin)
        return spin

    def combo_row(self, label: str, options: list[str], current: str) -> QComboBox:
        """Add a fixed-options combo row wired to the changed signal."""
        combo = QComboBox(self)
        combo.addItems(options)
        combo.setCurrentText(current)
        combo.currentTextChanged.connect(self.changed)
        self.form.addRow(label, combo)
        return combo

    def check_row(self, text: str, checked: bool) -> QCheckBox:
        """Add a checkbox row wired to the changed signal."""
        check = QCheckBox(text, self)
        check.setChecked(checked)
        check.toggled.connect(self.changed)
        self.form.addRow(check)
        return check

    def file_row(self, label: str, value: str, base_dir: str) -> QComboBox:
        """Add an editable combo listing image files from base_dir/input.

        An empty value keeps the first listed file selected (default for
        newly enabled sections).
        """
        combo = QComboBox(self)
        combo.setEditable(True)
        input_dir = os.path.join(base_dir, DIRS.INPUT)
        extensions = (FILE_EXT.PNG, FILE_EXT.JPG, FILE_EXT.JPEG, FILE_EXT.WEBP)
        if os.path.isdir(input_dir):
            combo.addItems(sorted(
                f for f in os.listdir(input_dir)
                if f.lower().endswith(extensions)
            ))
        if value:
            combo.setCurrentText(value)
        combo.currentTextChanged.connect(self.changed)
        self.form.addRow(label, combo)
        return combo

    def xy_rows(self, x: int, y: int) -> tuple[QSpinBox, QSpinBox]:
        """Add position x/y spin rows."""
        return self.spin_row("Position X", x), self.spin_row("Position Y", y)


class CropPanel(SettingsPanel):
    """Edits crop insets (pixels from each edge); used for screenshot and final crop."""

    def __init__(self, settings: CropSettings, title: str = "Screenshot Crop",
                 parent: QWidget | None = None) -> None:
        super().__init__(title, parent)
        self.top = self.spin_row("Top", settings.top)
        self.left = self.spin_row("Left", settings.left)
        self.right = self.spin_row("Right", settings.right)
        self.bottom = self.spin_row("Bottom", settings.bottom)

    def values(self) -> CropSettings:
        """Return the current crop settings."""
        return CropSettings(
            top=self.top.value(), left=self.left.value(),
            right=self.right.value(), bottom=self.bottom.value(),
        )


class BackgroundPanel(SettingsPanel):
    """Edits background file plus screenshot placement (position and width)."""

    def __init__(self, settings: BackgroundSettings | None, base_dir: str,
                 parent: QWidget | None = None) -> None:
        super().__init__("Background / Screenshot placement", parent)
        self.file = self.file_row("File", settings.file if settings else "", base_dir)
        self.pos_x, self.pos_y = self.xy_rows(
            settings.position_x if settings else 0, settings.position_y if settings else 0
        )
        self.width_spin = self.spin_row("Screenshot width", settings.width if settings else 100)
        self.height_spin = self.spin_row("Height (informational)",
                                         settings.height if settings else 100)
        self.make_optional(settings is not None)

    def values(self) -> BackgroundSettings | None:
        """Return current background settings, or None when the section is off."""
        if not self.isChecked():
            return None
        return BackgroundSettings(
            file=self.file.currentText(),
            position_x=self.pos_x.value(), position_y=self.pos_y.value(),
            width=self.width_spin.value(), height=self.height_spin.value(),
        )


class MaskPanel(SettingsPanel):
    """Edits the screenshot mask file (opaque pixels punch holes in the screenshot)."""

    def __init__(self, settings: ScreenshotMaskSettings | None, base_dir: str,
                 parent: QWidget | None = None) -> None:
        super().__init__("Screenshot Mask", parent)
        self.file = self.file_row("File", settings.file if settings else "", base_dir)
        self.make_optional(settings is not None)

    def values(self) -> ScreenshotMaskSettings | None:
        """Return current mask settings, or None when the section is off."""
        if not self.isChecked():
            return None
        return ScreenshotMaskSettings(file=self.file.currentText())


class OverlayPanel(SettingsPanel):
    """Edits overlay file and position."""

    def __init__(self, settings: OverlaySettings | None, base_dir: str,
                 parent: QWidget | None = None) -> None:
        super().__init__("Overlay", parent)
        self.file = self.file_row("File", settings.file if settings else "", base_dir)
        self.pos_x, self.pos_y = self.xy_rows(
            settings.position_x if settings else 0, settings.position_y if settings else 0
        )
        self.make_optional(settings is not None)

    def values(self) -> OverlaySettings | None:
        """Return current overlay settings, or None when the section is off."""
        if not self.isChecked():
            return None
        return OverlaySettings(
            file=self.file.currentText(),
            position_x=self.pos_x.value(), position_y=self.pos_y.value(),
        )
