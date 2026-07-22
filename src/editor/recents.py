"""
Persistent recent-projects store for the editor (Qt-free).
"""
from __future__ import annotations

import json
import logging
import os

from src.constants import CONFIG

logger = logging.getLogger("screenshot_cropper")

MAX_RECENT = 10
_DEFAULT_STORAGE = os.path.join(
    os.path.expanduser("~"), ".screenshot-cropper", "recent_projects.json"
)


class RecentProjects:
    """Stores the most recently opened project directories as a JSON list."""

    def __init__(self, storage_file: str | None = None) -> None:
        """
        Args:
            storage_file: Path to the JSON store; defaults to a per-user file.
        """
        self.storage_file = storage_file or _DEFAULT_STORAGE

    def load(self) -> list[str]:
        """Return recent project directories, most recent first.

        Entries whose config file no longer exists are filtered out.
        """
        try:
            with open(self.storage_file, encoding="utf-8") as f:
                entries = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            if not isinstance(e, FileNotFoundError):
                logger.warning(f"Could not read recent projects: {e}")
            return []
        if not isinstance(entries, list):
            return []
        return [
            d for d in entries
            if isinstance(d, str) and os.path.isfile(os.path.join(d, CONFIG.CONFIG_FILE))
        ]

    def add(self, directory: str) -> None:
        """Record a project directory as most recently used.

        Args:
            directory: Project base directory that was opened.
        """
        directory = os.path.normpath(directory)
        entries = [d for d in self.load() if os.path.normpath(d) != directory]
        entries.insert(0, directory)
        entries = entries[:MAX_RECENT]
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.warning(f"Could not save recent projects: {e}")
