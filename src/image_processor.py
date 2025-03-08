"""
Image processor module for the Screenshot Cropper application.
"""
import logging
import os
from PIL import Image

logger = logging.getLogger("screenshot_cropper")

class ImageProcessor:
    """Handler for image processing operations."""
    
    def __init__(self, input_dir, output_dir, crop_settings, background_settings=None):
        """
        Initialize the ImageProcessor.
        
        Args:
            input_dir (str): Directory containing input images.
            output_dir (str): Directory to save processed images.
            crop_settings (CropSettings): Crop settings to apply.
            background_settings (BackgroundSettings, optional): Background settings to apply.
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.crop_settings = crop_settings
        self.background_settings = background_settings
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
        
        # Process each image
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
    
    def _process_image(self, image_path):
        """
        Process a single image.
        
        Args:
            image_path (str): Path to the image file.
        
        Raises:
            Exception: If image processing fails.
        """
        # Get output file path
        filename = os.path.basename(image_path)
        output_path = os.path.join(self.output_dir, filename)
        
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
