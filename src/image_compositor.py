"""
Image compositor module for the Screenshot Cropper application.
"""
import logging
import os
from PIL import Image

logger = logging.getLogger("screenshot_cropper")

class ImageCompositor:
    """
    Handles the composition of images with background and text overlay.
    This class ensures consistent processing for both regular images and PSD exports.
    """
    
    def __init__(self, crop_settings, background_settings=None, text_processor=None, base_dir=None, overlay_settings=None):
        """
        Initialize the ImageCompositor.

        Args:
            crop_settings (CropSettings): Settings for cropping the image
            background_settings (BackgroundSettings, optional): Settings for background placement
            text_processor (TextProcessor, optional): Processor for text overlay
            base_dir (str, optional): Base directory for finding the background image
            overlay_settings (OverlaySettings, optional): Settings for overlay image
        """
        self.crop_settings = crop_settings
        self.background_settings = background_settings
        self.text_processor = text_processor
        self.base_dir = base_dir
        self.overlay_settings = overlay_settings
    
    def process_image(self, image_path, output_path, text=None, locale=None):
        """
        Process an image through the complete workflow:
        1. Open the image
        2. Crop according to settings
        3. Place on background
        4. Add text overlay if applicable
        5. Save the result
        
        Args:
            image_path (str): Path to the input image
            output_path (str): Path to save the output image
            text (str, optional): Text to overlay on the image
            locale (str, optional): Locale code for text overlay
            
        Returns:
            bool: True if processing was successful
        """
        try:
            logger.info(f"Processing image: {os.path.basename(image_path)}")
            logger.info(f"Output path: {output_path}")
            
            # Log text and locale parameters
            if text:
                logger.info(f"Text to overlay: '{text}'")
            else:
                logger.info("No text to overlay")
                
            if locale:
                logger.info(f"Locale: {locale}")
            else:
                logger.info("No locale specified")
            
            # Log background settings
            if self.background_settings:
                logger.info(f"Background settings: file={self.background_settings.file}, "
                           f"position=({self.background_settings.position_x}, {self.background_settings.position_y}), "
                           f"size=({self.background_settings.width}, {self.background_settings.height})")
            else:
                logger.info("No background settings")
                
            # Log text processor
            if self.text_processor:
                logger.info("Text processor is available")
            else:
                logger.info("No text processor")
            
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
                    logger.warning(f"Invalid crop box for {os.path.basename(image_path)}: {left}, {top}, {right}, {bottom}")
                    logger.warning("Skipping crop for this image")
                    cropped_img = img.copy()
                else:
                    # Crop image
                    logger.info(f"Cropping image: {left}, {top}, {right}, {bottom}")
                    cropped_img = img.crop((left, top, right, bottom))
                
                # If background settings are provided, apply background
                if self.background_settings:
                    try:
                        # Get the path to the background image
                        if os.path.isabs(self.background_settings.file):
                            # Use absolute path directly
                            bg_path = self.background_settings.file
                        elif self.base_dir:
                            # Use the provided base directory
                            bg_path = os.path.join(self.base_dir, "input", self.background_settings.file)
                        else:
                            # Try to determine the base directory from the image path
                            # This works for regular images but might not work for temporary files
                            input_dir = os.path.dirname(os.path.dirname(image_path))
                            bg_path = os.path.join(input_dir, "input", self.background_settings.file)
                        
                        logger.info(f"Loading background image from: {bg_path}")
                        
                        # Check if background image exists
                        if not os.path.isfile(bg_path):
                            logger.error(f"Background image not found: {bg_path}")
                            # Save just the cropped image
                            cropped_img.save(output_path)
                            logger.info(f"Saved cropped image to: {output_path}")
                            return True
                        
                        # Open background image
                        with Image.open(bg_path) as bg_img:
                            # Resize cropped image to specified width while maintaining aspect ratio
                            original_width, original_height = cropped_img.size
                            aspect_ratio = original_height / original_width
                            new_width = self.background_settings.width
                            new_height = int(new_width * aspect_ratio)
                            
                            logger.info(f"Resizing image from {original_width}x{original_height} to {new_width}x{new_height} (maintaining aspect ratio)")
                            resized_img = cropped_img.resize((new_width, new_height))
                            
                            # Create a copy of the background
                            final_img = bg_img.copy()
                            
                            # Paste cropped image onto background
                            final_img.paste(resized_img, (self.background_settings.position_x, self.background_settings.position_y))
                            
                            # If text processor and text are provided, draw text
                            if self.text_processor and text:
                                logger.info(f"Drawing text '{text}' with locale '{locale}'")
                                final_img = self.text_processor.draw_text(final_img, text, locale)
                                logger.info("Text drawing completed")
                            elif self.text_processor:
                                logger.info("Text processor available but no text to draw")
                            elif text:
                                logger.warning("Text provided but no text processor available")

                            # Apply overlay if configured
                            if self.overlay_settings:
                                # Find overlay path (same logic as background)
                                if os.path.isabs(self.overlay_settings.file):
                                    overlay_path = self.overlay_settings.file
                                elif self.base_dir:
                                    overlay_path = os.path.join(self.base_dir, "input", self.overlay_settings.file)
                                else:
                                    input_dir = os.path.dirname(os.path.dirname(image_path))
                                    overlay_path = os.path.join(input_dir, "input", self.overlay_settings.file)

                                if os.path.isfile(overlay_path):
                                    logger.info(f"Applying overlay from: {overlay_path}")
                                    overlay_img = Image.open(overlay_path).convert("RGBA")
                                    # Convert final_img to RGBA if needed
                                    if final_img.mode != "RGBA":
                                        final_img = final_img.convert("RGBA")
                                    # Paste with alpha transparency
                                    final_img.paste(
                                        overlay_img,
                                        (self.overlay_settings.position_x, self.overlay_settings.position_y),
                                        overlay_img  # Third arg = alpha mask
                                    )
                                    logger.info("Overlay applied successfully")
                                else:
                                    logger.warning(f"Overlay image not found: {overlay_path}")

                            # Save final image
                            final_img.save(output_path)
                            logger.info(f"Saved composite image to: {output_path}")
                    except Exception as e:
                        logger.error(f"Error applying background to {os.path.basename(image_path)}: {e}")
                        # Save just the cropped image as fallback
                        cropped_img.save(output_path)
                        logger.info(f"Saved cropped image to: {output_path}")
                else:
                    # Save just the cropped image
                    cropped_img.save(output_path)
                    logger.info(f"Saved cropped image to: {output_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing image {os.path.basename(image_path)}: {e}")
            return False
