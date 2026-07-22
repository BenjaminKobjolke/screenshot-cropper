"""
Editor application entry point (PySide6).
"""
from __future__ import annotations

import logging

logger = logging.getLogger("screenshot_cropper")


def launch_editor(base_dir: str, config_file: str) -> None:
    """Launch the PySide6 editor for a project directory.

    Args:
        base_dir: Project base directory.
        config_file: Path to screenshot-cropper.json inside it.
    """
    # Imported here so the headless pipeline never loads Qt
    from PySide6.QtWidgets import QApplication

    from src.editor.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(base_dir, config_file)
    window.show()
    app.exec()
