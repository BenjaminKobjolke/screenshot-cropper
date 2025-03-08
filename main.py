#!/usr/bin/env python3
"""
Screenshot Cropper - A tool to crop screenshots based on JSON configuration.
"""
import argparse
import logging
import os
import sys
from src.config import ConfigHandler
from src.image_processor import ImageProcessor
from src.locale_handler import LocaleHandler
from src.logger import setup_logger

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Crop screenshots based on JSON configuration.")
    parser.add_argument("--directory", required=True, help="Directory containing input folder and configuration file")
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    # Setup logging
    logger = setup_logger()
    
    # Parse command line arguments
    args = parse_arguments()
    directory = args.directory
    
    logger.info(f"Starting screenshot cropper with directory: {directory}")
    
    # Check if directory exists
    if not os.path.isdir(directory):
        logger.error(f"Directory '{directory}' does not exist")
        sys.exit(1)
    
    # Check if input directory exists
    input_dir = os.path.join(directory, "input", "screenshots")
    if not os.path.isdir(input_dir):
        logger.error(f"Input directory '{input_dir}' does not exist")
        sys.exit(1)
    
    # Check if configuration file exists
    config_file = os.path.join(directory, "screenshot-cropper.json")
    if not os.path.isfile(config_file):
        logger.error(f"Configuration file '{config_file}' does not exist")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(directory, "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")
    
    # Load configuration
    try:
        config_handler = ConfigHandler(config_file)
        crop_settings = config_handler.get_crop_settings()
        logger.info(f"Loaded crop settings: {crop_settings}")
        
        # Load background settings if available
        background_settings = config_handler.get_background_settings()
        if background_settings:
            logger.info(f"Loaded background settings: {background_settings}")
        else:
            logger.info("No background settings found, images will only be cropped")
            
        # Load text settings if available
        text_settings = config_handler.get_text_settings()
        if text_settings:
            logger.info(f"Loaded text settings: {text_settings}")
        else:
            logger.info("No text settings found, no text will be added")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Initialize locale handler if text settings are available
    locale_handler = None
    if text_settings:
        locales_dir = os.path.join(directory, "input", "locales")
        if os.path.isdir(locales_dir):
            locale_handler = LocaleHandler(locales_dir)
            logger.info(f"Initialized locale handler with locales: {', '.join(locale_handler.get_locales())}")
        else:
            logger.warning(f"Locales directory not found: {locales_dir}")
    
    # Process images
    try:
        image_processor = ImageProcessor(
            input_dir, 
            output_dir, 
            crop_settings, 
            background_settings, 
            text_settings, 
            locale_handler
        )
        processed_count = image_processor.process_images()
        logger.info(f"Successfully processed {processed_count} images")
    except Exception as e:
        logger.error(f"Failed to process images: {e}")
        sys.exit(1)
    
    logger.info("Screenshot cropping completed successfully")

if __name__ == "__main__":
    main()
