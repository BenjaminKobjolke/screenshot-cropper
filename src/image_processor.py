"""
Image processor module for the Screenshot Cropper application.
"""
import logging
import os
import os.path
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("screenshot_cropper")

class ImageProcessor:
    """Handler for image processing operations."""
    
    def __init__(self, input_dir, output_dir, crop_settings, background_settings=None, text_settings=None, locale_handler=None):
        """
        Initialize the ImageProcessor.
        
        Args:
            input_dir (str): Directory containing input images.
            output_dir (str): Directory to save processed images.
            crop_settings (CropSettings): Crop settings to apply.
            background_settings (BackgroundSettings, optional): Background settings to apply.
            text_settings (TextSettings, optional): Text settings to apply.
            locale_handler (LocaleHandler, optional): Handler for locale texts.
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.crop_settings = crop_settings
        self.background_settings = background_settings
        self.text_settings = text_settings
        self.locale_handler = locale_handler
        self.supported_extensions = ('.png', '.jpg', '.jpeg')
    
    def process_images(self):
        """
        Process all images in the input directory.
        
        Returns:
            int: Number of successfully processed images.
        """
        processed_count = 0
        
        # Get list of image files
        image_files = self._get_image_files()
        logger.info(f"Found {len(image_files)} image files to process")
        
        # If we have locales and text settings, process each image for each locale
        if self.locale_handler and self.text_settings:
            locales = self.locale_handler.get_locales()
            if locales:
                logger.info(f"Processing images for {len(locales)} locales: {', '.join(locales)}")
                for i, image_file in enumerate(image_files):
                    for locale in locales:
                        text = self.locale_handler.get_text(locale, i)
                        try:
                            self._process_image(image_file, locale=locale, text=text)
                            processed_count += 1
                        except Exception as e:
                            logger.error(f"Failed to process image {image_file} for locale {locale}: {e}")
            else:
                logger.warning("No locales found, processing images without text")
                # No locales, process normally
                for image_file in image_files:
                    try:
                        self._process_image(image_file)
                        processed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to process image {image_file}: {e}")
        else:
            # No text settings or locale handler, process normally
            for image_file in image_files:
                try:
                    self._process_image(image_file)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Failed to process image {image_file}: {e}")
        
        return processed_count
    
    def _get_image_files(self):
        """
        Get list of image files in the input directory.
        
        Returns:
            list: List of image file paths.
        """
        image_files = []
        
        for filename in os.listdir(self.input_dir):
            file_path = os.path.join(self.input_dir, filename)
            
            # Check if it's a file and has a supported extension
            if os.path.isfile(file_path) and filename.lower().endswith(self.supported_extensions):
                image_files.append(file_path)
        
        return image_files
    
    def _process_image(self, image_path, locale=None, text=None):
        """
        Process a single image.
        
        Args:
            image_path (str): Path to the image file.
            locale (str, optional): Locale code for text overlay.
            text (str, optional): Text to overlay on the image.
        
        Raises:
            Exception: If image processing fails.
        """
        # Get output file path
        filename = os.path.basename(image_path)
        name, ext = os.path.splitext(filename)
        
        # If locale is provided, add it to the output filename
        if locale:
            output_filename = f"{name}_{locale}{ext}"
        else:
            output_filename = filename
            
        output_path = os.path.join(self.output_dir, output_filename)
        
        if locale:
            logger.info(f"Processing image: {filename} for locale: {locale}")
        else:
            logger.info(f"Processing image: {filename}")
        
        try:
            # Open image
            with Image.open(image_path) as img:
                # Get image dimensions
                width, height = img.size
                
                # Calculate crop box
                left = self.crop_settings.left
                top = self.crop_settings.top
                right = width - self.crop_settings.right if self.crop_settings.right > 0 else width
                bottom = height - self.crop_settings.bottom if self.crop_settings.bottom > 0 else height
                
                # Ensure valid crop box
                if left >= right or top >= bottom:
                    logger.warning(f"Invalid crop box for {filename}: {left}, {top}, {right}, {bottom}")
                    logger.warning("Skipping crop for this image")
                    img.save(output_path)
                    return
                
                # Crop image
                cropped_img = img.crop((left, top, right, bottom))
                
                # If background settings are provided, apply background
                if self.background_settings:
                    try:
                        # Get the path to the background image (in the input directory)
                        bg_path = os.path.join(os.path.dirname(os.path.dirname(self.input_dir)), "input", self.background_settings.file)
                        
                        logger.info(f"Loading background image from: {bg_path}")
                        
                        # Check if background image exists
                        if not os.path.isfile(bg_path):
                            logger.error(f"Background image not found: {bg_path}")
                            # Save just the cropped image
                            cropped_img.save(output_path)
                            logger.info(f"Saved cropped image to: {output_path}")
                            return
                        
                        # Open background image
                        with Image.open(bg_path) as bg_img:
                            # Resize cropped image to specified dimensions
                            resized_img = cropped_img.resize((self.background_settings.width, self.background_settings.height))
                            
                            # Create a copy of the background
                            final_img = bg_img.copy()
                            
                            # Paste cropped image onto background
                            final_img.paste(resized_img, (self.background_settings.position_x, self.background_settings.position_y))
                            
                            # Store the current locale for font selection
                            self.current_locale = locale
                            
                            # If text settings and text are provided, draw text
                            if self.text_settings and text:
                                final_img = self._draw_text(final_img, text)
                                
                            # Clear the current locale
                            self.current_locale = None
                            
                            # Save final image
                            final_img.save(output_path)
                            logger.info(f"Saved composite image to: {output_path}")
                    except Exception as e:
                        logger.error(f"Error applying background to {filename}: {e}")
                        # Save just the cropped image as fallback
                        cropped_img.save(output_path)
                        logger.info(f"Saved cropped image to: {output_path}")
                else:
                    # Save just the cropped image
                    cropped_img.save(output_path)
                    logger.info(f"Saved cropped image to: {output_path}")
        except Exception as e:
            logger.error(f"Error processing image {filename}: {e}")
            raise
    
    def _draw_text(self, img, text):
        """
        Draw text on the image.
        
        Args:
            img (PIL.Image.Image): Image to draw text on.
            text (str): Text to draw.
            
        Returns:
            PIL.Image.Image: Image with text drawn.
        """
        if not self.text_settings or not text:
            return img
        
        logger.info(f"Drawing text: '{text}'")
        
        # Select the appropriate font file based on locale
        locale = getattr(self, 'current_locale', None)
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
        
        # Get text dimensions measurement function based on Pillow version
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
        
        return img
    
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
