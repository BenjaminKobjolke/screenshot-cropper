"""Command-line argument parsing and validation."""
from __future__ import annotations

import argparse
import logging
import os
import sys


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Crop screenshots based on JSON configuration."
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "--directory",
        help="Directory containing input folder and configuration file"
    )
    group.add_argument(
        "--config",
        help="Path to configuration JSON file (directories specified in JSON)"
    )
    parser.add_argument(
        "--file",
        help="Direct path to PSD file (for use with --prepare-and-export)"
    )
    parser.add_argument(
        "--output",
        help="Direct path for JSON output file (for use with --prepare-and-export)"
    )
    parser.add_argument(
        "--screenshot",
        type=int,
        help="Process only the specified screenshot number (e.g., 7 for '7.png')"
    )
    parser.add_argument(
        "--language",
        type=str,
        help="Process only the specified language (e.g., 'en', 'de')"
    )
    parser.add_argument(
        "--prepare-and-export",
        action="store_true",
        help="Prepare PSD by renaming text layers and export template.json"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip processing for languages where output file already exists"
    )
    parser.add_argument(
        "--editor",
        action="store_true",
        help="Launch visual editor to configure positions and sizes"
    )
    return parser.parse_args()


def validate_arguments(args: argparse.Namespace, logger: logging.Logger) -> None:
    """Validate command line arguments.

    Args:
        args: Parsed arguments namespace.
        logger: Logger instance for error messages.

    Exits with code 1 if validation fails.
    """
    prepare_and_export = args.prepare_and_export
    screenshot_filter = args.screenshot

    if prepare_and_export:
        # Two valid modes for prepare-and-export:
        # Mode A: --file + --output (direct paths)
        # Mode B: --directory + --screenshot (directory-based discovery)
        has_direct_mode = args.file and args.output
        has_directory_mode = args.directory and screenshot_filter is not None

        if not has_direct_mode and not has_directory_mode:
            logger.error(
                "--prepare-and-export requires either (--file and --output) "
                "or (--directory and --screenshot)"
            )
            sys.exit(1)

        if args.file and not args.output:
            logger.error("--file requires --output to be specified")
            sys.exit(1)

        if args.output and not args.file:
            logger.error("--output requires --file to be specified")
            sys.exit(1)

    # For non-prepare-and-export modes, require --directory or --config
    if not prepare_and_export and not args.directory and not args.config:
        logger.error("Either --directory or --config is required")
        sys.exit(1)


def resolve_paths(
    args: argparse.Namespace,
    logger: logging.Logger
) -> tuple[str, str, str, str]:
    """Resolve input/output paths from arguments.

    Args:
        args: Parsed arguments namespace.
        logger: Logger instance.

    Returns:
        Tuple of (config_file, input_dir, locales_dir, output_dir).

    Exits with code 1 if paths cannot be resolved.
    """
    from src.config import ConfigHandler
    from src.constants import CONFIG, DIRS

    if args.config:
        # --config mode: read directories from JSON
        config_file = args.config
        if not os.path.isfile(config_file):
            logger.error(f"Configuration file '{config_file}' does not exist")
            sys.exit(1)

        try:
            config_handler = ConfigHandler(config_file)
            dirs = config_handler.get_directories()
        except Exception as e:
            logger.error(f"Failed to load configuration from '{config_file}': {e}")
            sys.exit(1)

        input_dir = dirs.get("screenshots", "")
        locales_dir = dirs.get("locales", "")
        output_dir = dirs.get("output", "")

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

        config_file = os.path.join(directory, CONFIG.CONFIG_FILE)
        input_dir = os.path.join(directory, DIRS.INPUT, DIRS.SCREENSHOTS)
        locales_dir = os.path.join(directory, DIRS.INPUT, DIRS.LOCALES)
        output_dir = os.path.join(directory, DIRS.OUTPUT)

        logger.info(f"Starting screenshot cropper with directory: {directory}")

    return config_file, input_dir, locales_dir, output_dir
