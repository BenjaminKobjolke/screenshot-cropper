"""
Logger module for the Screenshot Cropper application.
"""
from __future__ import annotations

import logging
import sys


def setup_logger() -> logging.Logger:
    """Set up and configure the logger.

    Returns:
        Configured logger instance.
    """
    # Create logger
    logger = logging.getLogger("screenshot_cropper")
    logger.setLevel(logging.INFO)

    # Create console handler and set level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Add formatter to console handler
    console_handler.setFormatter(formatter)

    # Add console handler to logger
    logger.addHandler(console_handler)

    return logger
