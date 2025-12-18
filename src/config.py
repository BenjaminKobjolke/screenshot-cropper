"""
Configuration handler for the Screenshot Cropper application.
"""
import json
import logging
from src.models.settings import CropSettings, BackgroundSettings, TextSettings, OverlaySettings, ExportSettings

logger = logging.getLogger("screenshot_cropper")

class ConfigHandler:
    """Handler for configuration file operations."""
    
    def __init__(self, config_file):
        """
        Initialize the ConfigHandler.
        
        Args:
            config_file (str): Path to the configuration file.
        """
        self.config_file = config_file
        self.config_data = self._load_config()
    
    def _load_config(self):
        """
        Load configuration from file.
        
        Returns:
            dict: Configuration data.
        
        Raises:
            FileNotFoundError: If the configuration file does not exist.
            json.JSONDecodeError: If the configuration file is not valid JSON.
        """
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    def get_crop_settings(self):
        """
        Get crop settings from configuration.
        
        Returns:
            CropSettings: Crop settings object.
        
        Raises:
            KeyError: If required crop settings are missing.
        """
        try:
            # Check if crop settings are under the "crop" key
            if "crop" in self.config_data:
                crop_data = self.config_data["crop"]
                top = crop_data.get("top", 0)
                left = crop_data.get("left", 0)
                right = crop_data.get("right", 0)
                bottom = crop_data.get("bottom", 0)
            else:
                # Fallback to old format for backward compatibility
                logger.warning("Using deprecated JSON format. Please update to new format with 'crop' key.")
                top = self.config_data.get("top", 0)
                left = self.config_data.get("left", 0)
                right = self.config_data.get("right", 0)
                bottom = self.config_data.get("bottom", 0)
            
            return CropSettings(top=top, left=left, right=right, bottom=bottom)
        except KeyError as e:
            logger.error(f"Missing required crop setting: {e}")
            raise
    
    def get_background_settings(self):
        """
        Get background settings from configuration.
        
        Returns:
            BackgroundSettings: Background settings object, or None if not configured.
        
        Raises:
            KeyError: If required background settings are missing.
        """
        try:
            # Check if background settings are present
            if "background" not in self.config_data:
                return None
            
            bg_data = self.config_data["background"]
            
            # Check for required fields
            if "file" not in bg_data:
                logger.error("Missing required background setting: file")
                return None
            
            # Get position settings
            position = bg_data.get("position", {})
            position_x = position.get("x", 0)
            position_y = position.get("y", 0)
            
            # Get size settings
            size = bg_data.get("size", {})
            width = size.get("width", 100)
            height = size.get("height", 100)

            return BackgroundSettings(
                file=bg_data["file"],
                position_x=position_x,
                position_y=position_y,
                width=width,
                height=height
            )
        except KeyError as e:
            logger.error(f"Missing required background setting: {e}")
            return None

    def get_overlay_settings(self):
        """
        Get overlay settings from configuration.

        Returns:
            OverlaySettings: Overlay settings object, or None if not configured.
        """
        try:
            # Check if overlay settings are present at top level
            if "overlay" not in self.config_data:
                return None

            overlay_data = self.config_data["overlay"]

            # Check for required fields
            if "file" not in overlay_data:
                logger.error("Missing required overlay setting: file")
                return None

            # Get position settings (default to 0,0)
            position = overlay_data.get("position", {})
            position_x = position.get("x", 0)
            position_y = position.get("y", 0)

            return OverlaySettings(
                file=overlay_data["file"],
                position_x=position_x,
                position_y=position_y
            )
        except KeyError as e:
            logger.error(f"Missing required overlay setting: {e}")
            return None

    def get_text_settings(self):
        """
        Get text settings from configuration.

        Returns:
            TextSettings: Text settings object, or None if not configured.

        Raises:
            KeyError: If required text settings are missing.
        """
        try:
            # Check if text settings are present
            if "text" not in self.config_data:
                return None

            text_data = self.config_data["text"]

            # Get font settings
            font_data = text_data.get("font", {})

            # Get font properties
            font_files = font_data.get("files", {"default": "Arial.ttf"})
            if "default" not in font_files:
                logger.warning("No default font specified, using Arial.ttf")
                font_files["default"] = "Arial.ttf"

            # Get font names for Photoshop
            font_names = font_data.get("names", {})

            font_size = font_data.get("size", 24)

            # Get alignment settings
            align = font_data.get("align", "left")
            vertical_align = font_data.get("vertical-align", "top")

            # Get position and size
            x = font_data.get("x", 0)
            y = font_data.get("y", 0)
            width = font_data.get("width", 100)
            height = font_data.get("height", 100)

            # Get color (default is black)
            color_data = font_data.get("color", {})
            r = color_data.get("r", 0)
            g = color_data.get("g", 0)
            b = color_data.get("b", 0)
            color = (r, g, b)

            return TextSettings(
                font_files=font_files,
                font_size=font_size,
                align=align,
                vertical_align=vertical_align,
                x=x,
                y=y,
                width=width,
                height=height,
                color=color,
                font_names=font_names
            )
        except KeyError as e:
            logger.error(f"Missing required text setting: {e}")
            return None

    def get_directories(self):
        """
        Get directory settings from configuration.

        Returns:
            dict: Dictionary with keys 'screenshots', 'locales', 'output'.
                  Values are None if not configured.
        """
        directories = self.config_data.get("directories", {})
        return {
            'screenshots': directories.get("screenshots"),
            'locales': directories.get("locales"),
            'output': directories.get("output")
        }

    def get_export_settings(self):
        """
        Get export settings from configuration.

        Returns:
            ExportSettings: Export settings object with format, quality, and keep_cropped.
        """
        if "export" not in self.config_data:
            return ExportSettings()  # defaults to PNG, quality 90, keep_cropped False

        export_data = self.config_data["export"]
        return ExportSettings(
            format=export_data.get("format", "png"),
            quality=export_data.get("quality", 90),
            keep_cropped=export_data.get("keep_cropped", False),
            lossless=export_data.get("lossless", False)
        )
