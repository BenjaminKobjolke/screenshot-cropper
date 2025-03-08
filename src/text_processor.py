"""
Text processor module for the Screenshot Cropper application.
"""
import logging
import os
from PIL import ImageDraw, ImageFont

logger = logging.getLogger("screenshot_cropper")

class TextProcessor:
    """Handler for text processing operations."""
    
    def __init__(self, text_settings):
        """
        Initialize the TextProcessor.
        
        Args:
            text_settings (TextSettings): Text settings to apply.
        """
        self.text_settings = text_settings
        self.current_locale = None
    
    def draw_text(self, img, text, locale=None):
        """
        Draw text on the image.
        
        Args:
            img (PIL.Image.Image): Image to draw text on.
            text (str): Text to draw.
            locale (str, optional): Locale code for font selection.
            
        Returns:
            PIL.Image.Image: Image with text drawn.
        """
        if not self.text_settings or not text:
            return img
        
        logger.info(f"Drawing text: '{text}'")
        
        # Store the current locale for font selection
        self.current_locale = locale
        
        # Select the appropriate font file based on locale
        if locale and locale in self.text_settings.font_files:
            font_file = self.text_settings.font_files[locale]
            logger.info(f"Using locale-specific font for {locale}: {font_file}")
        else:
            font_file = self.text_settings.font_files["default"]
            if locale:
                logger.info(f"No specific font for locale {locale}, using default font: {font_file}")
            else:
                logger.info(f"Using default font: {font_file}")
        
        logger.info(f"Text settings: Font={font_file}, Size={self.text_settings.font_size}")
        
        # Log image dimensions
        img_width, img_height = img.size
        logger.info(f"Image dimensions: {img_width}x{img_height} pixels")
        
        # Create a drawing context
        draw = ImageDraw.Draw(img)
        
        # Create font object
        font = self._load_font(font_file)
        
        # Get text dimensions measurement functions
        get_text_width, get_text_height = self._get_text_measurement_functions(draw, font)
        
        # Check if text needs to be wrapped
        text_width = get_text_width(text)
        logger.info(f"Text width: {text_width} pixels for text '{text}' with font size {self.text_settings.font_size}")
        
        # Wrap text if it exceeds the specified width
        if text_width > self.text_settings.width:
            logger.info(f"Text width ({text_width}) exceeds specified width ({self.text_settings.width}), wrapping text")
            lines = self._wrap_text(text, font, get_text_width, self.text_settings.width)
            logger.info(f"Text wrapped into {len(lines)} lines")
        else:
            lines = [text]
            logger.info("Text fits within specified width, no wrapping needed")
        
        # Calculate line heights
        line_heights = [get_text_height(line) for line in lines]
        total_text_height = sum(line_heights)
        
        # Add some spacing between lines (20% of font size)
        line_spacing = int(self.text_settings.font_size * 0.2)
        if len(lines) > 1:
            total_text_height += line_spacing * (len(lines) - 1)
            logger.info(f"Using line spacing of {line_spacing} pixels")
        
        # Calculate starting Y position based on vertical alignment
        text_y = self.text_settings.y
        
        if self.text_settings.vertical_align == "middle":
            text_y += (self.text_settings.height - total_text_height) // 2
        elif self.text_settings.vertical_align == "bottom":
            text_y += self.text_settings.height - total_text_height
        
        logger.info(f"Text area dimensions: Width={self.text_settings.width}, Height={self.text_settings.height}")
        logger.info(f"Total text height with {len(lines)} lines: {total_text_height} pixels")
        logger.info(f"Starting text Y position: {text_y}")
        
        # Draw each line
        current_y = text_y
        for i, line in enumerate(lines):
            line_width = get_text_width(line)
            
            # Calculate X position based on alignment
            line_x = self.text_settings.x
            
            if self.text_settings.align == "center":
                line_x += (self.text_settings.width - line_width) // 2
            elif self.text_settings.align == "right":
                line_x += self.text_settings.width - line_width
            
            logger.info(f"Drawing line {i+1} at position: ({line_x}, {current_y}) with width: {line_width}")
            
            # Draw the line
            draw.text(
                (line_x, current_y),
                line,
                font=font,
                fill=self.text_settings.color
            )
            
            # Move to next line position
            current_y += line_heights[i] + line_spacing
        
        # Clear the current locale
        self.current_locale = None
        
        return img
    
    def _load_font(self, font_file):
        """
        Load font from file.
        
        Args:
            font_file (str): Font file name.
            
        Returns:
            PIL.ImageFont.ImageFont: Font object.
        """
        try:
            # Construct the path to the font file
            font_path = os.path.join("fonts", font_file)
            logger.info(f"Attempting to load font from file: {font_path} with size {self.text_settings.font_size}")
            
            # Try to load the font file
            font = ImageFont.truetype(font_path, self.text_settings.font_size)
            logger.info(f"Successfully loaded font from file: {font_path} with size {self.text_settings.font_size}")
            
            # Log font details if possible
            try:
                font_details = font.getname()
                logger.info(f"Font details - Family: {font_details[0]}, Style: {font_details[1]}")
            except Exception as font_detail_error:
                logger.info(f"Could not get font details: {font_detail_error}")
                
            return font
                
        except Exception as e:
            logger.warning(f"Failed to load font file {font_file}: {e}")
            logger.warning(f"Font error details: {str(e)}")
            
            # Fallback to default font
            font = ImageFont.load_default()
            logger.info(f"Using default font with size {self.text_settings.font_size}")
            
            # Try to get default font info
            try:
                default_info = font.getname()
                logger.info(f"Default font details - Family: {default_info[0]}, Style: {default_info[1]}")
            except Exception as default_font_error:
                logger.info(f"Could not get default font details: {default_font_error}")
            
            return font
    
    def _get_text_measurement_functions(self, draw, font):
        """
        Get functions for measuring text dimensions based on Pillow version.
        
        Args:
            draw (PIL.ImageDraw.ImageDraw): Drawing context.
            font (PIL.ImageFont.ImageFont): Font object.
            
        Returns:
            tuple: (get_text_width_func, get_text_height_func)
        """
        try:
            # For newer Pillow versions
            def get_text_width(text):
                return draw.textlength(text, font=font)
            
            def get_text_height(text):
                bbox = font.getbbox(text)
                if bbox:
                    return bbox[3] - bbox[1]  # bottom - top
                else:
                    return self.text_settings.font_size  # Fallback
        except AttributeError:
            # Fallback for older Pillow versions
            def get_text_width(text):
                return font.getsize(text)[0]
            
            def get_text_height(text):
                return font.getsize(text)[1]
        
        return get_text_width, get_text_height
    
    def _wrap_text(self, text, font, get_text_width_func, max_width):
        """
        Wrap text to fit within a specified width.
        
        Args:
            text (str): Text to wrap.
            font (PIL.ImageFont.ImageFont): Font to use for text measurement.
            get_text_width_func (callable): Function to measure text width.
            max_width (int): Maximum width in pixels.
            
        Returns:
            list: List of text lines.
        """
        words = text.split()
        if not words:
            return []
        
        lines = []
        current_line = words[0]
        
        for word in words[1:]:
            # Check if adding this word would exceed the max width
            test_line = current_line + " " + word
            test_width = get_text_width_func(test_line)
            
            if test_width <= max_width:
                # Word fits, add it to the current line
                current_line = test_line
            else:
                # Word doesn't fit, start a new line
                lines.append(current_line)
                current_line = word
                
                # Handle case where a single word is wider than max_width
                # In this case, we might need to break the word
                if get_text_width_func(word) > max_width:
                    logger.warning(f"Word '{word}' is wider than maximum width ({max_width}px)")
                    # We'll keep it as is for now, but this could be enhanced to break long words
        
        # Add the last line
        if current_line:
            lines.append(current_line)
        
        return lines
