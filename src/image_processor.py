"""
Image processor module for the Screenshot Cropper application.
"""
import logging
import os
import os.path
from PIL import Image
from src.psd_processor import PSDProcessor

logger = logging.getLogger("screenshot_cropper")

class ImageProcessor:
    """Handler for image processing operations."""
    
    def __init__(self, input_dir, output_dir, crop_settings, background_settings=None, text_processor=None, locale_handler=None):
        """
        Initialize the ImageProcessor.
        
        Args:
            input_dir (str): Directory containing input images.
            output_dir (str): Directory to save processed images.
            crop_settings (CropSettings): Crop settings to apply.
            background_settings (BackgroundSettings, optional): Background settings to apply.
            text_processor (TextProcessor, optional): Processor for text operations.
            locale_handler (LocaleHandler, optional): Handler for locale texts.
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.crop_settings = crop_settings
        self.background_settings = background_settings
        self.text_processor = text_processor
        self.locale_handler = locale_handler
        self.supported_extensions = ('.png', '.jpg', '.jpeg', '.psd')
        
        # Get text settings from text processor if available
        text_settings = None
        if text_processor and hasattr(text_processor, 'text_settings'):
            text_settings = text_processor.text_settings
            
        # Initialize PSD processor with locale handler and text settings
        self.psd_processor = PSDProcessor(locale_handler, text_settings)
    
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
        
        # If we have locales and text processor, process each image for each locale
        if self.locale_handler and self.text_processor:
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
        
        # If locale is provided, create locale-specific subdirectory and add locale to filename
        if locale:
            # Create locale-specific subdirectory
            locale_output_dir = os.path.join(self.output_dir, locale)
            if not os.path.exists(locale_output_dir):
                os.makedirs(locale_output_dir)
                logger.info(f"Created locale-specific output directory: {locale_output_dir}")
            
            output_filename = f"{name}_{locale}{ext}"
            output_path = os.path.join(locale_output_dir, output_filename)
        else:
            output_filename = filename
            output_path = os.path.join(self.output_dir, output_filename)
        
        if locale:
            logger.info(f"Processing image: {filename} for locale: {locale}")
        else:
            logger.info(f"Processing image: {filename}")
        
        # Handle PSD files differently
        if filename.lower().endswith('.psd'):
            # For PSD files, always save as PNG
            output_path = output_path.rsplit('.', 1)[0] + '.png'
            return self._process_psd(image_path, output_path, locale)
        
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
                            
                            # If text processor and text are provided, draw text
                            if self.text_processor and text:
                                final_img = self.text_processor.draw_text(final_img, text, locale)
                            
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
    
    def _process_psd(self, psd_path, output_path, locale=None):
        """
        Process a PSD file using the PSD processor.
        
        Args:
            psd_path (str): Path to the PSD file.
            output_path (str): Path to save the output PNG file.
            locale (str, optional): Locale code for text translation.
            
        Returns:
            bool: True if processing was successful.
            
        Raises:
            Exception: If PSD processing fails.
        """
        logger.info(f"Processing PSD file: {os.path.basename(psd_path)}")
        
        success = self.psd_processor.process_psd(psd_path, output_path, locale)
        
        if not success:
            raise Exception(f"Failed to process PSD file: {psd_path}")
        
        return True
