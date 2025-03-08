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
            # Get crop settings with defaults for missing values
            top = self.config_data.get("top", 0)
            left = self.config_data.get("left", 0)
            right = self.config_data.get("right", 0)
            bottom = self.config_data.get("bottom", 0)
            
            return CropSettings(top=top, left=left, right=right, bottom=bottom)
        except KeyError as e:
            logger.error(f"Missing required crop setting: {e}")
            raise
