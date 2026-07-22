"""
Settings panels: text overlay and export options.
"""
from __future__ import annotations

import logging

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDoubleSpinBox,
    QLineEdit,
    QPushButton,
    QWidget,
)

from src.constants import ALIGN, FORMATS
from src.editor.panels_layout import SettingsPanel
from src.models.settings import ExportSettings, TextSettings

logger = logging.getLogger("screenshot_cropper")


_DEFAULT_TEXT = TextSettings(
    font_files={"default": "Arial.ttf"}, font_size=100, align="center",
    x=0, y=0, width=1000, height=400, vertical_align="middle", color=(255, 255, 255),
)


class TextPanel(SettingsPanel):
    """Edits text overlay settings; per-locale font files stay untouched."""

    def __init__(self, settings: TextSettings | None,
                 parent: QWidget | None = None) -> None:
        super().__init__("Text", parent)
        configured = settings is not None
        if settings is None:
            settings = _DEFAULT_TEXT
        self._font_files = dict(settings.font_files)
        self._font_names = dict(settings.font_names)
        self._color = QColor(*settings.color)

        self.enabled_check = self.check_row("Render text", settings.enabled)
        self.size_spin = self.spin_row("Font size", settings.font_size, maximum=2000)

        self.line_height_spin = QDoubleSpinBox(self)
        self.line_height_spin.setRange(0.0, 5.0)
        self.line_height_spin.setSingleStep(0.05)
        self.line_height_spin.setSpecialValueText("auto")
        self.line_height_spin.setValue(settings.line_height or 0.0)
        self.line_height_spin.valueChanged.connect(self.changed)
        self.form.addRow("Line height (× size)", self.line_height_spin)

        self.align_combo = self.combo_row(
            "Align", [ALIGN.LEFT, ALIGN.CENTER, ALIGN.RIGHT], settings.align
        )
        self.valign_combo = self.combo_row(
            "Vertical align", [ALIGN.TOP, ALIGN.MIDDLE, ALIGN.BOTTOM], settings.vertical_align
        )
        self.x_spin = self.spin_row("Box X", settings.x)
        self.y_spin = self.spin_row("Box Y", settings.y)
        self.width_spin = self.spin_row("Box width", settings.width)
        self.height_spin = self.spin_row("Box height", settings.height)

        self.color_button = QPushButton(self)
        self._update_color_button()
        self.color_button.clicked.connect(self._pick_color)
        self.form.addRow("Color", self.color_button)

        self.default_font = QLineEdit(self._font_files.get("default", ""), self)
        self.default_font.textChanged.connect(self.changed)
        self.form.addRow("Default font file", self.default_font)
        self.make_optional(configured)

    def _update_color_button(self) -> None:
        self.color_button.setText(self._color.name())
        self.color_button.setStyleSheet(f"background-color: {self._color.name()};")

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(self._color, self, "Text color")
        if color.isValid():
            self._color = color
            self._update_color_button()
            self.changed.emit()

    def values(self) -> TextSettings | None:
        """Return current text settings, or None when the section is off."""
        if not self.isChecked():
            return None
        font_files = dict(self._font_files)
        font_files["default"] = self.default_font.text() or "Arial.ttf"
        return TextSettings(
            font_files=font_files,
            font_size=self.size_spin.value(),
            align=self.align_combo.currentText(),
            x=self.x_spin.value(), y=self.y_spin.value(),
            width=self.width_spin.value(), height=self.height_spin.value(),
            vertical_align=self.valign_combo.currentText(),
            color=(self._color.red(), self._color.green(), self._color.blue()),
            font_names=self._font_names,
            line_height=self.line_height_spin.value() or None,
            enabled=self.enabled_check.isChecked(),
        )


class ExportPanel(SettingsPanel):
    """Edits export format and quality settings."""

    def __init__(self, settings: ExportSettings, parent: QWidget | None = None) -> None:
        super().__init__("Export", parent)
        self.format_combo = self.combo_row(
            "Format", [FORMATS.PNG, FORMATS.WEBP], settings.format
        )
        self.quality_spin = self.spin_row(
            "Quality (webp)", settings.quality, maximum=100, minimum=1
        )
        self.lossless_check = self.check_row("Lossless (webp)", settings.lossless)
        self.keep_cropped_check = self.check_row("Keep cropped copies", settings.keep_cropped)

    def values(self) -> ExportSettings:
        """Return the current export settings."""
        return ExportSettings(
            format=self.format_combo.currentText(),
            quality=self.quality_spin.value(),
            keep_cropped=self.keep_cropped_check.isChecked(),
            lossless=self.lossless_check.isChecked(),
        )
