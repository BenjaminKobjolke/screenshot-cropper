"""
Image compositor module for the Screenshot Cropper application.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from PIL import Image, ImageChops, ImageOps

logger = logging.getLogger("screenshot_cropper")


@dataclass
class ComposeResult:
    """Result of an in-memory composition."""
    final: Image.Image
    cropped: Image.Image


class ImageCompositor:
    """
    Handles the composition of images with background and text overlay.
    This class ensures consistent processing for both regular images and PSD exports.
    """

    def __init__(self, crop_settings, background_settings=None, text_processor=None,
                 base_dir=None, overlay_settings=None, export_settings=None, output_dir=None,
                 final_crop_settings=None, mask_settings=None):
        """
        Initialize the ImageCompositor.

        Args:
            crop_settings (CropSettings): Settings for cropping the screenshot
            background_settings (BackgroundSettings, optional): Settings for background placement
            text_processor (TextProcessor, optional): Processor for text overlay
            base_dir (str, optional): Base directory for finding the background image
            overlay_settings (OverlaySettings, optional): Settings for overlay image
            export_settings (ExportSettings, optional): Settings for export format and quality
            output_dir (str, optional): Base output directory for saving cropped images
            final_crop_settings (CropSettings, optional): Crop applied to the final composite
            mask_settings (ScreenshotMaskSettings, optional): Mask whose opaque pixels
                are subtracted from the cropped screenshot
        """
        self.crop_settings = crop_settings
        self.background_settings = background_settings
        self.text_processor = text_processor
        self.base_dir = base_dir
        self.overlay_settings = overlay_settings
        self.export_settings = export_settings
        self.output_dir = output_dir
        self.final_crop_settings = final_crop_settings
        self.mask_settings = mask_settings

    def _save_image(self, img, output_path):
        """
        Save image with configured format and quality.

        Args:
            img (PIL.Image): The image to save
            output_path (str): Path to save the image

        Returns:
            str: The actual output path used (may have different extension)
        """
        if self.export_settings:
            # Change extension based on format
            base, _ = os.path.splitext(output_path)
            output_path = f"{base}.{self.export_settings.format}"

            if self.export_settings.format == "webp":
                if self.export_settings.lossless:
                    # Lossless WebP preserves transparency
                    img.save(output_path, "WEBP", lossless=True)
                else:
                    img.save(output_path, "WEBP", quality=self.export_settings.quality)
            else:
                img.save(output_path, "PNG")
        else:
            img.save(output_path)

        return output_path

    def _save_cropped_image(self, cropped_img, output_path, locale=None):
        """
        Save the cropped image to the cropped subfolder.

        Args:
            cropped_img (PIL.Image): The cropped image to save
            output_path (str): The final output path (used to derive cropped path)
            locale (str, optional): Locale code for subfolder organization
        """
        if not self.output_dir or not self.export_settings or not self.export_settings.keep_cropped:
            return

        # Build cropped output path: output_dir/cropped/{locale}/filename
        filename = os.path.basename(output_path)
        if locale:
            cropped_dir = os.path.join(self.output_dir, "cropped", locale)
        else:
            cropped_dir = os.path.join(self.output_dir, "cropped")

        # Create directory if it doesn't exist
        if not os.path.exists(cropped_dir):
            os.makedirs(cropped_dir)
            logger.info(f"Created cropped output directory: {cropped_dir}")

        cropped_path = os.path.join(cropped_dir, filename)
        actual_path = self._save_image(cropped_img, cropped_path)
        logger.info(f"Saved cropped image to: {actual_path}")

    def _resolve_asset_path(self, file, image_path=None):
        """
        Resolve a background/overlay file reference to an absolute path.

        Args:
            file (str): Configured file name or absolute path
            image_path (str, optional): Source image path used to derive the base
                directory when none was injected (temp files may not resolve)

        Returns:
            str: Resolved path (not guaranteed to exist)
        """
        if os.path.isabs(file):
            return file
        if self.base_dir:
            return os.path.join(self.base_dir, "input", file)
        input_dir = os.path.dirname(os.path.dirname(image_path or ""))
        return os.path.join(input_dir, "input", file)

    def _crop(self, img, name, settings):
        """Crop the image per the given crop settings, falling back to a copy on invalid box."""
        width, height = img.size
        left = settings.left
        top = settings.top
        right = width - settings.right if settings.right > 0 else width
        bottom = height - settings.bottom if settings.bottom > 0 else height

        if left >= right or top >= bottom:
            logger.warning(f"Invalid crop box for {name}: {left}, {top}, {right}, {bottom}")
            logger.warning("Skipping crop for this image")
            return img.copy()

        logger.info(f"Cropping image: {left}, {top}, {right}, {bottom}")
        return img.crop((left, top, right, bottom))

    def _subtract_mask(self, img, image_path=None):
        """Subtract the mask's opaque pixels from the given image's alpha.

        The mask is resized to the image (canvas) size when dimensions differ.
        """
        mask_path = self._resolve_asset_path(self.mask_settings.file, image_path)
        if not os.path.isfile(mask_path):
            logger.warning(f"Screenshot mask not found: {mask_path}")
            return img

        logger.info(f"Applying screenshot mask from: {mask_path}")
        mask_img = Image.open(mask_path).convert("RGBA")
        if mask_img.size != img.size:
            logger.info(f"Resizing mask from {mask_img.size} to {img.size}")
            mask_img = mask_img.resize(img.size, Image.Resampling.LANCZOS)

        result = img.convert("RGBA")
        # new_alpha = image_alpha * (1 - mask_alpha), keeps anti-aliased edges
        new_alpha = ImageChops.multiply(
            result.getchannel("A"), ImageOps.invert(mask_img.getchannel("A"))
        )
        result.putalpha(new_alpha)
        return result

    def _apply_overlay(self, final_img, image_path=None):
        """Paste the configured overlay (RGBA, native size) onto the composite."""
        overlay_path = self._resolve_asset_path(self.overlay_settings.file, image_path)
        if not os.path.isfile(overlay_path):
            logger.warning(f"Overlay image not found: {overlay_path}")
            return final_img

        logger.info(f"Applying overlay from: {overlay_path}")
        overlay_img = Image.open(overlay_path).convert("RGBA")
        if final_img.mode != "RGBA":
            final_img = final_img.convert("RGBA")
        # Third arg = alpha mask so transparency is respected
        final_img.paste(
            overlay_img,
            (self.overlay_settings.position_x, self.overlay_settings.position_y),
            overlay_img,
        )
        return final_img

    def compose(self, img, text=None, locale=None, image_path=None):
        """
        Run the full composition in memory: crop, background, text, overlay, final crop.

        Args:
            img (PIL.Image): Source image
            text (str, optional): Text to overlay
            locale (str, optional): Locale code for text overlay
            image_path (str, optional): Source path, used for asset resolution and logging

        Returns:
            ComposeResult: final composite and the intermediate cropped image
        """
        name = os.path.basename(image_path) if image_path else "<in-memory>"
        cropped_img = self._crop(img, name, self.crop_settings)

        if self.background_settings:
            # Mask is applied in canvas space inside _compose_on_background
            final_img = self._compose_on_background(cropped_img, text, locale, image_path, name)
        elif self.mask_settings:
            # No background: the cropped screenshot IS the canvas
            final_img = self._subtract_mask(cropped_img, image_path)
        else:
            final_img = cropped_img

        fc = self.final_crop_settings
        if fc and any((fc.top, fc.left, fc.right, fc.bottom)):
            logger.info("Applying final crop to composite")
            final_img = self._crop(final_img, name, fc)

        return ComposeResult(final=final_img, cropped=cropped_img)

    def _compose_on_background(self, cropped_img, text, locale, image_path, name):
        """Paste the cropped screenshot on the background, draw text and overlay.

        Falls back to the cropped image on any error (behavior preserved from
        the original pipeline).
        """
        try:
            bg_path = self._resolve_asset_path(self.background_settings.file, image_path)
            logger.info(f"Loading background image from: {bg_path}")

            if not os.path.isfile(bg_path):
                logger.error(f"Background image not found: {bg_path}")
                return cropped_img

            with Image.open(bg_path) as bg_img:
                # Resize cropped image to configured width, height follows aspect ratio
                original_width, original_height = cropped_img.size
                aspect_ratio = original_height / original_width
                new_width = self.background_settings.width
                new_height = int(new_width * aspect_ratio)

                logger.info(f"Resizing image from {original_width}x{original_height} "
                            f"to {new_width}x{new_height} (maintaining aspect ratio)")
                resized_img = cropped_img.resize((new_width, new_height))

                position = (self.background_settings.position_x,
                            self.background_settings.position_y)
                if self.mask_settings:
                    # Canvas-space mask: place screenshot on a transparent
                    # canvas-sized layer, subtract the mask there, then
                    # composite the layer over the background
                    layer = Image.new("RGBA", bg_img.size, (0, 0, 0, 0))
                    layer.paste(resized_img, position)
                    layer = self._subtract_mask(layer, image_path)
                    final_img = bg_img.copy().convert("RGBA")
                    final_img.alpha_composite(layer)
                else:
                    final_img = bg_img.copy()
                    final_img.paste(resized_img, position)

            if self.text_processor and text:
                logger.info(f"Drawing text '{text}' with locale '{locale}'")
                final_img = self.text_processor.draw_text(final_img, text, locale)
            elif text:
                logger.warning("Text provided but no text processor available")

            if self.overlay_settings:
                final_img = self._apply_overlay(final_img, image_path)

            return final_img
        except Exception as e:
            logger.error(f"Error applying background to {name}: {e}")
            return cropped_img

    def process_image(self, image_path, output_path, text=None, locale=None):
        """
        Process an image file end to end: compose in memory, then save.

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

            with Image.open(image_path) as img:
                result = self.compose(img, text=text, locale=locale, image_path=image_path)

            # Save cropped image separately if keep_cropped is enabled
            self._save_cropped_image(result.cropped, output_path, locale)

            actual_path = self._save_image(result.final, output_path)
            logger.info(f"Saved composite image to: {actual_path}")
            return True

        except Exception as e:
            logger.error(f"Error processing image {os.path.basename(image_path)}: {e}")
            return False
