"""
Centralized constants for the Screenshot Cropper application.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class FileExtensions:
    """File extension constants."""
    PSD: str = ".psd"
    INDD: str = ".indd"
    PNG: str = ".png"
    WEBP: str = ".webp"
    JSON: str = ".json"
    JPG: str = ".jpg"
    JPEG: str = ".jpeg"
    TTF: str = ".ttf"


@dataclass(frozen=True)
class ConfigKeys:
    """Configuration file name constants."""
    CONFIG_FILE: str = "screenshot-cropper.json"
    TEMPLATE_FILE: str = "template.json"


@dataclass(frozen=True)
class DirectoryNames:
    """Directory name constants."""
    INPUT: str = "input"
    OUTPUT: str = "output"
    SCREENSHOTS: str = "screenshots"
    LOCALES: str = "locales"
    DEFAULT: str = "default"
    CROPPED: str = "cropped"
    FONTS: str = "fonts"


@dataclass(frozen=True)
class Alignment:
    """Text alignment constants."""
    LEFT: str = "left"
    CENTER: str = "center"
    RIGHT: str = "right"
    TOP: str = "top"
    MIDDLE: str = "middle"
    BOTTOM: str = "bottom"


@dataclass(frozen=True)
class ExportFormats:
    """Export format constants."""
    PNG: str = "png"
    WEBP: str = "webp"


# Singleton instances for easy access
FILE_EXT = FileExtensions()
CONFIG = ConfigKeys()
DIRS = DirectoryNames()
ALIGN = Alignment()
FORMATS = ExportFormats()
