"""
Main window of the screenshot-cropper editor.
"""
from __future__ import annotations

import logging
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.config import ConfigHandler
from src.config_writer import ConfigWriter
from src.constants import CONFIG
from src.editor.panels_layout import BackgroundPanel, CropPanel, MaskPanel, OverlayPanel
from src.editor.panels_style import ExportPanel, TextPanel
from src.editor.preview import PreviewWidget
from src.editor.recents import RecentProjects
from src.editor.renderer import PreviewRenderer
from src.editor.sources import discover_screenshots, load_locales
from src.editor.state import EditorState

logger = logging.getLogger("screenshot_cropper")


class MainWindow(QMainWindow):
    """Editor window: settings panels on the left, live preview on the right."""

    def __init__(self, base_dir: str, config_file: str,
                 recents: RecentProjects | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Screenshot Cropper Editor")
        self.resize(1280, 900)
        self.setStatusBar(QStatusBar(self))
        self._build_menu()
        self._toolbar = QToolBar("Sources", self)
        self.addToolBar(self._toolbar)
        self.state: EditorState | None = None
        self.recents = recents or RecentProjects()
        self.load_project(base_dir, config_file)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        open_action = QAction("&Open Directory...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_directory)
        file_menu.addAction(open_action)
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def load_project(self, base_dir: str, config_file: str) -> None:
        """(Re)load a project directory and rebuild the whole UI.

        Args:
            base_dir: Project base directory.
            config_file: Path to screenshot-cropper.json inside it.
        """
        if not os.path.isfile(config_file):
            logger.warning(f"Configuration file not found: {config_file}")
            self._toolbar.clear()
            self.setCentralWidget(self._build_start_page(base_dir))
            self.state = None
            self.statusBar().showMessage("No project loaded")
            return

        self.base_dir = base_dir
        self.state = EditorState(
            base_dir=base_dir,
            config_handler=ConfigHandler(config_file),
            config_writer=ConfigWriter(config_file),
        )
        self.screenshots = discover_screenshots(base_dir)
        self.locale_handler = load_locales(base_dir)

        self.renderer = PreviewRenderer(self.state, parent=self)
        self.renderer.locale_handler = self.locale_handler
        self._build_toolbar()
        self._build_central()
        self.renderer.rendered.connect(self.preview.set_image)
        self._select_sources()
        self.recents.add(base_dir)
        self.statusBar().showMessage(f"Loaded: {config_file}")

    def _build_start_page(self, base_dir: str) -> QWidget:
        """Start page: hint plus large buttons for the recent projects."""
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(80, 40, 80, 40)
        layout.setSpacing(10)

        hint = QLabel(
            f"No {CONFIG.CONFIG_FILE} found in:\n{base_dir}\n\n"
            "Open a recent project or use File > Open Directory...", page
        )
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        recent_dirs = self.recents.load()
        self.recent_buttons: list[QPushButton] = []
        if recent_dirs:
            title = QLabel("Recent projects", page)
            title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 12px;")
            layout.addWidget(title)
        for directory in recent_dirs:
            button = QPushButton(f"{os.path.basename(directory)}\n{directory}", page)
            button.setMinimumHeight(56)
            button.setStyleSheet("font-size: 14px; text-align: left; padding: 8px 16px;")
            button.clicked.connect(
                lambda _=False, d=directory: self.load_project(
                    d, os.path.join(d, CONFIG.CONFIG_FILE)
                )
            )
            layout.addWidget(button)
            self.recent_buttons.append(button)
        layout.addStretch(1)
        return page

    def _build_toolbar(self) -> None:
        self._toolbar.clear()
        self._toolbar.addWidget(QLabel(" Screenshot: "))
        self.screenshot_combo = QComboBox(self)
        self.screenshot_combo.addItems([e.name for e in self.screenshots])
        self.screenshot_combo.currentIndexChanged.connect(self._select_sources)
        self._toolbar.addWidget(self.screenshot_combo)
        self._toolbar.addWidget(QLabel(" Locale: "))
        self.locale_combo = QComboBox(self)
        if self.locale_handler:
            self.locale_combo.addItems(sorted(self.locale_handler.get_locales()))
        self.locale_combo.currentIndexChanged.connect(self._select_sources)
        self._toolbar.addWidget(self.locale_combo)

    def _build_central(self) -> None:
        state = self.state
        if state is None:
            return
        self.crop_panel = CropPanel(state.crop, title="Screenshot Crop")
        self.background_panel = BackgroundPanel(state.background, self.base_dir)
        self.mask_panel = MaskPanel(state.screenshot_mask, self.base_dir)
        self.overlay_panel = OverlayPanel(state.overlay, self.base_dir)
        self.final_crop_panel = CropPanel(state.final_crop, title="Final Image Crop")
        self.text_panel = TextPanel(state.text)
        self.export_panel = ExportPanel(state.export)
        self._panels = (self.crop_panel, self.mask_panel, self.background_panel,
                        self.overlay_panel, self.final_crop_panel, self.text_panel,
                        self.export_panel)

        panel_container = QWidget(self)
        layout = QVBoxLayout(panel_container)
        for panel in self._panels:
            panel.changed.connect(self._on_settings_changed)
            layout.addWidget(panel)
        layout.addStretch(1)

        scroll = QScrollArea(self)
        scroll.setWidget(panel_container)
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(360)

        self.preview = PreviewWidget(self)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(scroll)
        splitter.addWidget(self.preview)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

    def _sync_state_from_panels(self) -> None:
        state = self.state
        if state is None:
            return
        state.crop = self.crop_panel.values()
        state.final_crop = self.final_crop_panel.values()
        state.screenshot_mask = self.mask_panel.values()
        state.background = self.background_panel.values()
        state.overlay = self.overlay_panel.values()
        state.text = self.text_panel.values()
        state.export = self.export_panel.values()

    def _on_settings_changed(self) -> None:
        self._sync_state_from_panels()
        self.renderer.request()

    def _select_sources(self) -> None:
        index = self.screenshot_combo.currentIndex()
        self.renderer.entry = self.screenshots[index] if 0 <= index < len(self.screenshots) else None
        locale = self.locale_combo.currentText()
        self.renderer.locale = locale or None
        self.renderer.request()

    def _open_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Open project directory")
        if not directory:
            return
        config_file = os.path.join(directory, CONFIG.CONFIG_FILE)
        if not os.path.isfile(config_file):
            QMessageBox.warning(self, "No config",
                                f"No {CONFIG.CONFIG_FILE} found in:\n{directory}")
            return
        self.load_project(directory, config_file)

    def save(self) -> None:
        """Persist the current settings back to the config file."""
        if self.state is None:
            self.statusBar().showMessage("No project loaded — nothing to save")
            return
        self._sync_state_from_panels()
        self.state.save()
        self.statusBar().showMessage("Configuration saved")
