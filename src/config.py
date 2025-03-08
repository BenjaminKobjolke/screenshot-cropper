"""
Configuration handler for the Screenshot Cropper application.
"""
import json
import logging
from dataclasses import dataclass

logger = logging.getLogger("screenshot_cropper")

@dataclass
class CropSettings:
    """Class to store crop settings."""
    top: int
    left: int = 0
    right: int = 0
    bottom: int = 0
    
    def __post_init__(self):
        """Validate crop settings after initialization."""
        if self.top < 0:
            logger.warning(f"Invalid top value: {self.top}, setting to 0")
            self.top = 0
        if self.left < 0:
            logger.warning(f"Invalid left value: {self.left}, setting to 0")
            self.left = 0
        if self.right < 0:
            logger.warning(f"Invalid right value: {self.right}, setting to 0")
            self.right = 0
        if self.bottom < 0:
            logger.warning(f"Invalid bottom value: {self.bottom}, setting to 0")
            self.bottom = 0

@dataclass
class BackgroundSettings:
    """Class to store background image settings."""
    file: str
    position_x: int
    position_y: int
    width: int
    height: int
    
    def __post_init__(self):
        """Validate background settings after initialization."""
        if self.position_x < 0:
            logger.warning(f"Invalid position_x value: {self.position_x}, setting to 0")
            self.position_x = 0
        if self.position_y < 0:
            logger.warning(f"Invalid position_y value: {self.position_y}, setting to 0")
            self.position_y = 0
        if self.width <= 0:
            logger.warning(f"Invalid width value: {self.width}, setting to 100")
            self.width = 100
        if self.height <= 0:
            logger.warning(f"Invalid height value: {self.height}, setting to 100")
            self.height = 100

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
