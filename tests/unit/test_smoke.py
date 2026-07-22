"""Smoke tests: core modules import and expose expected symbols."""
from __future__ import annotations


def test_core_imports() -> None:
    from src.cli.arguments import parse_arguments, resolve_paths, validate_arguments
    from src.config import ConfigHandler
    from src.image_processor import ImageProcessor
    from src.logger import setup_logger

    assert callable(parse_arguments)
    assert callable(validate_arguments)
    assert callable(resolve_paths)
    assert callable(setup_logger)
    assert ConfigHandler is not None
    assert ImageProcessor is not None


def test_models_import() -> None:
    from src.models.settings import (
        BackgroundSettings,
        CropSettings,
        ExportSettings,
        OverlaySettings,
        TextSettings,
    )

    for cls in (CropSettings, BackgroundSettings, OverlaySettings, ExportSettings, TextSettings):
        assert cls is not None
