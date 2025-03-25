"""
Image processor module for the Screenshot Cropper application.
"""
import logging
import os
import os.path
from PIL import Image
from src.psd_processor import PSDProcessor
from src.image_compositor import ImageCompositor

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
        
        # Initialize image compositor for consistent image processing
        # Pass the directory containing the input and output directories as the base directory
        base_dir = os.path.dirname(os.path.dirname(input_dir))
        self.image_compositor = ImageCompositor(crop_settings, background_settings, text_processor, base_dir)
        logger.info(f"Initialized image compositor with base directory: {base_dir}")
    
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
                    # Extract filename without extension and check if it's a valid integer
                    filename = os.path.basename(image_file)
                    name, _ = os.path.splitext(filename)
                    
                    # Use filename as index if it's a valid integer, otherwise use iteration index
                    text_index = int(name) if name.isdigit() else i
                    
                    # Determine whether to add one to the index when getting text
                    # If using filename as index, don't add one
                    add_one = not name.isdigit()
                    
                    for locale in locales:
                        logger.info(f"Processing image {filename} (index: {text_index}, add_one: {add_one}) for locale {locale}")
                        text = self.locale_handler.get_text(locale, text_index, add_one=add_one)
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
            return self._process_psd(image_path, output_path, locale, text)
        
        # Use the image compositor to process the image
        success = self.image_compositor.process_image(image_path, output_path, text, locale)
        
        if not success:
            raise Exception(f"Failed to process image: {image_path}")
        
        return True
    
    def _process_psd(self, psd_path, output_path, locale=None, text=None):
        """
        Process a PSD file using the PSD processor.
        
        Args:
            psd_path (str): Path to the PSD file.
            output_path (str): Path to save the output PNG file.
            locale (str, optional): Locale code for text translation.
            text (str, optional): Text to overlay on the image.
            
        Returns:
            bool: True if processing was successful.
            
        Raises:
            Exception: If PSD processing fails.
        """
        logger.info(f"Processing PSD file: {os.path.basename(psd_path)}")
        
        # Create a temporary path for the initial PNG output
        temp_output_dir = os.path.dirname(output_path)
        temp_filename = f"temp_{os.path.basename(output_path)}"
        temp_output_path = os.path.join(temp_output_dir, temp_filename)
        
        # Process the PSD file and save to temporary location
        success = self.psd_processor.process_psd(psd_path, temp_output_path, locale)
        
        if not success:
            raise Exception(f"Failed to process PSD file: {psd_path}")
        
        # Use the image compositor to process the temporary PNG file
        if os.path.exists(temp_output_path):
            try:
                # Process the temporary PNG using the image compositor
                logger.info(f"Applying compositor to processed PSD output: {temp_output_path}")
                success = self.image_compositor.process_image(temp_output_path, output_path, text, locale)
                
                if not success:
                    raise Exception(f"Failed to apply compositor to processed PSD: {temp_output_path}")
                
                # Remove the temporary file
                if os.path.exists(temp_output_path):
                    os.remove(temp_output_path)
                    logger.info(f"Removed temporary file: {temp_output_path}")
                
                return True
                
            except Exception as e:
                logger.error(f"Error processing PSD output: {e}")
                # If there was an error, use the temporary file as the output
                if os.path.exists(temp_output_path):
                    os.replace(temp_output_path, output_path)
                    logger.info(f"Saved unprocessed PSD output to: {output_path}")
        else:
            logger.error(f"Temporary PSD output file not found: {temp_output_path}")
            return False
        
        return True
