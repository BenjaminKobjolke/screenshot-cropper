"""
Preview widget: displays the composed image scaled to fit.
"""
from __future__ import annotations

import logging

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

logger = logging.getLogger("screenshot_cropper")


class PreviewWidget(QWidget):
    """Paints the current composite pixmap zoom-to-fit, centered."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self.setMinimumSize(200, 200)

    def pixmap(self) -> QPixmap | None:
        """Return the full-resolution pixmap currently shown."""
        return self._pixmap

    def set_image(self, img: Image.Image) -> None:
        """Convert a PIL image to a pixmap and repaint.

        Args:
            img: The composed PIL image.
        """
        rgba = img.convert("RGBA")
        data = rgba.tobytes("raw", "RGBA")
        qimage = QImage(data, rgba.width, rgba.height, QImage.Format.Format_RGBA8888)
        # copy() detaches from the transient Python buffer
        self._pixmap = QPixmap.fromImage(qimage.copy())
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.darkGray)
        if self._pixmap is None:
            return
        scaled = self._pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
