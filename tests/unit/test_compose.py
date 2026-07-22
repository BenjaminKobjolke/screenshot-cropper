"""
Unit tests for ImageCompositor.compose (in-memory composition).
"""
from __future__ import annotations

import os

import pytest
from PIL import Image, ImageChops

from src.image_compositor import ImageCompositor
from src.models.settings import (
    BackgroundSettings,
    CropSettings,
    ExportSettings,
    OverlaySettings,
    ScreenshotMaskSettings,
)


@pytest.fixture
def project(tmp_path):
    """Minimal project: input/bg.png, input/overlay.png, one screenshot."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    Image.new("RGB", (100, 80), (10, 20, 30)).save(input_dir / "bg.png")
    overlay = Image.new("RGBA", (100, 80), (0, 0, 0, 0))
    for x in range(100):
        overlay.putpixel((x, 0), (255, 0, 0, 255))
    overlay.save(input_dir / "overlay.png")
    screenshot = tmp_path / "shot.png"
    Image.new("RGB", (40, 40), (200, 100, 50)).save(screenshot)
    return tmp_path


def _make_compositor(project, with_bg: bool = True, with_overlay: bool = True,
                     final_crop: CropSettings | None = None,
                     mask_file: str | None = None) -> ImageCompositor:
    return ImageCompositor(
        CropSettings(top=2, left=2, right=2, bottom=2),
        background_settings=BackgroundSettings(
            file="bg.png", position_x=5, position_y=5, width=30, height=30
        ) if with_bg else None,
        base_dir=str(project),
        overlay_settings=OverlaySettings(file="overlay.png") if with_overlay else None,
        export_settings=ExportSettings(format="png"),
        final_crop_settings=final_crop,
        mask_settings=ScreenshotMaskSettings(file=mask_file) if mask_file else None,
    )


def test_compose_parity_with_process_image(project):
    """compose().final saved manually must be pixel-identical to process_image output."""
    compositor = _make_compositor(project)
    shot = str(project / "shot.png")
    out = str(project / "out.png")

    assert compositor.process_image(shot, out) is True

    with Image.open(shot) as img:
        result = compositor.compose(img, image_path=shot)
    manual = str(project / "manual.png")
    result.final.save(manual, "PNG")

    with Image.open(out) as a, Image.open(manual) as b:
        assert a.size == b.size
        assert ImageChops.difference(a.convert("RGBA"), b.convert("RGBA")).getbbox() is None


def test_compose_crop_only(project):
    """Without background settings, final is just the cropped image."""
    compositor = _make_compositor(project, with_bg=False, with_overlay=False)
    with Image.open(project / "shot.png") as img:
        result = compositor.compose(img)
    assert result.final.size == (36, 36)
    assert result.cropped.size == (36, 36)


def test_compose_invalid_crop_falls_back(project):
    """Invalid crop box (left >= right) keeps the full image."""
    compositor = ImageCompositor(CropSettings(top=0, left=50, right=50, bottom=0))
    with Image.open(project / "shot.png") as img:
        result = compositor.compose(img)
    assert result.final.size == (40, 40)


def test_compose_missing_background_falls_back_to_cropped(project):
    """Missing background file: final equals the cropped image (pipeline saves it, returns True)."""
    compositor = ImageCompositor(
        CropSettings(top=2, left=2, right=2, bottom=2),
        background_settings=BackgroundSettings(
            file="does-not-exist.png", position_x=0, position_y=0, width=30, height=30
        ),
        base_dir=str(project),
    )
    with Image.open(project / "shot.png") as img:
        result = compositor.compose(img)
    assert result.final.size == (36, 36)

    out = str(project / "out_missing_bg.png")
    assert compositor.process_image(str(project / "shot.png"), out) is True
    assert os.path.isfile(out)


def _add_mask(project, size: tuple[int, int], box: tuple[int, int, int, int],
              name: str = "mask.png") -> str:
    """Create a mask: transparent canvas with an opaque black rectangle at box."""
    mask = Image.new("RGBA", size, (0, 0, 0, 0))
    for x in range(box[0], box[2]):
        for y in range(box[1], box[3]):
            mask.putpixel((x, y), (0, 0, 0, 255))
    mask.save(project / "input" / name)
    return name


def test_screenshot_mask_punches_hole_in_canvas_space(project):
    """Mask aligns with the canvas: opaque canvas region removes the screenshot there."""
    # Canvas is 100x80; screenshot pasted at (5,5) size 30x30.
    # Opaque mask over canvas rect (5,5)-(20,20) → that part of the screenshot goes,
    # the background (itself untouched by the mask) shows through.
    name = _add_mask(project, (100, 80), (0, 0, 20, 20))
    compositor = _make_compositor(project, with_overlay=False, mask_file=name)
    with Image.open(project / "shot.png") as img:
        result = compositor.compose(img, image_path=str(project / "shot.png"))
    final = result.final.convert("RGBA")
    assert final.getpixel((10, 10)) == (10, 20, 30, 255)   # masked → background color
    assert final.getpixel((25, 25)) == (200, 100, 50, 255)  # unmasked → screenshot
    assert final.getpixel((60, 60)) == (10, 20, 30, 255)   # outside screenshot → bg


def test_screenshot_mask_resized_to_canvas_size(project):
    """Mask with different dimensions is scaled to the canvas."""
    # 50x40 mask (half canvas), opaque top-left 10x10 → scales to canvas 20x20
    name = _add_mask(project, (50, 40), (0, 0, 10, 10), name="small_mask.png")
    compositor = _make_compositor(project, with_overlay=False, mask_file=name)
    with Image.open(project / "shot.png") as img:
        result = compositor.compose(img, image_path=str(project / "shot.png"))
    final = result.final.convert("RGBA")
    assert final.getpixel((10, 10)) == (10, 20, 30, 255)
    assert final.getpixel((25, 25)) == (200, 100, 50, 255)


def test_screenshot_mask_without_background_uses_cropped_space(project):
    """No background: canvas is the cropped screenshot itself."""
    name = _add_mask(project, (36, 36), (0, 0, 18, 18), name="crop_mask.png")
    compositor = _make_compositor(project, with_bg=False, with_overlay=False,
                                  mask_file=name)
    with Image.open(project / "shot.png") as img:
        result = compositor.compose(img, image_path=str(project / "shot.png"))
    final = result.final.convert("RGBA")
    assert final.getpixel((5, 5))[3] == 0      # masked quadrant transparent
    assert final.getpixel((25, 25))[3] == 255  # rest opaque


def test_screenshot_mask_missing_file_is_noop(project):
    compositor = _make_compositor(project, mask_file="does-not-exist.png")
    reference = _make_compositor(project)
    with Image.open(project / "shot.png") as img:
        masked = compositor.compose(img, image_path=str(project / "shot.png"))
        plain = reference.compose(img, image_path=str(project / "shot.png"))
    assert ImageChops.difference(
        masked.final.convert("RGBA"), plain.final.convert("RGBA")
    ).getbbox() is None


def test_final_crop_applied_after_overlay(project):
    """final_crop shrinks the composite; overlay row 0 (red) is cropped away by top inset."""
    compositor = _make_compositor(
        project, final_crop=CropSettings(top=10, left=5, right=0, bottom=0)
    )
    with Image.open(project / "shot.png") as img:
        result = compositor.compose(img, image_path=str(project / "shot.png"))
    assert result.final.size == (95, 70)
    # Row 0 of the final image is no longer the overlay's red line
    assert result.final.convert("RGBA").getpixel((50, 0)) != (255, 0, 0, 255)


def test_final_crop_on_crop_only_path(project):
    """Without background, final_crop applies to the cropped screenshot."""
    compositor = _make_compositor(
        project, with_bg=False, with_overlay=False,
        final_crop=CropSettings(top=6, left=0, right=0, bottom=0),
    )
    with Image.open(project / "shot.png") as img:
        result = compositor.compose(img)
    assert result.final.size == (36, 30)
    assert result.cropped.size == (36, 36)


def test_final_crop_all_zero_is_noop(project):
    compositor = _make_compositor(project, final_crop=CropSettings(top=0))
    with Image.open(project / "shot.png") as img:
        result = compositor.compose(img, image_path=str(project / "shot.png"))
    assert result.final.size == (100, 80)


def test_compose_background_and_overlay_geometry(project):
    """Screenshot resized to background.width, pasted at position; canvas = bg size; overlay on top."""
    compositor = _make_compositor(project)
    with Image.open(project / "shot.png") as img:
        result = compositor.compose(img, image_path=str(project / "shot.png"))
    assert result.final.size == (100, 80)
    # Overlay row 0 red must survive on top
    assert result.final.convert("RGBA").getpixel((50, 0)) == (255, 0, 0, 255)
    # Screenshot pixel inside pasted area (position 5,5 + resized 30x30)
    assert result.final.convert("RGBA").getpixel((10, 10)) == (200, 100, 50, 255)
