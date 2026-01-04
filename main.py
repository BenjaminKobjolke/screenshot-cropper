#!/usr/bin/env python3
"""
Screenshot Cropper - A tool to crop screenshots based on JSON configuration.
"""
from __future__ import annotations

import os
import sys

from src.cli.arguments import parse_arguments, resolve_paths, validate_arguments
from src.commands.editor import run_editor
from src.commands.prepare_export import (
    run_prepare_export_direct,
    run_prepare_export_directory,
)
from src.commands.process_images import run_image_processing
from src.commands.process_psd import run_psd_processing
from src.config import ConfigHandler
from src.logger import setup_logger


def main() -> None:
    """Main entry point for the application."""
    # Setup logging
    logger = setup_logger()

    # Parse and validate command line arguments
    args = parse_arguments()
    validate_arguments(args, logger)

    screenshot_filter = args.screenshot
    language_filter = args.language
    prepare_and_export = args.prepare_and_export
    skip_existing = args.skip_existing

    # Handle direct path mode for prepare-and-export
    if prepare_and_export and args.file and args.output:
        run_prepare_export_direct(args.file, args.output, logger)
        return

    # Handle editor mode
    if args.editor:
        if not args.directory:
            logger.error("--editor requires --directory to be specified")
            sys.exit(1)
        run_editor(args.directory, logger)
        return

    # Resolve paths from arguments
    config_file, input_dir, locales_dir, output_dir = resolve_paths(args, logger)

    # Build log message with filters
    log_parts: list[str] = []
    if screenshot_filter is not None:
        log_parts.append(f"filtering screenshot: {screenshot_filter}")
    if language_filter is not None:
        log_parts.append(f"filtering language: {language_filter}")
    if skip_existing:
        log_parts.append("skipping existing files")
    if log_parts:
        logger.info(", ".join(log_parts))

    if prepare_and_export:
        logger.info("Prepare and export mode enabled")

    # Check if input directory exists
    if not os.path.isdir(input_dir):
        logger.error(f"Input directory '{input_dir}' does not exist")
        sys.exit(1)

    # Handle directory-based prepare-and-export mode
    if prepare_and_export:
        run_prepare_export_directory(input_dir, output_dir, screenshot_filter, logger)
        return

    # Run image processing pipeline
    run_image_processing(
        config_file=config_file,
        input_dir=input_dir,
        locales_dir=locales_dir,
        output_dir=output_dir,
        screenshot_filter=screenshot_filter,
        language_filter=language_filter,
        skip_existing=skip_existing,
        logger=logger,
    )

    # Get text_settings for PSD processing (need to reload config)
    text_settings = None
    if os.path.isfile(config_file):
        try:
            config_handler = ConfigHandler(config_file)
            text_settings = config_handler.get_text_settings()
            crop_settings = config_handler.get_crop_settings()
        except Exception:
            crop_settings = None
    else:
        crop_settings = None

    # Run PSD processing only if ImageProcessor was skipped (no crop settings)
    if not crop_settings:
        run_psd_processing(
            input_dir=input_dir,
            output_dir=output_dir,
            locales_dir=locales_dir,
            screenshot_filter=screenshot_filter,
            language_filter=language_filter,
            skip_existing=skip_existing,
            text_settings=text_settings,
            logger=logger,
        )

    logger.info("All operations finished.")


if __name__ == "__main__":
    main()
