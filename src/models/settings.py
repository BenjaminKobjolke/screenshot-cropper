"""
Settings models for the Screenshot Cropper application.
"""
import logging

logger = logging.getLogger("screenshot_cropper")

class CropSettings:
    """Class to store crop settings."""
    
    def __init__(self, top, left=0, right=0, bottom=0):
        """
        Initialize crop settings.
        
        Args:
            top (int): Top crop margin in pixels.
            left (int, optional): Left crop margin in pixels. Defaults to 0.
            right (int, optional): Right crop margin in pixels. Defaults to 0.
            bottom (int, optional): Bottom crop margin in pixels. Defaults to 0.
        """
        self.top = top
        self.left = left
        self.right = right
        self.bottom = bottom
        self._validate()
    
    def _validate(self):
        """Validate crop settings."""
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
    
    def __repr__(self):
        """Return string representation of crop settings."""
        return f"CropSettings(top={self.top}, left={self.left}, right={self.right}, bottom={self.bottom})"


class BackgroundSettings:
    """Class to store background image settings."""

    def __init__(self, file, position_x, position_y, width, height):
        """
        Initialize background settings.

        Args:
            file (str): Background image file name.
            position_x (int): X position of the cropped image on the background.
            position_y (int): Y position of the cropped image on the background.
            width (int): Width to resize the cropped image to.
            height (int): Height to resize the cropped image to.
        """
        self.file = file
        self.position_x = position_x
        self.position_y = position_y
        self.width = width
        self.height = height
        self._validate()
    
    def _validate(self):
        """Validate background settings."""
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
    
    def __repr__(self):
        """Return string representation of background settings."""
        return (f"BackgroundSettings(file='{self.file}', position_x={self.position_x}, "
                f"position_y={self.position_y}, width={self.width}, height={self.height})")


class OverlaySettings:
    """Class to store overlay image settings."""

    def __init__(self, file, position_x=0, position_y=0):
        """
        Initialize overlay settings.

        Args:
            file (str): Overlay image file name.
            position_x (int): X position of the overlay on the final image.
            position_y (int): Y position of the overlay on the final image.
        """
        self.file = file
        self.position_x = position_x
        self.position_y = position_y
        self._validate()

    def _validate(self):
        """Validate overlay settings."""
        if self.position_x < 0:
            logger.warning(f"Invalid position_x value: {self.position_x}, setting to 0")
            self.position_x = 0
        if self.position_y < 0:
            logger.warning(f"Invalid position_y value: {self.position_y}, setting to 0")
            self.position_y = 0

    def __repr__(self):
        """Return string representation of overlay settings."""
        return (f"OverlaySettings(file='{self.file}', position_x={self.position_x}, "
                f"position_y={self.position_y})")


class ExportSettings:
    """Class to store export format settings."""

    def __init__(self, format="png", quality=90, keep_cropped=False, lossless=False):
        """
        Initialize export settings.

        Args:
            format (str): Export format ("png" or "webp"). Defaults to "png".
            quality (int): Quality for lossy formats like WebP (1-100). Defaults to 90.
            keep_cropped (bool): If True, save cropped images separately. Defaults to False.
            lossless (bool): If True, use lossless WebP compression (preserves transparency). Defaults to False.
        """
        self.format = format.lower()
        self.quality = quality
        self.keep_cropped = keep_cropped
        self.lossless = lossless
        self._validate()

    def _validate(self):
        """Validate export settings."""
        if self.format not in ["png", "webp"]:
            logger.warning(f"Invalid format value: {self.format}, setting to 'png'")
            self.format = "png"
        if self.quality < 1 or self.quality > 100:
            logger.warning(f"Invalid quality value: {self.quality}, setting to 90")
            self.quality = 90

    def __repr__(self):
        """Return string representation of export settings."""
        return f"ExportSettings(format='{self.format}', quality={self.quality}, keep_cropped={self.keep_cropped}, lossless={self.lossless})"


class TextSettings:
    """Class to store text overlay settings."""
    
    def __init__(self, font_files, font_size, align, x, y, width, height, 
                 vertical_align="top", color=(0, 0, 0), font_names=None):
        """
        Initialize text settings.
        
        Args:
            font_files (dict): Dictionary of language codes to font files.
            font_size (int): Font size in points.
            align (str): Horizontal alignment ("left", "center", or "right").
            x (int): X position of the text area.
            y (int): Y position of the text area.
            width (int): Width of the text area.
            height (int): Height of the text area.
            vertical_align (str, optional): Vertical alignment ("top", "middle", or "bottom"). 
                                           Defaults to "top".
            color (tuple, optional): RGB color tuple. Defaults to (0, 0, 0) (black).
            font_names (dict, optional): Dictionary of language codes to font names for Photoshop.
                                        Defaults to None.
        """
        self.font_files = font_files
        self.font_size = font_size
        self.align = align
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.vertical_align = vertical_align
        self.color = color
        self.font_names = font_names or {}
        self._validate()
    
    def _validate(self):
        """Validate text settings."""
        if not isinstance(self.font_files, dict) or "default" not in self.font_files:
            logger.warning("Invalid font_files value, must be a dictionary with a 'default' key")
            self.font_files = {"default": "Arial.ttf"}
        if self.font_size <= 0:
            logger.warning(f"Invalid font_size value: {self.font_size}, setting to 24")
            self.font_size = 24
        if self.align not in ["left", "center", "right"]:
            logger.warning(f"Invalid align value: {self.align}, setting to 'left'")
            self.align = "left"
        if self.vertical_align not in ["top", "middle", "bottom"]:
            logger.warning(f"Invalid vertical_align value: {self.vertical_align}, setting to 'top'")
            self.vertical_align = "top"
        if self.x < 0:
            logger.warning(f"Invalid x value: {self.x}, setting to 0")
            self.x = 0
        if self.y < 0:
            logger.warning(f"Invalid y value: {self.y}, setting to 0")
            self.y = 0
        if self.width <= 0:
            logger.warning(f"Invalid width value: {self.width}, setting to 100")
            self.width = 100
        if self.height <= 0:
            logger.warning(f"Invalid height value: {self.height}, setting to 100")
            self.height = 100
    
    def __repr__(self):
        """Return string representation of text settings."""
        return (f"TextSettings(font_files={self.font_files}, font_size={self.font_size}, "
                f"align='{self.align}', vertical_align='{self.vertical_align}', "
                f"x={self.x}, y={self.y}, width={self.width}, height={self.height}, "
                f"color={self.color})")
