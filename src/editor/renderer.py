"""
Debounced preview renderer: composes the current screenshot with current settings.
"""
from __future__ import annotations

import logging

from adobe_document_handler import LocaleHandler
from PIL import Image
from PySide6.QtCore import QObject, QTimer, Signal

from src.editor.sources import ScreenshotEntry
from src.editor.state import EditorState

logger = logging.getLogger("screenshot_cropper")

DEBOUNCE_MS = 300


class PreviewRenderer(QObject):
    """Renders the composite after a short debounce and emits the result."""

    rendered = Signal(object)  # PIL.Image.Image

    def __init__(self, state: EditorState, parent: QObject | None = None) -> None:
        """
        Args:
            state: Editor state providing the compositor.
            parent: Qt parent object.
        """
        super().__init__(parent)
        self._state = state
        self.entry: ScreenshotEntry | None = None
        self.locale: str | None = None
        self.locale_handler: LocaleHandler | None = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(DEBOUNCE_MS)
        self._timer.timeout.connect(self.render_now)

    def request(self) -> None:
        """Schedule a render after the debounce interval (restarts on each call)."""
        self._timer.start()

    def render_now(self) -> None:
        """Render synchronously and emit the composed image."""
        if self.entry is None:
            return
        try:
            text = None
            if self.locale_handler and self.locale:
                text = self.locale_handler.get_text(
                    self.locale, self.entry.text_index, add_one=self.entry.add_one
                )
            compositor = self._state.build_compositor()
            # PSDs open as flattened composite via Pillow (no Photoshop involved)
            with Image.open(self.entry.path) as img:
                result = compositor.compose(
                    img, text=text, locale=self.locale, image_path=self.entry.path
                )
            self.rendered.emit(result.final)
        except Exception as e:
            logger.error(f"Preview render failed for {self.entry.path}: {e}")
