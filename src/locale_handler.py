"""
Locale handler module for the Screenshot Cropper application.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger("screenshot_cropper")


class LocaleHandler:
    """Handler for locale files."""

    def __init__(self, locales_dir: str, language_filter: str | None = None) -> None:
        """Initialize the LocaleHandler.

        Args:
            locales_dir: Directory containing locale files.
            language_filter: Only load this specific language.
        """
        self.locales_dir = locales_dir
        self.language_filter = language_filter
        self.locales: dict[str, dict[str, str] | list[str]] = self._load_locales()

    def _load_locales(self) -> dict[str, dict[str, str] | list[str]]:
        """Load all locale files from the locales directory.

        Returns:
            Dictionary of locale codes to text dictionaries or arrays.
        """
        locales: dict[str, Any] = {}

        if not os.path.isdir(self.locales_dir):
            logger.warning(f"Locales directory not found: {self.locales_dir}")
            return locales

        for filename in os.listdir(self.locales_dir):
            if filename.endswith(".json"):
                locale_code = os.path.splitext(filename)[0]  # e.g., "en" from "en.json"

                # If language filter is set, skip locales that don't match
                if self.language_filter and locale_code != self.language_filter:
                    logger.debug(
                        f"Skipping locale {locale_code} (filter: {self.language_filter})"
                    )
                    continue

                locale_path = os.path.join(self.locales_dir, filename)

                try:
                    with open(locale_path, "r", encoding="utf-8") as f:
                        locale_data = json.load(f)

                        # Store the data as-is, whether it's a dictionary or an array
                        locales[locale_code] = locale_data

                        if isinstance(locale_data, dict):
                            logger.info(
                                f"Loaded locale: {locale_code} with "
                                f"{len(locale_data)} texts (dictionary format)"
                            )
                        else:
                            logger.info(
                                f"Loaded locale: {locale_code} with "
                                f"{len(locale_data)} texts (array format)"
                            )
                except Exception as e:
                    logger.error(f"Failed to load locale file {filename}: {e}")

        return locales

    def get_locales(self) -> list[str]:
        """Get all loaded locale codes.

        Returns:
            List of locale codes.
        """
        return list(self.locales.keys())

    def get_text(self, locale_code: str, index: int, add_one: bool = True) -> str | None:
        """Get text for a specific locale and index.

        Args:
            locale_code: Locale code (e.g., "en").
            index: Index of the text in the locale array or key in the dictionary.
            add_one: Whether to add 1 to the index when forming the key.
                Defaults to True for backward compatibility.

        Returns:
            Text for the specified locale and index, or None if not found.
        """
        if locale_code not in self.locales:
            logger.warning(f"Locale not found: {locale_code}")
            return None

        texts = self.locales[locale_code]

        # Handle dictionary format
        if isinstance(texts, dict):
            # Try to get text using "Text_X" format
            key_index = index + 1 if add_one else index
            key = f"Text_{key_index}"
            if key in texts:
                return texts[key]

            # If not found, try to get text using index as string
            if str(index) in texts:
                return texts[str(index)]

            # If still not found, log warning
            logger.warning(f"Text key '{key}' not found in locale {locale_code}")
            return None

        # Handle array format
        else:
            if index >= len(texts):
                logger.warning(
                    f"Text index {index} out of range for locale {locale_code} "
                    f"(max: {len(texts) - 1})"
                )
                return None

            return texts[index]

    def get_translation(self, locale_code: str, key: str) -> str | None:
        """Get translation for a specific locale and key.

        Args:
            locale_code: Locale code (e.g., "en").
            key: Translation key.

        Returns:
            Translation text, or None if not found.
        """
        if locale_code not in self.locales:
            logger.warning(f"Locale not found: {locale_code}")
            return None

        texts = self.locales[locale_code]

        if not isinstance(texts, dict):
            logger.warning(f"Locale {locale_code} is not in dictionary format")
            return None

        return texts.get(key)
