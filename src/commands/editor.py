"""Editor mode command handler."""
from __future__ import annotations

import logging
import os
import sys

from src.constants import CONFIG


def run_editor(directory: str, logger: logging.Logger) -> None:
    """Launch the visual editor for configuration.

    Args:
        directory: Base directory containing the project.
        logger: Logger instance.

    Exits with code 0 on success, 1 on failure.
    """
    if not os.path.isdir(directory):
        logger.error(f"Directory '{directory}' does not exist")
        sys.exit(1)

    config_file = os.path.join(directory, CONFIG.CONFIG_FILE)
    logger.info(f"Launching visual editor for: {directory}")

    from src.editor.editor_window import launch_editor
    launch_editor(directory, config_file)
    sys.exit(0)
