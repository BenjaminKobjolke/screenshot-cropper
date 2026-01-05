"""
InDesign processor for handling .indd files via COM automation.
"""
from __future__ import annotations

import json
import logging
import os
import re

logger = logging.getLogger("screenshot_cropper")

# Known InDesign COM version strings to try (generic first = uses system default/newest)
INDESIGN_VERSIONS = [
    "InDesign.Application",  # Generic - uses system default (usually newest)
    "InDesign.Application.2026",  # Version 21.x
    "InDesign.Application.2025",  # Version 20.x
    "InDesign.Application.2024",  # Version 19.x
    "InDesign.Application.2023",  # Version 18.x
    "InDesign.Application.CC.2022",
    "InDesign.Application.CC.2021",
    "InDesign.Application.CC.2020",
    "InDesign.Application.CC.2019",
    "InDesign.Application.CC.2018",
    "InDesign.Application.CC.2017",
]


class InDesignProcessor:
    """Handler for InDesign file processing operations."""

    def __init__(self, locale_handler: object | None = None) -> None:
        """Initialize the InDesign processor.

        Args:
            locale_handler: Optional locale handler for translations.
        """
        self.locale_handler = locale_handler
        self.app = None

    @staticmethod
    def list_available_versions() -> str | None:
        """List available InDesign versions and return the first working one.

        Returns:
            The COM version string that works, or None if none found.
        """
        try:
            import win32com.client
        except ImportError:
            logger.error("win32com not available. Install with: pip install pypiwin32")
            print("ERROR: win32com not available. Install with: pip install pypiwin32")
            return None

        print("Checking available InDesign versions...")
        print("-" * 50)

        working_version = None

        for version_string in INDESIGN_VERSIONS:
            try:
                app = win32com.client.Dispatch(version_string)
                version_number = app.Version if hasattr(app, "Version") else "unknown"
                print(f"SUCCESS: {version_string} (Version: {version_number})")
                if working_version is None:
                    working_version = version_string
            except Exception:
                print(f"Not found: {version_string}")

        print("-" * 50)
        if working_version:
            print(f"Recommended version string: {working_version}")
        else:
            print("No InDesign installation found.")

        return working_version

    def _connect_to_indesign(self) -> object:
        """Connect to InDesign application.

        Returns:
            The InDesign application COM object.

        Raises:
            ImportError: If win32com is not available.
            RuntimeError: If no InDesign installation is found.
        """
        try:
            import win32com.client
        except ImportError as e:
            logger.error("win32com not available. Install with: pip install pypiwin32")
            raise ImportError(
                "win32com not available. Install with: pip install pypiwin32"
            ) from e

        # Try each version string until one works
        for version_string in INDESIGN_VERSIONS:
            try:
                self.app = win32com.client.Dispatch(version_string)
                version_number = (
                    self.app.Version if hasattr(self.app, "Version") else "unknown"
                )
                logger.info(
                    f"Connected to InDesign: {version_string} (Version: {version_number})"
                )
                return self.app
            except Exception:
                continue

        raise RuntimeError(
            "Could not connect to InDesign. "
            "Ensure InDesign is installed and run --list-indesign-versions to check."
        )

    def _color_to_hex(self, color: object) -> str:
        """Convert an InDesign color object to hex string.

        Args:
            color: InDesign color COM object.

        Returns:
            Hex color string (e.g., "#000000") or "none" if not applicable.
        """
        try:
            # Check if it's a valid color object
            if color is None:
                return "none"

            # Try to get color value - InDesign colors have different types
            color_name = str(color.Name) if hasattr(color, "Name") else ""

            # Handle named colors
            if color_name.lower() in ("none", "[none]"):
                return "none"
            if color_name.lower() in ("black", "[black]"):
                return "#000000"
            if color_name.lower() in ("white", "[white]"):
                return "#ffffff"

            # Try to get RGB values if available
            if hasattr(color, "ColorValue"):
                values = color.ColorValue
                # Check color space
                space = color.Space if hasattr(color, "Space") else None

                # RGB color space (value 1919248498 or similar)
                if len(values) >= 3:
                    r, g, b = int(values[0]), int(values[1]), int(values[2])
                    return f"#{r:02x}{g:02x}{b:02x}"

            # Fallback: return the color name
            return color_name if color_name else "unknown"

        except Exception as e:
            logger.debug(f"Could not convert color: {e}")
            return "unknown"

    def _extract_text_ranges(self, text_frame: object) -> list[dict]:
        """Extract text style ranges with formatting from a text frame.

        Args:
            text_frame: InDesign text frame COM object.

        Returns:
            List of dictionaries, each containing text and formatting properties.
        """
        ranges = []

        try:
            text_style_ranges = text_frame.TextStyleRanges
            range_count = text_style_ranges.Count

            for i in range(range_count):
                try:
                    # InDesign uses 1-based indexing
                    style_range = text_style_ranges.Item(i + 1)

                    # Extract text content
                    text = style_range.Contents if hasattr(style_range, "Contents") else ""

                    # Skip empty ranges
                    if not text:
                        continue

                    # Extract formatting properties
                    range_data = {
                        "text": text,
                        "fontStyle": self._get_font_style(style_range),
                        "pointSize": self._get_point_size(style_range),
                        "appliedFont": self._get_applied_font(style_range),
                        "underline": self._get_bool_prop(style_range, "Underline"),
                        "strikeThru": self._get_bool_prop(style_range, "StrikeThru"),
                        "fillColor": self._get_fill_color(style_range),
                        "baselineShift": self._get_float_prop(style_range, "BaselineShift"),
                    }

                    ranges.append(range_data)

                except Exception as range_error:
                    logger.debug(f"Error extracting range {i + 1}: {range_error}")

        except Exception as e:
            logger.debug(f"Error extracting text ranges: {e}")

        return ranges

    def _get_font_style(self, style_range: object) -> str:
        """Get font style (Regular, Bold, Italic, etc.) from a style range."""
        try:
            if hasattr(style_range, "FontStyle"):
                return str(style_range.FontStyle)
        except Exception:
            pass
        return "Regular"

    def _get_point_size(self, style_range: object) -> float:
        """Get point size from a style range."""
        try:
            if hasattr(style_range, "PointSize"):
                return float(style_range.PointSize)
        except Exception:
            pass
        return 12.0

    def _get_applied_font(self, style_range: object) -> str:
        """Get applied font name from a style range."""
        try:
            if hasattr(style_range, "AppliedFont"):
                font = style_range.AppliedFont
                if hasattr(font, "Name"):
                    return str(font.Name)
                return str(font)
        except Exception:
            pass
        return "Unknown"

    def _get_bool_prop(self, style_range: object, prop_name: str) -> bool:
        """Get a boolean property from a style range."""
        try:
            if hasattr(style_range, prop_name):
                return bool(getattr(style_range, prop_name))
        except Exception:
            pass
        return False

    def _get_float_prop(self, style_range: object, prop_name: str) -> float:
        """Get a float property from a style range."""
        try:
            if hasattr(style_range, prop_name):
                return float(getattr(style_range, prop_name))
        except Exception:
            pass
        return 0.0

    def _get_fill_color(self, style_range: object) -> str:
        """Get fill color as hex string from a style range."""
        try:
            if hasattr(style_range, "FillColor"):
                return self._color_to_hex(style_range.FillColor)
        except Exception:
            pass
        return "#000000"

    def _sanitize_layer_name(self, name: str) -> str:
        """Sanitize a name for use as a translation key.

        Rules:
        - Convert to lowercase
        - Replace spaces with underscores
        - Keep only a-z, 0-9, underscore, dot, and hyphen
        - Limit to 30 characters, truncating at word boundaries when possible

        Args:
            name: Original text content.

        Returns:
            Sanitized name for use as translation key.
        """
        # Convert to lowercase
        sanitized = name.lower()

        # Strip all existing "lang_" prefixes to avoid duplication
        while sanitized.startswith("lang_"):
            sanitized = sanitized[5:]  # Remove "lang_" (5 chars)

        # Replace spaces with underscores
        sanitized = sanitized.replace(" ", "_")

        # Keep only a-z, 0-9, underscore, dot, and hyphen
        sanitized = re.sub(r"[^a-z0-9._-]", "", sanitized)

        # Limit to 30 characters, truncating at word boundaries
        if len(sanitized) > 30:
            # Find the last underscore within the 30-character limit
            truncated = sanitized[:30]
            last_underscore = truncated.rfind("_")

            if last_underscore > 0:
                # Truncate at the last underscore to end on a complete word
                sanitized = sanitized[:last_underscore]
            else:
                # No underscore found, use hard truncation
                sanitized = truncated

        return sanitized

    def _prepare_text_frames(self, doc: object, template: dict) -> None:
        """Iterate all text frames, rename labels, and populate template.

        Args:
            doc: InDesign document COM object.
            template: Template dictionary to populate.
        """
        logger.info("Processing all text frames for template preparation")

        try:
            text_frames = doc.TextFrames
            frame_count = text_frames.Count

            logger.info(f"Found {frame_count} text frames in document")

            for i in range(frame_count):
                try:
                    # InDesign uses 1-based indexing for Item()
                    text_frame = text_frames.Item(i + 1)
                    self._process_text_frame_for_template(text_frame, template)
                except Exception as frame_error:
                    logger.warning(f"Error processing text frame {i + 1}: {frame_error}")

        except Exception as e:
            logger.error(f"Error accessing text frames: {e}")

    def _process_text_frame_for_template(
        self, text_frame: object, template: dict
    ) -> None:
        """Process a single text frame: rename its label and add to template.

        Args:
            text_frame: InDesign text frame COM object.
            template: Template dictionary to populate.
        """
        try:
            # Get current text content
            text_content = text_frame.Contents if hasattr(text_frame, "Contents") else ""

            # Skip empty text frames
            if not text_content or not text_content.strip():
                return

            original_label = (
                text_frame.Label if hasattr(text_frame, "Label") else ""
            )
            logger.info(
                f"Found text frame with content: '{text_content[:50]}...' "
                f"(label: '{original_label}')"
            )

            # Sanitize the text content to create the key
            sanitized_name = self._sanitize_layer_name(text_content)

            # Handle duplicate keys - only add suffix if plain text content differs
            base_name = sanitized_name
            counter = 2
            while sanitized_name in template:
                existing = template[sanitized_name]
                existing_plain = (
                    existing.get("plainText", existing)
                    if isinstance(existing, dict)
                    else existing
                )
                if existing_plain == text_content:
                    break
                sanitized_name = f"{base_name}_{counter}"
                counter += 1

            # Create new label name
            new_label = f"lang_{sanitized_name}"

            # Set the label on the text frame
            text_frame.Label = new_label
            logger.info(f"Set text frame label to '{new_label}'")

            # Extract text ranges with formatting
            ranges = self._extract_text_ranges(text_frame)

            # Build structured template entry
            template_entry = {
                "plainText": text_content,
                "ranges": ranges,
            }

            # Add/update in template
            template[sanitized_name] = template_entry
            logger.info(
                f"Added to template: {sanitized_name} = '{text_content[:50]}...' "
                f"({len(ranges)} style ranges)"
            )

        except Exception as e:
            logger.warning(f"Error processing text frame: {e}")

    def prepare_and_export_template(
        self, indd_path: str, output_json_path: str
    ) -> bool:
        """Prepare an InDesign file by labeling text frames and exporting a template.

        This method:
        1. Loads existing template.json if it exists
        2. Opens the InDesign file
        3. Traverses all text frames
        4. Sets each text frame's Label to lang_[sanitized_name]
        5. Exports/updates template.json with text content
        6. Saves the modified InDesign file

        Args:
            indd_path: Path to the InDesign file.
            output_json_path: Path to save the template JSON file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            logger.info(f"Preparing InDesign file and exporting template: {indd_path}")

            # Load existing template if it exists
            template: dict = {}
            if os.path.exists(output_json_path):
                try:
                    with open(output_json_path, "r", encoding="utf-8") as f:
                        template = json.load(f)
                    logger.info(f"Loaded existing template with {len(template)} keys")
                except Exception as load_error:
                    logger.warning(f"Could not load existing template: {load_error}")

            # Get absolute paths
            abs_indd_path = os.path.abspath(indd_path)
            abs_output_path = os.path.abspath(output_json_path)

            logger.info(f"Absolute INDD path: {abs_indd_path}")
            logger.info(f"Absolute template output path: {abs_output_path}")

            # Connect to InDesign
            self._connect_to_indesign()

            # Get version info for metadata
            app_version = self.app.Version if hasattr(self.app, "Version") else "unknown"

            # Open the document
            logger.info(f"Opening InDesign file: {abs_indd_path}")
            doc = self.app.Open(abs_indd_path)

            try:
                # Add metadata to template
                template["_meta"] = {
                    "application": "Adobe InDesign",
                    "version": str(app_version),
                    "sourceFile": os.path.basename(abs_indd_path),
                }

                # Process all text frames
                self._prepare_text_frames(doc, template)

                # Save the template JSON
                output_dir = os.path.dirname(abs_output_path)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                with open(abs_output_path, "w", encoding="utf-8") as f:
                    json.dump(template, f, indent=4, ensure_ascii=False, sort_keys=True)
                logger.info(
                    f"Exported template with {len(template)} keys to: {abs_output_path}"
                )

                # Save the modified InDesign file
                logger.info(f"Saving modified InDesign file: {abs_indd_path}")
                doc.Save()
                logger.info("InDesign file saved successfully")

            finally:
                # Close the document
                logger.info("Closing document")
                doc.Close()

            return True

        except ImportError as import_error:
            logger.error(f"win32com not available: {import_error}")
            logger.error("This feature requires InDesign and pypiwin32")
            return False

        except Exception as e:
            logger.error(f"Error preparing InDesign file {indd_path}: {e}")
            return False
