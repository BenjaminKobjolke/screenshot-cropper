"""Image processing command handler."""
from __future__ import annotations

import logging
import os

from adobe_document_handler import LocaleHandler

from src.config import ConfigHandler
from src.image_processor import ImageProcessor
from src.models.settings import (
    BackgroundSettings,
    CropSettings,
    ExportSettings,
    OverlaySettings,
    TextSettings,
)
from src.text_processor import TextProcessor


def run_image_processing(
    config_file: str,
    input_dir: str,
    locales_dir: str,
    output_dir: str,
    screenshot_filter: int | None,
    language_filter: str | None,
    skip_existing: bool,
    logger: logging.Logger,
) -> int:
    """Run image processing pipeline.

    Args:
        config_file: Path to configuration file.
        input_dir: Input directory containing images.
        locales_dir: Directory containing locale files.
        output_dir: Output directory for processed images.
        screenshot_filter: Optional screenshot number filter.
        language_filter: Optional language filter.
        skip_existing: Whether to skip existing output files.
        logger: Logger instance.

    Returns:
        Number of images processed.
    """
    # Initialize settings
    crop_settings: CropSettings | None = None
    background_settings: BackgroundSettings | None = None
    text_settings: TextSettings | None = None
    overlay_settings: OverlaySettings | None = None
    export_settings: ExportSettings | None = None
    config_handler: ConfigHandler | None = None

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    if not os.path.isfile(config_file):
        logger.warning(
            f"Configuration file '{config_file}' not found. "
            "Cropping, background addition, and text overlay will be skipped."
        )
    else:
        logger.info(f"Attempting to load configuration from '{config_file}'")
        try:
            config_handler = ConfigHandler(config_file)

            # Load crop settings
            current_crop_settings = config_handler.get_crop_settings()
            if current_crop_settings:
                crop_settings = current_crop_settings
                logger.info(f"Loaded crop settings: {crop_settings}")
            else:
                logger.warning(
                    f"No crop settings found in '{config_file}'. Cropping will be skipped."
                )

            # Load background settings
            current_background_settings = config_handler.get_background_settings()
            if current_background_settings:
                background_settings = current_background_settings
                logger.info(f"Loaded background settings: {background_settings}")
            else:
                logger.info(
                    f"No background settings found in '{config_file}', or section is missing."
                )

            # Load text settings
            current_text_settings = config_handler.get_text_settings()
            if current_text_settings:
                text_settings = current_text_settings
                logger.info(f"Loaded text settings: {text_settings}")
            else:
                logger.info(
                    f"No text settings found in '{config_file}', or section is missing."
                )

            # Load overlay settings
            current_overlay_settings = config_handler.get_overlay_settings()
            if current_overlay_settings:
                overlay_settings = current_overlay_settings
                logger.info(f"Loaded overlay settings: {overlay_settings}")
            else:
                logger.info(
                    f"No overlay settings found in '{config_file}', or section is missing."
                )

            # Load export settings
            current_export_settings = config_handler.get_export_settings()
            if current_export_settings:
                export_settings = current_export_settings
                logger.info(f"Loaded export settings: {export_settings}")

        except Exception as e:
            logger.error(
                f"Failed to load or parse configuration from '{config_file}': {e}. "
                "Cropping, background, and text overlay will be skipped."
            )
            crop_settings = None
            background_settings = None
            text_settings = None
            overlay_settings = None
            export_settings = None

    # Initialize locale handler if text settings are available
    locale_handler: LocaleHandler | None = None
    if text_settings and locales_dir:
        if os.path.isdir(locales_dir):
            locale_handler = LocaleHandler(locales_dir, language_filter)
            if locale_handler.get_locales():
                logger.info(
                    f"Initialized locale handler with locales: "
                    f"{', '.join(locale_handler.get_locales())}"
                )
            else:
                logger.warning("No locales loaded. Check language filter or locales directory.")
        else:
            logger.warning(f"Locales directory not found: {locales_dir}")

    # Initialize text processor if text settings are available
    text_processor: TextProcessor | None = None
    if text_settings:
        text_processor = TextProcessor(text_settings)
        logger.info("Initialized text processor")

    # Process images only if crop_settings were successfully loaded
    processed_count = 0
    if crop_settings:
        logger.info("Proceeding with image processing (cropping, background, text).")
        try:
            image_processor = ImageProcessor(
                input_dir,
                output_dir,
                crop_settings,
                background_settings,
                text_processor,
                locale_handler,
                screenshot_filter,
                skip_existing,
                overlay_settings,
                export_settings,
            )
            processed_count = image_processor.process_images()
            logger.info(f"Successfully processed {processed_count} images for cropping/text.")
        except Exception as e:
            logger.error(f"Failed to process images: {e}")
            raise
    else:
        logger.info(
            "Skipping image cropping, background addition, and text overlay "
            "as no valid crop settings were loaded."
        )

    logger.info("Main script operations for screenshot processing finished.")
    return processed_count
