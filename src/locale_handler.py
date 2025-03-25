"""
Locale handler module for the Screenshot Cropper application.
"""
import json
import logging
import os

logger = logging.getLogger("screenshot_cropper")

class LocaleHandler:
    """Handler for locale files."""
    
    def __init__(self, locales_dir):
        """
        Initialize the LocaleHandler.
        
        Args:
            locales_dir (str): Directory containing locale files.
        """
        self.locales_dir = locales_dir
        self.locales = self._load_locales()
    
    def _load_locales(self):
        """
        Load all locale files from the locales directory.
        
        Returns:
            dict: Dictionary of locale codes to text dictionaries or arrays.
        """
        locales = {}
        
        if not os.path.isdir(self.locales_dir):
            logger.warning(f"Locales directory not found: {self.locales_dir}")
            return locales
            
        for filename in os.listdir(self.locales_dir):
            if filename.endswith('.json'):
                locale_code = os.path.splitext(filename)[0]  # e.g., "en" from "en.json"
                locale_path = os.path.join(self.locales_dir, filename)
                
                try:
                    with open(locale_path, 'r', encoding='utf-8') as f:
                        locale_data = json.load(f)
                        
                        # Store the data as-is, whether it's a dictionary or an array
                        locales[locale_code] = locale_data
                        
                        if isinstance(locale_data, dict):
                            logger.info(f"Loaded locale: {locale_code} with {len(locale_data)} texts (dictionary format)")
                        else:
                            logger.info(f"Loaded locale: {locale_code} with {len(locale_data)} texts (array format)")
                except Exception as e:
                    logger.error(f"Failed to load locale file {filename}: {e}")
        
        return locales
    
    def get_locales(self):
        """
        Get all loaded locale codes.
        
        Returns:
            list: List of locale codes.
        """
        return list(self.locales.keys())
    
    def get_text(self, locale_code, index, add_one=True):
        """
        Get text for a specific locale and index.
        
        Args:
            locale_code (str): Locale code (e.g., "en").
            index (int): Index of the text in the locale array or key in the dictionary.
            add_one (bool, optional): Whether to add 1 to the index when forming the key. 
                                     Defaults to True for backward compatibility.
            
        Returns:
            str: Text for the specified locale and index, or None if not found.
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
                logger.warning(f"Text index {index} out of range for locale {locale_code} (max: {len(texts) - 1})")
                return None
                
            return texts[index]
