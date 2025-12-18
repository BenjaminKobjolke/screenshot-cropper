#!/usr/bin/env python3
"""
Screenshot Cropper - A tool to crop screenshots based on JSON configuration.
"""
import argparse
import logging
import os
import sys
from src.config import ConfigHandler
from src.image_processor import ImageProcessor
from src.locale_handler import LocaleHandler
from src.text_processor import TextProcessor
from src.psd_processor import PSDProcessor # Added import
from src.logger import setup_logger
from src.filename_utils import extract_screenshot_number

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Crop screenshots based on JSON configuration.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--directory", help="Directory containing input folder and configuration file")
    group.add_argument("--config", help="Path to configuration JSON file (directories specified in JSON)")
    parser.add_argument("--screenshot", type=int, help="Process only the specified screenshot number (e.g., 7 for '7.png')")
    parser.add_argument("--language", type=str, help="Process only the specified language (e.g., 'en', 'de')")
    parser.add_argument("--prepare-and-export", action="store_true", help="Prepare PSD by renaming text layers and export template.json (requires --screenshot)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip processing for languages where output file already exists")
    parser.add_argument("--editor", action="store_true", help="Launch visual editor to configure positions and sizes")
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    # Setup logging
    logger = setup_logger()

    # Parse command line arguments
    args = parse_arguments()
    screenshot_filter = args.screenshot
    language_filter = args.language
    prepare_and_export = args.prepare_and_export
    skip_existing = args.skip_existing

    # Validate arguments
    if prepare_and_export and screenshot_filter is None:
        logger.error("--prepare-and-export requires --screenshot to be specified")
        sys.exit(1)

    # Handle --editor mode
    if args.editor:
        if not args.directory:
            logger.error("--editor requires --directory to be specified")
            sys.exit(1)

        directory = args.directory
        if not os.path.isdir(directory):
            logger.error(f"Directory '{directory}' does not exist")
            sys.exit(1)

        config_file = os.path.join(directory, "screenshot-cropper.json")
        logger.info(f"Launching visual editor for: {directory}")

        from src.editor.editor_window import launch_editor
        launch_editor(directory, config_file)
        sys.exit(0)

    # Determine config file and directories based on mode
    if args.config:
        # --config mode: read directories from JSON
        config_file = args.config
        if not os.path.isfile(config_file):
            logger.error(f"Configuration file '{config_file}' does not exist")
            sys.exit(1)

        # Load config to get directories
        try:
            config_handler = ConfigHandler(config_file)
            dirs = config_handler.get_directories()
        except Exception as e:
            logger.error(f"Failed to load configuration from '{config_file}': {e}")
            sys.exit(1)

        input_dir = dirs.get('screenshots')
        locales_dir = dirs.get('locales')
        output_dir = dirs.get('output')

        if not input_dir:
            logger.error("Configuration must specify 'directories.screenshots'")
            sys.exit(1)
        if not output_dir:
            logger.error("Configuration must specify 'directories.output'")
            sys.exit(1)

        logger.info(f"Starting screenshot cropper with config: {config_file}")
    else:
        # --directory mode: derive paths from base directory
        directory = args.directory
        if not os.path.isdir(directory):
            logger.error(f"Directory '{directory}' does not exist")
            sys.exit(1)

        config_file = os.path.join(directory, "screenshot-cropper.json")
        input_dir = os.path.join(directory, "input", "screenshots")
        locales_dir = os.path.join(directory, "input", "locales")
        output_dir = os.path.join(directory, "output")
        config_handler = None

        logger.info(f"Starting screenshot cropper with directory: {directory}")

    # Build log message with filters
    log_parts = []
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

    # Handle prepare-and-export mode
    if prepare_and_export:
        logger.info("Running in prepare-and-export mode")

        # Find the PSD file matching the screenshot filter
        psd_file = None
        for filename in os.listdir(input_dir):
            if filename.lower().endswith(".psd"):
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
        output_json_path = os.path.join(output_dir, "template.json")

        # Initialize PSD processor and run prepare and export
        psd_processor = PSDProcessor()
        success = psd_processor.prepare_and_export_template(psd_file, output_json_path)

        if success:
            logger.info("Successfully prepared PSD and exported template")
            sys.exit(0)
        else:
            logger.error("Failed to prepare PSD and export template")
            sys.exit(1)

    # Initialize settings to None
    crop_settings = None
    background_settings = None
    text_settings = None
    overlay_settings = None
    export_settings = None

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    if not os.path.isfile(config_file):
        logger.warning(f"Configuration file '{config_file}' not found. Cropping, background addition, and text overlay will be skipped.")
    else:
        logger.info(f"Attempting to load configuration from '{config_file}'")
        try:
            # Reuse config_handler if already loaded (--config mode)
            if config_handler is None:
                config_handler = ConfigHandler(config_file)
            # Attempt to load crop_settings. It's crucial.
            current_crop_settings = config_handler.get_crop_settings()
            if current_crop_settings:
                crop_settings = current_crop_settings # Assign to the main variable
                logger.info(f"Loaded crop settings: {crop_settings}")
            else:
                # crop_settings remains None if not found or empty
                logger.warning(f"No crop settings found in '{config_file}'. Cropping will be skipped.")

            # Background and text settings are optional, assign if found
            current_background_settings = config_handler.get_background_settings()
            if current_background_settings:
                background_settings = current_background_settings
                logger.info(f"Loaded background settings: {background_settings}")
            else:
                logger.info(f"No background settings found in '{config_file}', or section is missing.")
                
            current_text_settings = config_handler.get_text_settings()
            if current_text_settings:
                text_settings = current_text_settings
                logger.info(f"Loaded text settings: {text_settings}")
            else:
                logger.info(f"No text settings found in '{config_file}', or section is missing.")

            current_overlay_settings = config_handler.get_overlay_settings()
            if current_overlay_settings:
                overlay_settings = current_overlay_settings
                logger.info(f"Loaded overlay settings: {overlay_settings}")
            else:
                logger.info(f"No overlay settings found in '{config_file}', or section is missing.")

            current_export_settings = config_handler.get_export_settings()
            if current_export_settings:
                export_settings = current_export_settings
                logger.info(f"Loaded export settings: {export_settings}")
        except Exception as e:
            logger.error(f"Failed to load or parse configuration from '{config_file}': {e}. Cropping, background, and text overlay will be skipped.")
            # Ensure settings are reset to None if any error occurred during parsing
            crop_settings = None
            background_settings = None
            text_settings = None
            overlay_settings = None
            export_settings = None
    
    # Initialize locale handler if text settings are available
    locale_handler = None
    if text_settings and locales_dir:
        if os.path.isdir(locales_dir):
            locale_handler = LocaleHandler(locales_dir, language_filter)
            if locale_handler.get_locales():
                logger.info(f"Initialized locale handler with locales: {', '.join(locale_handler.get_locales())}")
            else:
                logger.warning(f"No locales loaded. Check language filter or locales directory.")
        else:
            logger.warning(f"Locales directory not found: {locales_dir}")
    
    # Initialize text processor if text settings are available
    text_processor = None
    if text_settings:
        text_processor = TextProcessor(text_settings)
        logger.info("Initialized text processor")
    
    # Process images only if crop_settings were successfully loaded
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
                export_settings
            )
            processed_count = image_processor.process_images()
            logger.info(f"Successfully processed {processed_count} images for cropping/text.")
        except Exception as e:
            logger.error(f"Failed to process images: {e}")
            sys.exit(1) # If processing starts but fails, it's a critical error for this part.
    else:
        logger.info("Skipping image cropping, background addition, and text overlay as no valid crop settings were loaded.")
    
    logger.info("Main script operations for screenshot processing finished.")

    # --- PSD Processing Section (Only if ImageProcessor was NOT used) ---
    # If crop_settings exist, ImageProcessor already handled PSD files along with regular images
    # This section only runs when crop_settings is None (no cropping configured)
    if not crop_settings:
        logger.info("Starting direct PSD processing (ImageProcessor was skipped).")

        # Initialize a separate LocaleHandler for PSD processing
        psd_locale_handler = None
        if locales_dir and os.path.isdir(locales_dir):
            try:
                psd_locale_handler = LocaleHandler(locales_dir, language_filter)
                if psd_locale_handler.get_locales():
                    logger.info(f"Initialized LocaleHandler for PSD processing with locales: {', '.join(psd_locale_handler.get_locales())}")
                else:
                    logger.info(f"LocaleHandler for PSD initialized, but no locale files found in '{locales_dir}'. PSDs will be processed to 'default' output.")
                    psd_locale_handler = None # Ensure it's None if no actual locales
            except Exception as e:
                logger.error(f"Failed to initialize LocaleHandler for PSD processing from '{locales_dir}': {e}")
                psd_locale_handler = None
        else:
            logger.info(f"Locales directory not configured or not found for PSD processing. PSDs will be processed to 'default' output without localization.")

        # --- PSD Processing Section ---
        logger.info("Starting PSD processing if applicable.")
        # PSD files are in the input/screenshots directory (same as input_dir)
        psd_input_dir = input_dir

        # We already check for input_dir at the beginning, so this should exist
        if not os.path.isdir(psd_input_dir):
            logger.warning(f"PSD input directory '{psd_input_dir}' not found. Skipping PSD processing.")
        else:
            logger.info(f"Found PSD input directory: {psd_input_dir}")
        
            # Initialize PSDProcessor
            # It will use the independent psd_locale_handler and text_settings (if loaded from screenshot-cropper.json)
            try:
                psd_processor = PSDProcessor(locale_handler=psd_locale_handler, text_settings=text_settings)
                logger.info("Initialized PSDProcessor for PSD file handling.")

                psd_files_processed_count = 0
                for filename in os.listdir(psd_input_dir):
                    if filename.lower().endswith(".psd"):
                        # Check if we should filter by screenshot number
                        if screenshot_filter is not None:
                            screenshot_num = extract_screenshot_number(filename)
                            if screenshot_num != screenshot_filter:
                                logger.debug(f"Skipping PSD file '{filename}' (filter: {screenshot_filter})")
                                continue

                        psd_file_path = os.path.join(psd_input_dir, filename)
                        logger.info(f"Found PSD file for processing: {psd_file_path}")

                        if psd_locale_handler and psd_locale_handler.get_locales():
                            logger.info(f"Processing PSD '{filename}' for locales: {', '.join(psd_locale_handler.get_locales())}")

                            # Build dictionary of output paths for all locales
                            # If skip_existing is enabled, filter out locales where output already exists
                            output_paths_by_locale = {}
                            skipped_count = 0

                            for loc in psd_locale_handler.get_locales():
                                # Output path is now output_dir / locale / filename.png
                                locale_specific_output_dir = os.path.join(output_dir, loc)
                                if not os.path.exists(locale_specific_output_dir):
                                    os.makedirs(locale_specific_output_dir)
                                    logger.info(f"Created PSD output directory for locale '{loc}': {locale_specific_output_dir}")

                                output_png_filename = os.path.basename(psd_file_path).replace('.psd', '.png').replace('.PSD', '.png')
                                output_png_path = os.path.join(locale_specific_output_dir, output_png_filename)

                                # Check if we should skip this locale
                                if skip_existing and os.path.exists(output_png_path):
                                    logger.info(f"Skipping locale {loc} for PSD '{filename}' - output file already exists")
                                    skipped_count += 1
                                    psd_files_processed_count += 1  # Count as processed (skipped)
                                else:
                                    output_paths_by_locale[loc] = output_png_path

                            # Process all locales efficiently in one pass (if any remain)
                            if output_paths_by_locale:
                                logger.info(f"Processing PSD '{psd_file_path}' for {len(output_paths_by_locale)} locales in one pass")
                                results = psd_processor.process_psd_for_multiple_locales(psd_file_path, output_paths_by_locale)

                                # Count successful processing
                                for loc, success in results.items():
                                    if success:
                                        psd_files_processed_count += 1
                                        logger.info(f"Successfully processed PSD '{psd_file_path}' for locale '{loc}'")
                                    else:
                                        logger.error(f"Failed to process PSD '{psd_file_path}' for locale '{loc}'")
                            else:
                                logger.info(f"All locales skipped for PSD '{filename}'")
                        else:
                            logger.info(f"No active locales for PSD processing of '{filename}'. Processing to 'default' directory.")
                            # Output path is now output_dir / default / filename.png
                            default_output_dir = os.path.join(output_dir, "default")
                            if not os.path.exists(default_output_dir):
                                os.makedirs(default_output_dir)
                                logger.info(f"Created default PSD output directory: {default_output_dir}")

                            output_png_filename = os.path.basename(psd_file_path).replace('.psd', '.png').replace('.PSD', '.png')
                            output_png_path = os.path.join(default_output_dir, output_png_filename)

                            logger.info(f"Processing PSD '{psd_file_path}' (no locale) -> '{output_png_path}'")
                            if psd_processor.process_psd(psd_file_path, output_png_path): # No locale passed
                                psd_files_processed_count += 1
                            else:
                                logger.error(f"Failed to process PSD '{psd_file_path}' (no locale)")
            
                if psd_files_processed_count > 0:
                    logger.info(f"Successfully processed {psd_files_processed_count} PSD file instances.")
                else:
                    logger.info("No PSD files were processed (or found ending with .psd).")

            except ImportError:
                logger.error("PSDProcessor could not be initialized due to missing 'photoshop-python-api'. PSD processing will be skipped.")
            except Exception as e:
                logger.error(f"An error occurred during PSD processing setup or execution: {e}")

    logger.info("All operations finished.")

if __name__ == "__main__":
    main()
