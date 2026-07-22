"""
Editor state: current settings, compositor factory, config persistence.

Qt-free so the editor core stays unit-testable.
"""
from __future__ import annotations

import logging

from src.config import ConfigHandler
from src.config_writer import ConfigWriter, merge_settings_into_config
from src.image_compositor import ImageCompositor
from src.models.settings import (
    BackgroundSettings,
    CropSettings,
    ExportSettings,
    OverlaySettings,
    ScreenshotMaskSettings,
    TextSettings,
)
from src.text_processor import TextProcessor

logger = logging.getLogger("screenshot_cropper")


class EditorState:
    """Holds the editable settings and persists them back to the config file."""

    def __init__(self, base_dir: str, config_handler: ConfigHandler,
                 config_writer: ConfigWriter) -> None:
        """
        Args:
            base_dir: Project base directory (contains input/, output/).
            config_handler: Loaded config reader providing initial settings.
            config_writer: Writer used to persist edited settings.
        """
        self.base_dir = base_dir
        self._writer = config_writer
        self._raw = config_writer.load_raw()

        self.crop: CropSettings = (
            config_handler.get_crop_settings() or CropSettings(top=0)
        )
        self.final_crop: CropSettings = (
            config_handler.get_final_crop_settings() or CropSettings(top=0)
        )
        self.background: BackgroundSettings | None = config_handler.get_background_settings()
        self.screenshot_mask: ScreenshotMaskSettings | None = (
            config_handler.get_screenshot_mask_settings()
        )
        self.overlay: OverlaySettings | None = config_handler.get_overlay_settings()
        self.text: TextSettings | None = config_handler.get_text_settings()
        self.export: ExportSettings = (
            config_handler.get_export_settings() or ExportSettings()
        )

    def build_compositor(self) -> ImageCompositor:
        """Create an ImageCompositor reflecting the current settings.

        Returns:
            A compositor whose compose() renders the live preview.
        """
        text_processor = TextProcessor(self.text) if self.text else None
        return ImageCompositor(
            self.crop,
            background_settings=self.background,
            text_processor=text_processor,
            base_dir=self.base_dir,
            overlay_settings=self.overlay,
            export_settings=self.export,
            final_crop_settings=self.final_crop,
            mask_settings=self.screenshot_mask,
        )

    def save(self) -> None:
        """Merge current settings into the raw config and write it to disk."""
        fc = self.final_crop
        # Emit final_crop only when it does something or the section already exists,
        # so untouched configs gain no noise
        final_crop = fc if (
            any((fc.top, fc.left, fc.right, fc.bottom)) or "final_crop" in self._raw
        ) else None
        merge_settings_into_config(
            self._raw, self.crop, self.background, self.overlay, self.text, self.export,
            final_crop=final_crop, screenshot_mask=self.screenshot_mask,
        )
        self._writer.save(self._raw)
