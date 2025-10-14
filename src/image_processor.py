"""
Image processor module for the Screenshot Cropper application.
"""
import logging
import os
import os.path
from PIL import Image
from src.psd_processor import PSDProcessor
from src.image_compositor import ImageCompositor
from src.filename_utils import extract_screenshot_number

logger = logging.getLogger("screenshot_cropper")

class ImageProcessor:
    """Handler for image processing operations."""
    
    def __init__(self, input_dir, output_dir, crop_settings, background_settings=None, text_processor=None, locale_handler=None, screenshot_filter=None, skip_existing=False):
        """
        Initialize the ImageProcessor.

        Args:
            input_dir (str): Directory containing input images.
            output_dir (str): Directory to save processed images.
            crop_settings (CropSettings): Crop settings to apply.
            background_settings (BackgroundSettings, optional): Background settings to apply.
            text_processor (TextProcessor, optional): Processor for text operations.
            locale_handler (LocaleHandler, optional): Handler for locale texts.
            screenshot_filter (int, optional): Only process screenshot with this number.
            skip_existing (bool, optional): Skip processing if output file already exists.
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.crop_settings = crop_settings
        self.background_settings = background_settings
        self.text_processor = text_processor
        self.locale_handler = locale_handler
        self.screenshot_filter = screenshot_filter
        self.skip_existing = skip_existing
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

        # Separate PSD files from regular images
        psd_files = [f for f in image_files if f.lower().endswith('.psd')]
        regular_files = [f for f in image_files if not f.lower().endswith('.psd')]

        if psd_files:
            logger.info(f"Found {len(psd_files)} PSD files and {len(regular_files)} regular image files")

        # If we have locales and text processor, process each image for each locale
        if self.locale_handler and self.text_processor:
            locales = self.locale_handler.get_locales()
            if locales:
                logger.info(f"Processing images for {len(locales)} locales: {', '.join(locales)}")

                # Process PSD files efficiently (all locales at once per PSD)
                for i, psd_file in enumerate(psd_files):
                    filename = os.path.basename(psd_file)
                    screenshot_num = extract_screenshot_number(filename)
                    text_index = screenshot_num if screenshot_num is not None else i
                    add_one = screenshot_num is None

                    logger.info(f"Processing PSD file {filename} (index: {text_index}, add_one: {add_one}) for all locales")
                    try:
                        count = self._process_psd_for_all_locales(psd_file, locales, text_index, add_one)
                        processed_count += count
                    except Exception as e:
                        logger.error(f"Failed to process PSD file {psd_file} for all locales: {e}")

                # Process regular image files (one locale at a time)
                for i, image_file in enumerate(regular_files):
                    filename = os.path.basename(image_file)
                    screenshot_num = extract_screenshot_number(filename)
                    text_index = screenshot_num if screenshot_num is not None else i + len(psd_files)
                    add_one = screenshot_num is None

                    for locale in locales:
                        # Check if we should skip this locale for this image
                        if self.skip_existing:
                            name, ext = os.path.splitext(filename)
                            locale_output_dir = os.path.join(self.output_dir, locale)
                            output_filename = f"{name}_{locale}{ext}"
                            output_path = os.path.join(locale_output_dir, output_filename)

                            if os.path.exists(output_path):
                                logger.info(f"Skipping {filename} for locale {locale} - output file already exists")
                                processed_count += 1  # Count as processed (skipped)
                                continue

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
                # If screenshot filter is set, only include files with matching number
                if self.screenshot_filter is not None:
                    screenshot_num = extract_screenshot_number(filename)
                    if screenshot_num == self.screenshot_filter:
                        image_files.append(file_path)
                    else:
                        logger.debug(f"Skipping file '{filename}' (filter: {self.screenshot_filter})")
                else:
                    image_files.append(file_path)

        return image_files

    def _process_psd_for_all_locales(self, psd_path, locales, text_index, add_one=False):
        """
        Process a PSD file for all locales efficiently by opening it once.

        Args:
            psd_path (str): Path to the PSD file.
            locales (list): List of locale codes to process.
            text_index (int): Index to use when getting text from locale handler.
            add_one (bool): Whether to add one to the index when getting text.

        Returns:
            int: Number of successfully processed locale outputs.

        Raises:
            Exception: If PSD processing fails completely.
        """
        logger.info(f"Processing PSD file for {len(locales)} locales: {os.path.basename(psd_path)}")

        filename = os.path.basename(psd_path)
        name, _ = os.path.splitext(filename)

        # Build dictionary of final output paths for all locales
        # Export directly to final filenames (no temp files needed)
        # If skip_existing is enabled, filter out locales where output already exists
        output_paths_by_locale = {}
        skipped_locales = []

        for locale in locales:
            locale_output_dir = os.path.join(self.output_dir, locale)
            if not os.path.exists(locale_output_dir):
                os.makedirs(locale_output_dir)
                logger.info(f"Created locale-specific output directory: {locale_output_dir}")

            output_filename = f"{name}_{locale}.png"
            output_path = os.path.join(locale_output_dir, output_filename)

            # Check if we should skip this locale
            if self.skip_existing and os.path.exists(output_path):
                logger.info(f"Skipping locale {locale} - output file already exists: {output_path}")
                skipped_locales.append(locale)
            else:
                output_paths_by_locale[locale] = output_path

        # If all locales were skipped, return early
        if not output_paths_by_locale:
            logger.info(f"All locales skipped for PSD file: {os.path.basename(psd_path)}")
            return len(skipped_locales)

        # Process PSD for all locales efficiently (opens file once, exports to final names)
        try:
            results = self.psd_processor.process_psd_for_multiple_locales(psd_path, output_paths_by_locale)
        except Exception as e:
            logger.error(f"Failed to process PSD file {psd_path}: {e}")
            raise

        # Now apply compositor processing to each exported PNG (in-place)
        success_count = 0
        for locale in output_paths_by_locale.keys():
            if not results.get(locale, False):
                logger.error(f"PSD processing failed for locale {locale}")
                continue

            output_path = output_paths_by_locale[locale]

            # Verify the file was created
            if not os.path.exists(output_path):
                logger.error(f"PSD output not found for locale {locale}: {output_path}")
                continue

            # Get text for this locale
            text = self.locale_handler.get_text(locale, text_index, add_one=add_one)

            # Apply compositor processing (crop, background, text overlay)
            # Process in-place: read from output_path, write back to output_path
            try:
                logger.info(f"Applying compositor to PSD output for locale {locale}: {output_path}")

                # Create a temporary file for compositor processing
                temp_compositor_path = output_path.replace('.png', '_comp_temp.png')

                compositor_success = self.image_compositor.process_image(output_path, temp_compositor_path, text, locale)

                if compositor_success:
                    # Replace original with composited version
                    os.replace(temp_compositor_path, output_path)
                    logger.info(f"Successfully processed PSD with compositor for locale {locale}")
                    success_count += 1
                else:
                    logger.warning(f"Compositor failed for locale {locale}, keeping PSD output as-is")
                    # Remove temp file if it exists
                    if os.path.exists(temp_compositor_path):
                        os.remove(temp_compositor_path)
                    success_count += 1

            except Exception as compositor_error:
                logger.error(f"Error applying compositor for locale {locale}: {compositor_error}")
                # Keep the original PSD output
                logger.info(f"Keeping unprocessed PSD output for locale {locale}")
                # Clean up temp file if it exists
                if os.path.exists(temp_compositor_path):
                    try:
                        os.remove(temp_compositor_path)
                    except:
                        pass
                success_count += 1

        # Add skipped locales to the total count
        total_count = success_count + len(skipped_locales)
        if skipped_locales:
            logger.info(f"Successfully processed PSD for {success_count} locales, skipped {len(skipped_locales)} (total: {total_count}/{len(locales)})")
        else:
            logger.info(f"Successfully processed PSD for {success_count}/{len(locales)} locales")
        return total_count

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
