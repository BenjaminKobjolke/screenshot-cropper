"""
Settings models for the Screenshot Cropper application.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.constants import ALIGN, FORMATS

logger = logging.getLogger("screenshot_cropper")


@dataclass
class CropSettings:
    """Settings for image cropping."""
    top: int
    left: int = 0
    right: int = 0
    bottom: int = 0

    def __post_init__(self) -> None:
        """Validate settings after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate crop settings."""
        if self.top < 0:
            logger.warning(f"Invalid top value: {self.top}, setting to 0")
            object.__setattr__(self, "top", 0)
        if self.left < 0:
            logger.warning(f"Invalid left value: {self.left}, setting to 0")
            object.__setattr__(self, "left", 0)
        if self.right < 0:
            logger.warning(f"Invalid right value: {self.right}, setting to 0")
            object.__setattr__(self, "right", 0)
        if self.bottom < 0:
            logger.warning(f"Invalid bottom value: {self.bottom}, setting to 0")
            object.__setattr__(self, "bottom", 0)


@dataclass
class BackgroundSettings:
    """Settings for background image placement."""
    file: str
    position_x: int
    position_y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        """Validate settings after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate background settings."""
        if self.position_x < 0:
            logger.warning(f"Invalid position_x value: {self.position_x}, setting to 0")
            object.__setattr__(self, "position_x", 0)
        if self.position_y < 0:
            logger.warning(f"Invalid position_y value: {self.position_y}, setting to 0")
            object.__setattr__(self, "position_y", 0)
        if self.width <= 0:
            logger.warning(f"Invalid width value: {self.width}, setting to 100")
            object.__setattr__(self, "width", 100)
        if self.height <= 0:
            logger.warning(f"Invalid height value: {self.height}, setting to 100")
            object.__setattr__(self, "height", 100)


@dataclass
class OverlaySettings:
    """Settings for overlay image placement."""
    file: str
    position_x: int = 0
    position_y: int = 0

    def __post_init__(self) -> None:
        """Validate settings after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate overlay settings."""
        if self.position_x < 0:
            logger.warning(f"Invalid position_x value: {self.position_x}, setting to 0")
            object.__setattr__(self, "position_x", 0)
        if self.position_y < 0:
            logger.warning(f"Invalid position_y value: {self.position_y}, setting to 0")
            object.__setattr__(self, "position_y", 0)


@dataclass
class ExportSettings:
    """Settings for export format and quality."""
    format: str = FORMATS.PNG
    quality: int = 90
    keep_cropped: bool = False
    lossless: bool = False

    def __post_init__(self) -> None:
        """Validate and normalize settings after initialization."""
        # Normalize format to lowercase
        object.__setattr__(self, "format", self.format.lower())
        self._validate()

    def _validate(self) -> None:
        """Validate export settings."""
        valid_formats = [FORMATS.PNG, FORMATS.WEBP]
        if self.format not in valid_formats:
            logger.warning(f"Invalid format value: {self.format}, setting to '{FORMATS.PNG}'")
            object.__setattr__(self, "format", FORMATS.PNG)
        if self.quality < 1 or self.quality > 100:
            logger.warning(f"Invalid quality value: {self.quality}, setting to 90")
            object.__setattr__(self, "quality", 90)


@dataclass
class TextSettings:
    """Settings for text overlay."""
    font_files: dict[str, str]
    font_size: int
    align: str
    x: int
    y: int
    width: int
    height: int
    vertical_align: str = ALIGN.TOP
    color: tuple[int, int, int] = (0, 0, 0)
    font_names: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate settings after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate text settings."""
        if not isinstance(self.font_files, dict) or "default" not in self.font_files:
            logger.warning("Invalid font_files value, must be a dictionary with a 'default' key")
            object.__setattr__(self, "font_files", {"default": "Arial.ttf"})
        if self.font_size <= 0:
            logger.warning(f"Invalid font_size value: {self.font_size}, setting to 24")
            object.__setattr__(self, "font_size", 24)

        valid_h_aligns = [ALIGN.LEFT, ALIGN.CENTER, ALIGN.RIGHT]
        if self.align not in valid_h_aligns:
            logger.warning(f"Invalid align value: {self.align}, setting to '{ALIGN.LEFT}'")
            object.__setattr__(self, "align", ALIGN.LEFT)

        valid_v_aligns = [ALIGN.TOP, ALIGN.MIDDLE, ALIGN.BOTTOM]
        if self.vertical_align not in valid_v_aligns:
            logger.warning(f"Invalid vertical_align value: {self.vertical_align}, setting to '{ALIGN.TOP}'")
            object.__setattr__(self, "vertical_align", ALIGN.TOP)

        if self.x < 0:
            logger.warning(f"Invalid x value: {self.x}, setting to 0")
            object.__setattr__(self, "x", 0)
        if self.y < 0:
            logger.warning(f"Invalid y value: {self.y}, setting to 0")
            object.__setattr__(self, "y", 0)
        if self.width <= 0:
            logger.warning(f"Invalid width value: {self.width}, setting to 100")
            object.__setattr__(self, "width", 100)
        if self.height <= 0:
            logger.warning(f"Invalid height value: {self.height}, setting to 100")
            object.__setattr__(self, "height", 100)
