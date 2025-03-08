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
    input_dir = os.path.join(directory, "input")
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
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Process images
    try:
        image_processor = ImageProcessor(input_dir, output_dir, crop_settings)
        processed_count = image_processor.process_images()
        logger.info(f"Successfully processed {processed_count} images")
    except Exception as e:
        logger.error(f"Failed to process images: {e}")
        sys.exit(1)
    
    logger.info("Screenshot cropping completed successfully")

if __name__ == "__main__":
    main()
