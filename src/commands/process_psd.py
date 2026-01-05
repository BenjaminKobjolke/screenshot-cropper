"""PSD processing command handler."""
from __future__ import annotations

import logging
import os

from adobe_document_handler import LocaleHandler, PSDProcessor

from src.constants import DIRS, FILE_EXT
from src.filename_utils import extract_screenshot_number
from src.models.settings import TextSettings


def run_psd_processing(
    input_dir: str,
    output_dir: str,
    locales_dir: str,
    screenshot_filter: int | None,
    language_filter: str | None,
    skip_existing: bool,
    text_settings: TextSettings | None,
    logger: logging.Logger,
) -> int:
    """Run PSD processing pipeline.

    This processes PSD files when crop_settings is not available
    (i.e., when ImageProcessor was skipped).

    Args:
        input_dir: Input directory containing PSD files.
        output_dir: Output directory for processed files.
        locales_dir: Directory containing locale files.
        screenshot_filter: Optional screenshot number filter.
        language_filter: Optional language filter.
        skip_existing: Whether to skip existing output files.
        text_settings: Optional text settings for font configuration.
        logger: Logger instance.

    Returns:
        Number of PSD files processed.
    """
    logger.info("Starting direct PSD processing (ImageProcessor was skipped).")

    # Initialize a separate LocaleHandler for PSD processing
    psd_locale_handler: LocaleHandler | None = None
    if locales_dir and os.path.isdir(locales_dir):
        try:
            psd_locale_handler = LocaleHandler(locales_dir, language_filter)
            if psd_locale_handler.get_locales():
                logger.info(
                    f"Initialized LocaleHandler for PSD processing with locales: "
                    f"{', '.join(psd_locale_handler.get_locales())}"
                )
            else:
                logger.info(
                    f"LocaleHandler for PSD initialized, but no locale files found in "
                    f"'{locales_dir}'. PSDs will be processed to 'default' output."
                )
                psd_locale_handler = None
        except Exception as e:
            logger.error(
                f"Failed to initialize LocaleHandler for PSD processing from "
                f"'{locales_dir}': {e}"
            )
            psd_locale_handler = None
    else:
        logger.info(
            "Locales directory not configured or not found for PSD processing. "
            "PSDs will be processed to 'default' output without localization."
        )

    logger.info("Starting PSD processing if applicable.")
    psd_input_dir = input_dir

    if not os.path.isdir(psd_input_dir):
        logger.warning(f"PSD input directory '{psd_input_dir}' not found. Skipping PSD processing.")
        return 0

    logger.info(f"Found PSD input directory: {psd_input_dir}")

    try:
        psd_processor = PSDProcessor(
            locale_handler=psd_locale_handler,
            text_settings=text_settings
        )
        logger.info("Initialized PSDProcessor for PSD file handling.")

        psd_files_processed_count = 0
        for filename in os.listdir(psd_input_dir):
            if not filename.lower().endswith(FILE_EXT.PSD):
                continue

            # Check if we should filter by screenshot number
            if screenshot_filter is not None:
                screenshot_num = extract_screenshot_number(filename)
                if screenshot_num != screenshot_filter:
                    logger.debug(f"Skipping PSD file '{filename}' (filter: {screenshot_filter})")
                    continue

            psd_file_path = os.path.join(psd_input_dir, filename)
            logger.info(f"Found PSD file for processing: {psd_file_path}")

            if psd_locale_handler and psd_locale_handler.get_locales():
                psd_files_processed_count += _process_psd_with_locales(
                    psd_processor=psd_processor,
                    psd_file_path=psd_file_path,
                    filename=filename,
                    output_dir=output_dir,
                    psd_locale_handler=psd_locale_handler,
                    skip_existing=skip_existing,
                    logger=logger,
                )
            else:
                psd_files_processed_count += _process_psd_without_locales(
                    psd_processor=psd_processor,
                    psd_file_path=psd_file_path,
                    filename=filename,
                    output_dir=output_dir,
                    logger=logger,
                )

        if psd_files_processed_count > 0:
            logger.info(f"Successfully processed {psd_files_processed_count} PSD file instances.")
        else:
            logger.info("No PSD files were processed (or found ending with .psd).")

        return psd_files_processed_count

    except ImportError:
        logger.error(
            "PSDProcessor could not be initialized due to missing 'photoshop-python-api'. "
            "PSD processing will be skipped."
        )
        return 0
    except Exception as e:
        logger.error(f"An error occurred during PSD processing setup or execution: {e}")
        return 0


def _process_psd_with_locales(
    psd_processor: PSDProcessor,
    psd_file_path: str,
    filename: str,
    output_dir: str,
    psd_locale_handler: LocaleHandler,
    skip_existing: bool,
    logger: logging.Logger,
) -> int:
    """Process a PSD file with multiple locales.

    Returns:
        Number of locale instances processed.
    """
    logger.info(
        f"Processing PSD '{filename}' for locales: "
        f"{', '.join(psd_locale_handler.get_locales())}"
    )

    # Build dictionary of output paths for all locales
    output_paths_by_locale: dict[str, str] = {}
    skipped_count = 0
    processed_count = 0

    for loc in psd_locale_handler.get_locales():
        locale_specific_output_dir = os.path.join(output_dir, loc)
        if not os.path.exists(locale_specific_output_dir):
            os.makedirs(locale_specific_output_dir)
            logger.info(
                f"Created PSD output directory for locale '{loc}': "
                f"{locale_specific_output_dir}"
            )

        output_png_filename = (
            os.path.basename(psd_file_path)
            .replace(".psd", FILE_EXT.PNG)
            .replace(".PSD", FILE_EXT.PNG)
        )
        output_png_path = os.path.join(locale_specific_output_dir, output_png_filename)

        # Check if we should skip this locale
        if skip_existing and os.path.exists(output_png_path):
            logger.info(
                f"Skipping locale {loc} for PSD '{filename}' - output file already exists"
            )
            skipped_count += 1
            processed_count += 1
        else:
            output_paths_by_locale[loc] = output_png_path

    # Process all locales efficiently in one pass (if any remain)
    if output_paths_by_locale:
        logger.info(
            f"Processing PSD '{psd_file_path}' for "
            f"{len(output_paths_by_locale)} locales in one pass"
        )
        results = psd_processor.process_psd_for_multiple_locales(
            psd_file_path, output_paths_by_locale
        )

        for loc, success in results.items():
            if success:
                processed_count += 1
                logger.info(f"Successfully processed PSD '{psd_file_path}' for locale '{loc}'")
            else:
                logger.error(f"Failed to process PSD '{psd_file_path}' for locale '{loc}'")
    else:
        logger.info(f"All locales skipped for PSD '{filename}'")

    return processed_count


def _process_psd_without_locales(
    psd_processor: PSDProcessor,
    psd_file_path: str,
    filename: str,
    output_dir: str,
    logger: logging.Logger,
) -> int:
    """Process a PSD file without locales (to 'default' directory).

    Returns:
        1 if successful, 0 otherwise.
    """
    logger.info(
        f"No active locales for PSD processing of '{filename}'. "
        "Processing to 'default' directory."
    )

    default_output_dir = os.path.join(output_dir, DIRS.DEFAULT)
    if not os.path.exists(default_output_dir):
        os.makedirs(default_output_dir)
        logger.info(f"Created default PSD output directory: {default_output_dir}")

    output_png_filename = (
        os.path.basename(psd_file_path)
        .replace(".psd", FILE_EXT.PNG)
        .replace(".PSD", FILE_EXT.PNG)
    )
    output_png_path = os.path.join(default_output_dir, output_png_filename)

    logger.info(f"Processing PSD '{psd_file_path}' (no locale) -> '{output_png_path}'")
    if psd_processor.process_psd(psd_file_path, output_png_path):
        return 1
    else:
        logger.error(f"Failed to process PSD '{psd_file_path}' (no locale)")
        return 0
