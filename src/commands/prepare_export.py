"""Prepare-and-export command handlers."""
from __future__ import annotations

import logging
import os
import sys

from src.constants import CONFIG, FILE_EXT
from src.filename_utils import extract_screenshot_number
from src.psd_processor import PSDProcessor


def run_prepare_export_direct(
    design_file: str,
    output_json: str,
    logger: logging.Logger
) -> None:
    """Run prepare-and-export with direct file paths.

    Args:
        design_file: Path to the PSD or INDD file.
        output_json: Path for the output JSON file.
        logger: Logger instance.

    Exits with code 0 on success, 1 on failure.
    """
    logger.info("Running in prepare-and-export mode (direct path)")

    if not os.path.isfile(design_file):
        logger.error(f"Design file not found: {design_file}")
        sys.exit(1)

    logger.info(f"Design file: {design_file}")
    logger.info(f"Output JSON: {output_json}")

    # Auto-create output directory if it doesn't exist
    output_dir = os.path.dirname(output_json)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    # Detect file type and use appropriate processor
    file_lower = design_file.lower()

    if file_lower.endswith(FILE_EXT.INDD):
        # InDesign file
        from src.indesign_processor import InDesignProcessor
        processor = InDesignProcessor()
        success = processor.prepare_and_export_template(design_file, output_json)
        file_type = "INDD"
    elif file_lower.endswith(FILE_EXT.PSD):
        # Photoshop file
        processor = PSDProcessor()
        success = processor.prepare_and_export_template(design_file, output_json)
        file_type = "PSD"
    else:
        logger.error(
            f"Unsupported file type: {design_file}. "
            f"Supported: {FILE_EXT.PSD}, {FILE_EXT.INDD}"
        )
        sys.exit(1)

    if success:
        logger.info(f"Successfully prepared {file_type} and exported template")
        sys.exit(0)
    else:
        logger.error(f"Failed to prepare {file_type} and export template")
        sys.exit(1)


def run_prepare_export_directory(
    input_dir: str,
    output_dir: str,
    screenshot_filter: int,
    logger: logging.Logger
) -> None:
    """Run prepare-and-export with directory-based discovery.

    Args:
        input_dir: Input directory containing PSD files.
        output_dir: Output directory for the JSON file.
        screenshot_filter: Screenshot number to filter by.
        logger: Logger instance.

    Exits with code 0 on success, 1 on failure.
    """
    logger.info("Running in prepare-and-export mode (directory-based)")

    # Find the PSD file matching the screenshot filter
    psd_file: str | None = None
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(FILE_EXT.PSD):
            screenshot_num = extract_screenshot_number(filename)
            if screenshot_num == screenshot_filter:
                psd_file = os.path.join(input_dir, filename)
                break

    if not psd_file:
        logger.error(f"No PSD file found matching screenshot number: {screenshot_filter}")
        sys.exit(1)

    logger.info(f"Found PSD file: {psd_file}")

    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    # Set output path for template.json
    output_json_path = os.path.join(output_dir, CONFIG.TEMPLATE_FILE)

    # Initialize PSD processor and run prepare and export
    psd_processor = PSDProcessor()
    success = psd_processor.prepare_and_export_template(psd_file, output_json_path)

    if success:
        logger.info("Successfully prepared PSD and exported template")
        sys.exit(0)
    else:
        logger.error("Failed to prepare PSD and export template")
        sys.exit(1)
